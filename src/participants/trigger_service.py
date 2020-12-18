# Copyright (C) 2013 Jolla Ltd.
# Contact: Islam Amer <islam.amer@jollamobile.com>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""Used to trigger service of an OBS project / package :

:term:`Workitem` fields IN:

:Parameters:
   :ev.namespace (string):
      Used to contact the right OBS instance.
   :package (string):
      Package name to be rebuilt
   :project (string):
      OBS project in which the package lives


:term:`Workitem` params IN

:Parameters:
   :package (string):
      Package name to be rebuilt, overrides the package field
   :project (string):
      OBS project in which the package lives, overrides the project field

:term:`Workitem` fields OUT:

:Returns:
   :result (Boolean):
      True if the everything went OK, False otherwise


:Configuration:
Constraints can be defined in the configuration like

[const:<package regex>]
disk=<value in GB>
memory=<value in GB>

The package regex is wrapped explicitly in ^...$ to avoid partial matches.
"""

from boss.obs import BuildServiceParticipant
from urlparse import urlparse
from osc import core
from StringIO import StringIO
from lxml import etree
import urllib2
import re
from ConfigParser import NoOptionError

empty_service = "<services></services>"

tar_git_service = """
<service name="tar_git">
  <param name="url">%(url)s</param>
  <param name="branch">%(branch)s</param>
  <param name="revision">%(revision)s</param>
  <param name="token">%(token)s</param>
  <param name="debian">%(debian)s</param>
  <param name="dumb">%(dumb)s</param>
</service>
"""

git_pkg_service = """
<service name="gitpkg">
  <param name="repo">%(repo)s</param>
  <param name="tag">%(revision)s</param>
  <param name="service">%(service)s</param>
</service>
"""


def find_service_repo(url):
    """
    Given url = 'https://github.com/mer-tools/git-pkg'
    provides 'github', 'mer-tools/git-pkg'
    """
    if url.endswith(".git"):
        url = url[:-4]
    u = urlparse(url)
    if u.netloc.endswith("github.com"):  # github
        return "github", "/".join(u.path.split("/")[1:3])
    elif u.netloc.endswith("gitorious.org"):  # gitorious
        return "gitorious", "/".join(u.path.split("/")[1:3])
    elif u.netloc.endswith("merproject.org"):  # Mer
        return "Mer", "/".join(u.path.split("/")[1:3])
    elif u.netloc.endswith("omprussia.ru"):  # omprussia
        return "omprussia", "/".join(u.path.split("/")[1:3])

    return None, None


class ParticipantHandler(BuildServiceParticipant):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == 'start':
            # Collect the constraint patterns and values from the config
            self._constraints = []
            for section in ctrl.config.sections():
                if not section.startswith('const:'):
                    continue
                _, pattern = section.split(':', 1)
                values = {}
                for key in ['disk', 'memory']:
                    try:
                        value = ctrl.config.get(section, key, None)
                        if value:
                            values[key] = value
                    except NoOptionError:
                        pass
                self.log.debug('Adding constraint: %s -> %s', pattern, values)

                pattern = re.compile('^%s$' % pattern)
                self._constraints.append((pattern, values))

        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ Workitem handling function """
        wid.result = False
        f = wid.fields
        p = wid.params

        project = None
        package = None

        if f.project and f.package:
            project = f.project
            package = f.package

        if p.project and p.package:
            project = p.project
            package = p.package

        if not project or not package:
            raise RuntimeError(
                "Missing mandatory field or parameter: package, project")

        if not f.repourl and not p.repourl:
            raise RuntimeError("Missing mandatory field or parameter: repourl")

        params = {}

        if f.repourl:
            params["url"] = f.repourl

        if p.repourl:
            params["url"] = p.repourl

        params["service"], params["repo"] = find_service_repo(params["url"])

        if f.branch:
            params["branch"] = f.branch
        if p.branch:
            params["branch"] = p.branch
        params["revision"] = ""
        if f.revision:
            params["revision"] = f.revision
        if p.revision:
            params["revision"] = p.revision
        params["token"] = ""
        params["debian"] = ""
        params["dumb"] = ""
        if f.token:
            params["token"] = f.token
        if p.token:
            params["token"] = p.token
        if p.debian:
            params["debian"] = p.debian
        if f.debian:
            params["debian"] = f.debian

        if p.dumb:
            params["dumb"] = p.dumb
        if f.dumb:
            params["dumb"] = f.dumb

        if "branch" in params and params["branch"].startswith("pkg-"):
            if "service" not in params or "repo" not in params:
                raise RuntimeError(
                    "Service/Repo not found in repourl %s " % p.repourl)
            service = git_pkg_service
        else:
            service = tar_git_service

        # the simple approach doesn't work with project links
        # if self.obs.isNewPackage(project, package):
            # self.obs.getCreatePackage(str(project), str(package))
        # else:
        try:
            pkginfo = core.show_files_meta(
                self.obs.apiurl, str(project), str(package),
                expand=False, meta=True)
            if "<entry" not in pkginfo:
                # This is a link and it needs branching from the linked project
                # so grab the meta and extract the project from the link
                self.log.debug("Found %s as a link in %s" % (package, project))
                x = etree.fromstring(
                    "".join(core.show_project_meta(self.obs.apiurl, project)))
                link = x.find('link')
                if link is None:
                    raise Exception(
                        "Expected a <link> in project %s." % project)
                self.log.debug("Got a link  %s" % link)
                linked_project = link.get('project')
                self.log.debug("Branching %s to overwrite _service" % package)
                core.branch_pkg(self.obs.apiurl, linked_project,
                                str(package), target_project=str(project))
        except Exception as exc:
            self.log.warn(
                "Doing a metatype pkg add because I caught %s" % exc)
            self.log.warn(
                "Creating package %s in project %s" % (package, project))
            data = core.metatypes['pkg']['template']
            data = StringIO(
                data % {
                    "name": str(package),
                    "user": self.obs.getUserName()}
            ).readlines()
            u = core.makeurl(
                self.obs.apiurl,
                ['source', str(project), str(package), "_meta"])
            x = core.http_PUT(u, data="".join(data))
            self.log.debug("HTTP PUT result of pkg add : %s" % x)

        # Set any constraint before we set the service file
        constraint_xml = self.make_constraint(package)
        if constraint_xml:
            # obs module only exposed the putFile by filepath so
            # this is a reimplement to avoid writing a tmpfile
            u = core.makeurl(self.obs.apiurl,
                             ['source', project, package, "_constraints"])
            core.http_PUT(u, data=constraint_xml)
            self.log.info("New _constraints file:\n%s" % constraint_xml)
        else:
            self.log.info("No _constraints for %s" % package)

        # Start with an empty XML doc
        try:  # to get any existing _service file.
            # We use expand=0 as otherwise a failed service run won't
            # return the _service file
            self.log.debug(
                "Trying to get _service file for %s/%s" % (project, package))
            services_xml = self.obs.getFile(
                project, package, "_service", expand=0)
        except urllib2.HTTPError as e:
            self.log.debug(
                "Exception %s trying to get _service file for %s/%s" %
                (e, project, package))
            if e.code == 404:
                services_xml = empty_service
            elif e.code == 400:
                # HTTP Error 400: service in progress error
                wid.result = True
                self.log.warn(
                    "Service in progress, could not get _service file. "
                    "Not triggering another run.")
                return
            else:
                raise e

        services_xml = services_xml.strip() or empty_service

        # Replace the matching one:
        try:
            services = etree.fromstring(services_xml)
        except etree.XMLSyntaxError as e:
            self.log.exception("Creating services xml failed")
            raise

        # Create our new service (not services anymore)
        new_service_xml = service % params
        new_service = etree.fromstring(new_service_xml)
        svcname = new_service.find(".").get("name")
        old_service = services.find("./service[@name='%s']" % svcname)
        if old_service is not None:
            services.replace(old_service, new_service)
        else:
            services.append(new_service)

        svc_file = etree.tostring(services, pretty_print=True)
        self.log.debug("New _service file:\n%s" % svc_file)

        # And send our new service file
        self.obs.setupService(project, package, svc_file)

        wid.result = True

    def make_constraint(self, package):
        for pattern, values in self._constraints:
            if pattern.search(package):
                self.log.info(
                    "Package %s matched constraint %s: %s",
                    package, pattern, values
                )
                break
        else:
            # No match found
            return None

        # Construct xml with the format
        #
        # <constraints>
        #   <hardware>
        #     <KEY>
        #       <size unit="G">VALUE</size>
        #     </KEY>
        #     ...
        #
        # Where KEY and VALUE come from the disk and memory options set for
        # the matched pattern in the config

        constraints = etree.Element("constraints")
        hardware = etree.SubElement(constraints, "hardware")
        for elem, value in values.items():
            node = etree.SubElement(hardware, elem)
            etree.SubElement(node, "size", unit="G").text = unicode(value)

        return etree.tostring(constraints, pretty_print=True)
