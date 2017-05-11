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

"""Used to autopromote a just triggered service:

:term:`Workitem` fields IN:

:Parameters:
   :ev.namespace (string):
      Used to contact the right OBS instance.
   :project (string):
      Project where service was triggered
   :package (string)
      Package name that was triggered
   :target_project (string)
      Project to which promotion should happen

:term:`Workitem` fields OUT:

:Returns:
   :result (Boolean):
      True if the everything went OK, False otherwise

"""

from boss.obs import BuildServiceParticipant
import osc
from urlparse import urlparse
import os
from lxml import etree

from boss.bz.config import parse_bz_config
from boss.bz.rest import BugzillaError

os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'
import django
django.setup()

from webhook_launcher.app.models import WebHookMapping, Project, get_or_none

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

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ Workitem handling function """
        wid.result = False
        f = wid.fields

        project = f.project
        package = f.package
        gated_project = f.gated_project

        if not project or not gated_project:
            print "Nothing to do, no project or gated_project in the fields"
            wid.result = True
            return

        # events for official projects that are gated get diverted to a side project
        prjobj = Project.get_matching(gated_project, self.obs.apiurl)
        if prjobj and prjobj.gated:
            webhook = get_or_none(WebHookMapping, pk=f.pk)
            actions = [{"action" : "submit", "src_project" : project, "src_package" : package,
                        "tgt_project" : gated_project, "tgt_package" : package}]
            description = "%s @ %s" % (webhook.tag or webhook.rev_or_head, str(webhook))
            comment = ""
            print "Requesting actions: %s\ndesc: %s" %(actions, description)
            result = self.obs.createRequest(options_list=actions, description=description, comment=comment, supersede=True, opt_sourceupdate="cleanup")

            if not result:
                raise RuntimeError("Something went wrong while creating project %s" % project)
            print "Created submit request from %s/%s to %s/%s : %s" %(project,package,gated_project,package,description)
        else:
            print "No gated Project matching gated_project: %s" % (gated_project)
        wid.result = True
