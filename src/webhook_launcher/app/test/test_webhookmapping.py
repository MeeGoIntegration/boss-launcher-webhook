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

from django.contrib.auth.models import User
from django.forms import ModelForm
from django.test import TestCase

from webhook_launcher.app.models import BuildService, WebHookMapping


class WHMTestForm(ModelForm):
    class Meta:
        model = WebHookMapping
        fields = ["repourl", "obs", "project", "package", "build"]


class WebHookMappingTestCase(TestCase):
    def setUp(self):
        self.user = User(username="test")
        self.user.set_password('test')
        self.user.save()
        self.obs = BuildService.objects.create(
            namespace="test",
            apiurl="https://example.com",
            weburl="https://example.com",
        )
        self.obs2 = BuildService.objects.create(
            namespace="test2",
            apiurl="https://example.com/2",
            weburl="https://example.com/2",
        )

    def test_uniqueness_form(self):
        data = {
            "repourl": "https://example.com/two",
            "project": "test",
            "package": "test",
            "build": True,
        }

        WebHookMapping.objects.create(
            user=self.user,
            obs=self.obs,
            **data
        )

        data["obs"] = self.obs.pk
        form = WHMTestForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "already exists",
            "|".join(str(x) for x in list(form.errors.values()))
        )

        test_data = data.copy()
        test_data['obs'] = self.obs2.pk
        form = WHMTestForm(test_data)
        self.assertTrue(form.is_valid())

        test_data = data.copy()
        test_data['project'] = 'test2'
        form = WHMTestForm(test_data)
        self.assertTrue(form.is_valid())

        test_data = data.copy()
        test_data['package'] = 'test2'
        form = WHMTestForm(test_data)
        self.assertTrue(form.is_valid())

        test_data = data.copy()
        test_data['build'] = False
        form = WHMTestForm(test_data)
        self.assertTrue(form.is_valid())
