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

"""Used to handle an queued webhook event

:term:`Workitem` fields IN:

:Parameters:
   :payload (dict):
      Payload of incoming event

:term:`Workitem` fields OUT:

:Returns:
   :result (Boolean):
      True if the everything went OK, False otherwise

"""

class ParticipantHandler(object):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    def handle_wi(self, wid):
        """ Workitem handling function """
        wid.result = False

        if wid.fields.repourl is None:
           raise RuntimeError("Missing mandatory field: repourl")

        GITBASE="/srv/cache/mirror_git"
        upstream_url = wid.fields.repourl
        upstream_parsed_url = urlparse.urlparse(upstream_url)
        mirror_parsed_url = upstream_parsed_url._replace(netloc="git.omprussia.ru")
        mirror_url = mirror_parsed_url.geturl()
        mirror_path= os.path.join(GITBASE, upstream_parsed_url.netloc, upstream_parsed_url.path.strip("/")

        if not os.path.exists(mirror_path):
            os.makedirs(mirror_path)
            os.chdir(mirror_path)
            os.system("git --bare init")
            os.system("git remote add mirror %s" % mirror_url)
            os.system("git remote add upstream %s" % upstream_url)
        else:
            os.chdir(mirror_path)
            os.system("git remote set-url mirror %s" % mirror_url)
            os.system("git remote set-url upstream %s" % upstream_url)

        os.system("git remote update mirror")
        os.system("git remote update upstream")
        os.system("cp refs/remotes/upstream/* refs/heads/")
        os.system("git push mirror 'refs/tags/*' 'refs/heads/*'")

        wid.result = True
