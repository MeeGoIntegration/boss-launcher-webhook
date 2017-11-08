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

import json

from django.contrib.auth.models import User
from django.test import TestCase
from webhook_launcher.app.models import (
    BuildService, WebHookMapping
)


TEST_WHM_DATA = {
    "comment": "",
    "project": "mer:core",
    "package": "test",
    "obs": "test",
    "repourl": "https://exmaple.com",
    "token": "nnn",
    "branch": "master",
    "user": "admin",
    "dumb": "N",
    "debian": 'N',
    "notify": True,
    "build": True,
    "lsr": {
        "revision": "xyz",
        "tag": "0.1",
    },
}


class TestWebhookMappingApi(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='admin',
            is_staff=True,
            is_superuser=True,
        )
        self.build_service = BuildService.objects.create(
            namespace='test',
            apiurl='api.example.com',
            weburl='build.example.com',
        )

    def test_create(self):
        self.assertEqual(WebHookMapping.objects.count(), 0)
        self.client.force_login(self.admin)

        response = self.client.post(
            '/webhook/api/webhookmappings/',
            content_type='application/json',
            data=json.dumps(TEST_WHM_DATA),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WebHookMapping.objects.count(), 1)
        whm_id = response.json()['id']
        whm = WebHookMapping.objects.get(id=whm_id)
        self.assertEqual(whm.project, TEST_WHM_DATA['project'])
        self.assertEqual(whm.package, TEST_WHM_DATA['package'])
        self.assertEqual(whm.repourl, TEST_WHM_DATA['repourl'])
        self.assertEqual(whm.token, TEST_WHM_DATA['token'])
        self.assertEqual(whm.branch, TEST_WHM_DATA['branch'])
        self.assertEqual(whm.dumb, TEST_WHM_DATA['dumb'])
        self.assertEqual(whm.debian, TEST_WHM_DATA['debian'])
        self.assertEqual(whm.build, TEST_WHM_DATA['build'])
        self.assertEqual(whm.notify, TEST_WHM_DATA['notify'])

        self.assertEqual(whm.obs, self.build_service)
        self.assertEqual(whm.user, self.admin)

        self.assertEqual(whm.lsr.revision, 'xyz')
        self.assertEqual(whm.lsr.tag, '0.1')

    def test_update(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            '/webhook/api/webhookmappings/',
            content_type='application/json',
            data=json.dumps(TEST_WHM_DATA),
        )
        self.assertEqual(response.status_code, 201)
        whm_data = response.json()

        whm_data['repourl'] = 'https://example.com/repo'
        whm_data['lsr']['revision'] = 'abc'
        whm_data['lsr']['tag'] = '123'
        response = self.client.put(
            '/webhook/api/webhookmappings/%s/' % whm_data['id'],
            content_type='application/json',
            data=json.dumps(whm_data),
        )
        self.assertEqual(response.status_code, 200)
        whm = WebHookMapping.objects.get(id=whm_data['id'])
        self.assertEqual(whm.repourl, 'https://example.com/repo')
        self.assertEqual(whm.lsr.revision, 'abc')
        self.assertEqual(whm.lsr.tag, '123')

        self.assertEqual(whm.project, TEST_WHM_DATA['project'])
        self.assertEqual(whm.package, TEST_WHM_DATA['package'])
        self.assertEqual(whm.token, TEST_WHM_DATA['token'])
        self.assertEqual(whm.branch, TEST_WHM_DATA['branch'])
        self.assertEqual(whm.dumb, TEST_WHM_DATA['dumb'])
        self.assertEqual(whm.debian, TEST_WHM_DATA['debian'])
        self.assertEqual(whm.build, TEST_WHM_DATA['build'])
        self.assertEqual(whm.notify, TEST_WHM_DATA['notify'])

