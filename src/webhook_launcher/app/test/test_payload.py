# Copyright (C) 2017 Jolla Ltd.
#
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
# along with this program; if not, write to
# the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from webhook_launcher.app.models import (
    BuildService, LastSeenRevision, WebHookMapping
)
from webhook_launcher.app.payload import (
    BbPushV2, GhPush, get_payload
)

from .data import get_obj


class TestPayloadDetection(TestCase):
    def test_bb_v2_push(self):
        p = get_payload(get_obj('payload_bb_v2_push'))
        self.assertIsInstance(p, BbPushV2)

    def test_gh_push(self):
        p = get_payload(get_obj('payload_gh_push'))
        self.assertIsInstance(p, GhPush)


@patch('webhook_launcher.app.payload.requests')
@patch('webhook_launcher.app.payload.bbAPIcall')
@patch('webhook_launcher.app.models.launch_notify')
@patch('webhook_launcher.app.models.launch_build')
class TestPayloadHandling(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='placeholder')
        self.build_Service = BuildService.objects.create(
            namespace='test',
            apiurl='api.example.com',
            weburl='build.example.com',
        )

    def test_bb_v2_push(self, *mocks):
        payload = self._handle_first_push(
            get_obj('payload_bb_v2_push'), *mocks
        )
        launch_build, launch_notify, bbAPIcall = mocks[:3]
        payload = get_payload(get_obj('payload_bb_v2_push_2commits'))
        payload.handle()
        launch_notify.assert_called_once()
        launch_build.assert_not_called()
        # Prepare api response and push tag
        api_mock = bbAPIcall.return_value
        api_mock.branches.return_value = [
            # Actual response has more stuf but only these are currently used
            {
                "name": "master",
                "target": {
                    "hash": "fd0af720f9465c98ed795b544b82334b0b5cc9b4"
                },
            },
        ]
        payload = get_payload(get_obj('payload_bb_v2_push_tag'))
        payload.handle()
        api_mock.branches.assert_called_once()
        launch_build.assert_called_once()

    def test_gh_push(self, *mocks):
        payload = self._handle_first_push(
            get_obj('payload_gh_push'), *mocks
        )
        launch_build, launch_notify = mocks[:2]
        # Fake another commit
        payload.data['head_commit']['id'] = 'otherrevision'
        payload.handle()
        launch_notify.assert_called_once()
        launch_build.assert_not_called()
        # TODO: Test GH tag push and build trigger
        #   Need to gerate proper test payloads for tags

    def _handle_first_push(
        self, data, launch_build, launch_notify, bbAPIcall, requests
    ):
        # First push creates the placeholder mapping
        payload = get_payload(data)
        payload.handle()
        self.assertEqual(
            WebHookMapping.objects.count(), 1
        )
        self.assertEqual(
            LastSeenRevision.objects.count(), 1
        )
        whm = WebHookMapping.objects.first()
        launch_notify.assert_not_called()
        launch_build.assert_not_called()

        # Enable mapping
        whm.build = True
        whm.notify = True
        whm.project = 'test'
        whm.package = 'test'
        whm.save()
        return payload
