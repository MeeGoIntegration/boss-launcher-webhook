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

"""Used to create a new OBS (sub)project if needed for trigger_service :

:term:`Workitem` fields IN:

:Parameters:
   :ev.namespace (string):
      Used to contact the right OBS instance.
   :project (string):
      Optional OBS project to create

:term:`Workitem` params IN

:Parameters:
   :project (string):
      Optional OBS project in which the package lives,
      overrides the project field

:term:`Workitem` fields OUT:

:Returns:
   :result (Boolean):
      True if the everything went OK, False otherwise

"""

import os
from lxml import etree

from boss.obs import BuildServiceParticipant
from boss.bz.config import parse_bz_config
from boss.bz.rest import BugzillaError

os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'
import django
django.setup()

from webhook_launcher.app.models import Project


class ParticipantHandler(BuildServiceParticipant):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            self.setup_config(ctrl.config)

    def setup_config(self, config):
        """
        :param config: ConfigParser instance with the bugzilla configuration
        """
        self.bzs = parse_bz_config(config)
        # If there are any auth errors in the config, find out now.
        for bzconfig in self.bzs.values():
            bzconfig['interface'].login()

    def get_repolinks(self, wid, prjmeta):
        """Get a description of the repositories to link to.
           Returns a dictionary where the repository names are keys
           and the values are lists of architectures."""
        exclude_repos = wid.fields.exclude_repos or []
        exclude_archs = wid.fields.exclude_archs or []

        repolinks = {}

        for repoelem in prjmeta.findall('repository'):
            repo = repoelem.get('name')
            if repo in exclude_repos:
                continue
            repolinks[repo] = []
            for archelem in repoelem.findall('arch'):
                arch = archelem.text
                if arch in exclude_archs:
                    continue
                repolinks[repo].append(arch)
            if not repolinks[repo]:
                del repolinks[repo]
        return repolinks

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ Workitem handling function """
        wid.result = True
        f = wid.fields
        p = wid.params

        project = p.project or f.project
        package = p.package or f.package
        # Prime the maintainer list with the current obs user
        maintainers = [self.obs.getUserName()]
        linked_projects = []
        flags = []
        repolinks = {}
        build = True
        create = False
        mechanism = "localdep"
        block = "all"
        rebuild = "transitive"
        linked_project = None
        summary = ""
        desc = ""
        if not project:
            # TODO: deduce project name from "official" mappings of the same
            # repo for now just short circuit here
            wid.result = True
            self.log.warning("No project given. Continuing")
            return

        # events for official projects that are gated get diverted to a side
        # project
        prjobj = Project.get_matching(project, self.obs.apiurl)
        if prjobj and prjobj.gated:
            self.log.info("%s is gated", prjobj)
            linked_project = project
            f.gated_project = project
            project = "gate:%s:%s" % (project, package)
            f.project = project
            summary = "Gate entry for %s" % package
            desc = summary
            mechanism = "off"
            block = "local"
            rebuild = "local"
            create = True

        project_list = self.obs.getProjectList()

        prj_parts = project.split(":")
        if prj_parts[0] == "home" and len(prj_parts) > 1:
            maintainers.append(project.split(":")[1])
            if project not in project_list:
                create = True
            # TODO: construct repos and build paths for a devel build

        if len(prj_parts) >= 3 and prj_parts[-3] == "feature":
            linked_project = ":".join(prj_parts[0:-3])
            fea = "%s#%s" % (prj_parts[-2], prj_parts[-1])
            # Go through each bugzilla we support
            for (bugzillaname, bugzilla) in self.bzs.iteritems():
                for match in bugzilla['compiled_re'].finditer(fea):
                    bugnum = match.group('key')
                    try:
                        summary = bugzilla['interface'].bug_get(
                            bugnum)['summary']
                        desc = bugzilla['interface'].comment_get(
                            bugnum, 0)['text']
                    except BugzillaError, error:
                        if error.code == 101:
                            self.log.warning("Bug %s not found" % bugnum)
                        else:
                            raise
            if project not in project_list:
                create = True

        if linked_project and linked_project in project_list:
            linked_projects.append(linked_project)
            prjmeta = etree.fromstring(
                self.obs.getProjectMeta(linked_project)
            )
            repolinks.update(self.get_repolinks(wid, prjmeta))
            # Get the build flags from the original project meta to disable
            # unnecessary cross architecture builds and such
            build_element = prjmeta.find('build')
            if build_element is not None:
                flags.append(build_element)

        if create:
            if not repolinks:
                # Creating a project with no repos makes no sense
                # as we are only doing this to perform a test build
                #
                # It is debatable that we could want to create
                # projects that have no repos to build against but
                # there have been real-world issues where such
                # projects are not properly detected and reported by
                # the workflow.
                #
                # If this participant is developed to be a general
                # purpose create_project then existing usage should be
                # audited.
                raise RuntimeError(
                    "No suitable repos found in %s "
                    "(must contain an arch in the name)"
                    % project)

            result = self.obs.createProject(
                project, repolinks,
                desc=desc,
                title=summary,
                mechanism=mechanism,
                links=linked_projects,
                maintainers=maintainers,
                build=build,
                block=block,
                rebuild=rebuild,
                flags=flags,
            )

            if not result:
                raise RuntimeError(
                    "Something went wrong while creating project %s" % project)
            self.log.info("Created project %s", project)
        else:
            self.log.info("Didn't need to create project %s", project)

        wid.result = True
