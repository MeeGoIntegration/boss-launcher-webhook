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

import os
import hashlib
import json
os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'
import django
django.setup()

from webhook_launcher.app.payload import get_payload


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

        if wid.fields.payload is None:
            raise RuntimeError("Missing mandatory field: payload")

        md5 = hashlib.md5(json.dumps(wid.fields.payload.as_dict(),
                                     sort_keys=True)).hexdigest()
        if md5 in self.seen:
            print("Ignoring duplicate webhook (possible resend or "
                  "github hook set at both repo and orginisation level)")
            wid.result = True
            return
        self.seen[md5] = True

        print("Handling a webhook payload")
        payload = get_payload(wid.fields.payload.as_dict())
        payload.handle()
        print("Webhook handled")

        wid.result = True
