# Copyright (C) 2017 Jolla Ltd.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""Check to see the source state for a particular package
   Success if there is src ready to build
   service_state has more details

   Packages which don't use a service are indistinguishable from a
   successful service run.

:term:`Workitem` fields IN:

:Parameters:
   :ev.namespace (string):
      Used to contact the right OBS instance.
   :package (string):
      Package name to be checked
   :project (string):
      OBS project in which the package lives


:term:`Workitem` params IN

:Parameters:
   :package (string):
      Package name to be checked, overrides the package field
   :project (string):
      OBS project in which the package lives, overrides the project field

:term:`Workitem` fields OUT:

:Returns:
   :f.service_state (string):
      succeeded : src is present : service ran successfully or there's
                  no _service
      running   : service is in progress
      failed    : service failed to run
   :result (Boolean):
      True if the status is succeeded
      False if it's runnning or failed

"""

from boss.obs import BuildServiceParticipant


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
            print("setting %s/%s from fields" % (project, package))

        if p.project and p.package:
            project = p.project
            package = p.package
            print("setting %s/%s from params" % (project, package))

        err = []
        if not project:
            err.append("no project")
        if not package:
            err.append("no package")
        if len(err) > 0:
            raise RuntimeError(
                "Missing mandatory field or parameter: %s" % ", ".join(err))

        print("Checking service for %s/%s" % (project, package))
        f.service_state = self.obs.getServiceState(project, package)
        print("State : %s" % f.service_state)
        if f.service_state == "succeeded":
            wid.result = True
