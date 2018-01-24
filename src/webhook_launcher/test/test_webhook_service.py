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

import os
from subprocess import check_output, CalledProcessError

from django.test import LiveServerTestCase
from django.contrib.auth.models import User

from webhook_launcher.app.models import WebHookMapping, BuildService


class WebhookServiceTestCase(LiveServerTestCase):
    def setUp(self):
        self.service = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '../../service/webhook',
            )
        )
        self.user = User(username='admin')
        self.user.set_password('root')
        self.user.save()
        self.obs = BuildService.objects.create(
            namespace='mer',
        )
        self.env = {
            'DEBUG': '1',
            'OBS': self.obs.namespace,
            'OBS_SERVICE_PROJECT': 'example:test',
            'OBS_SERVICE_PACKAGE': 'test',
            'WEBHOOK_URL': '%s/webhook/api' % self.live_server_url,
            'WH_USER': 'admin',
            'WH_PASSWD': 'root',
        }

    def _call_service(self, *args):
        cmd = [self.service]
        cmd.extend(args)
        try:
            output = check_output(cmd, env=self.env)
        except CalledProcessError as e:
            self.fail("webhook service call failed: %s\n%s" % (
                " ".join(cmd), e.output)
            )
        return output

    def test_create(self):
        self._call_service(
            '--repourl', 'https://example.com/project',
            '--branch', 'master',
        )
        self.assertEqual(
            WebHookMapping.objects.count(),
            1,
        )
        whm = WebHookMapping.objects.last()
        self.assertEqual(
            whm.repourl,
            'https://example.com/project.git',
        )

    def test_update(self):
        whm = WebHookMapping.objects.create(
            user=self.user,
            obs=self.obs,
            project='example:test',
            package='test',
            repourl='https://something.else.com/'
        )
        self._call_service(
            '--repourl', 'https://example.com/project',
            '--branch', 'master',
        )
        whm = WebHookMapping.objects.get(
            project='example:test',
            package='test',
        )
        self.assertEqual(
            whm.repourl,
            'https://example.com/project.git',
        )
