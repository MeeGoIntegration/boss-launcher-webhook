# Copyright (C) 2017 Jolla Ltd.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

"""Used decide wether a git repository needs to be mirrored locally

:term:`Workitem` fields IN:

:Parameters:
   :payload (dict):
      Payload of incoming event

:term:`Workitem` fields OUT:

:Returns:
   :ignore_hook (Boolean):
      True if VCSCOMMIT_QUEUE should not do any further processing of
      the webhook event

   :result (Boolean):
      True if the everything went OK, False otherwise

"""

import os
import urlparse


os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'
import django
django.setup()


from webhook_launcher.app.payload import get_payload
from webhook_launcher.app.boss import launch_pdef


vcsmirror_pdef = """
Ruote.process_definition 'vcsmirror' do
  sequence do
    set :f => 'log_channel', :value => '#mer-boss'
    set :f => 'debug_dump', :value => 'true'
    mirror_git
    notify_irc :irc_channel => '${f:log_channel}',
               :msg => 'Mirroring ${f:repourl}'
  end
end
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
        wid.fields.ignore_hook = False

        if wid.fields.payload is None:
            raise RuntimeError("Missing mandatory field: payload")

        payload = get_payload(wid.fields.payload.as_dict())
        payload_url = payload.url
        parsed_url = urlparse.urlparse(payload_url)
        # TODO: payload.url is not set to the canonical repository
        self.log.info("Received payload for %s: %s", payload_url, payload)
        if parsed_url.netloc not in ("git.omprussia.ru",):
            launch_pdef(vcsmirror_pdef, {
                "repourl": payload_url
            })
            wid.fields.ignore_hook = True

        wid.result = True
