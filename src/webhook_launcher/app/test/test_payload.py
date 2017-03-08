from mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from webhook_launcher.app.models import (
    BuildService, LastSeenRevision, WebHookMapping
)
from webhook_launcher.app.payload import (
    BbPush, BbPushV2, GhPush, get_payload
)

from .data import get_obj


class TestPayloadDetection(TestCase):
    def test_bb_v1_push(self):
        p = get_payload(get_obj('payload_bb_v1_push'))
        self.assertIsInstance(p, BbPush)

    def test_bb_v2_push(self):
        p = get_payload(get_obj('payload_bb_v2_push'))
        self.assertIsInstance(p, BbPushV2)

    def test_gh_push(self):
        p = get_payload(get_obj('payload_gh_push'))
        self.assertIsInstance(p, GhPush)


@patch('webhook_launcher.app.payload.requests')
@patch('webhook_launcher.app.payload.bbAPIcall')
@patch('webhook_launcher.app.tasks.launch_notify')
@patch('webhook_launcher.app.tasks.launch_build')
class TestPayloadHandling(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='placeholder')
        self.build_Service = BuildService.objects.create(
            namespace='test',
            apiurl='api.example.com',
            weburl='build.example.com',
        )

    def test_bb_v1_push(self, *mocks):
        payload = self._handle_first_push(
            get_obj('payload_bb_v1_push'), *mocks
        )
        launch_build, launch_notify, bbAPIcall = mocks[:3]
        # Fake another commit
        payload.data['commits'][0]['raw_node'] = 'otherrevision'
        payload.handle()
        launch_notify.assert_called_once()
        launch_build.assert_not_called()
        # Prepare api response and fake tag push
        api_mock = bbAPIcall.return_value
        api_mock.branches_tags.return_value = {
            'branches': [
                {'name': 'master', 'changeset': 'otherrevision'}
            ],
            'tags': [
                {'name': '1.0', 'changeset': 'otherrevision'}
            ]
        }
        payload.data['commits'] = []
        payload.handle()
        api_mock.branches_tags.assert_called_once()
        launch_build.assert_called_once()

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
        api_mock.branches_tags.return_value = {
            'branches': [
                {
                    'name': 'master',
                    'changeset': 'fd0af720f9465c98ed795b544b82334b0b5cc9b4'
                }
            ],
            'tags': [
                {
                    'name': '0.0.1',
                    'changeset': 'fd0af720f9465c98ed795b544b82334b0b5cc9b4'
                }
            ]
        }
        payload = get_payload(get_obj('payload_bb_v2_push_tag'))
        payload.handle()
        api_mock.branches_tags.assert_called_once()
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
