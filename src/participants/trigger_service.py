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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

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

"""

from boss.obs import BuildServiceParticipant
import osc
from urlparse import urlparse

tar_git_service = """
<services>
  <service name="tar_git">
    <param name="url">%(url)s</param>
    <param name="branch">%(branch)s</param>
    <param name="revision">%(revision)s</param>
    <param name="token">%(token)s</param>
    <param name="debian">%(debian)s</param>
    <param name="dumb">%(dumb)s</param>
  </service>
</services>
"""

git_pkg_service = """
<services>
  <service name="gitpkg">
  <param name="repo">%(repo)s</param>
  <param name="tag">%(revision)s</param>
  <param name="service">%(service)s</param>
  </service>
</services>
"""

def find_service_repo(url):
    """
    Given url = 'https://github.com/mer-tools/git-pkg'
    provides 'github', 'mer-tools/git-pkg'
    """
    if url.endswith(".git"):
        url = url[:-4]
    u = urlparse(url)
    print u
    if u.netloc.endswith("github.com"):  # github
        return "github", "/".join(u.path.split("/")[1:3])
    elif u.netloc.endswith("gitorious.org"):  # gitorious
        return "gitorious", "/".join(u.path.split("/")[1:3])
    elif u.netloc.endswith("merproject.org"):  # Mer
        return "Mer", "/".join(u.path.split("/")[1:3])
    
    return None, None

class ParticipantHandler(BuildServiceParticipant):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
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
           raise RuntimeError("Missing mandatory field or parameter: package, project")

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
            if not "service" in params or not "repo" in params:
                raise RuntimeError("Service/Repo not found in repourl %s " % p.repourl)
            service = git_pkg_service
        else:
            service = tar_git_service
        
        if self.obs.isNewPackage(project, package):
            x = self.obs.getCreatePackage(str(project), str(package))
            print x.read()
        
        self.obs.setupService(project, package, service % params)

        wid.result = True
