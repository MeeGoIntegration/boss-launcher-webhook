from mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from webhook_launcher.app.models import (
    BuildService, LastSeenRevision, WebHookMapping
)
from webhook_launcher.app.payload import (
    BbPull, BbPush, GhPull, GhPush, get_payload
)

from .data import get_obj


class TestPayloadDetection(TestCase):
    def test_bb_v1_push(self):
        p = get_payload(get_obj('payload_bb_v1_push'))
        self.assertIsInstance(p, BbPush)

    def test_bb_v1_pull(self):
        p = get_payload(get_obj('payload_bb_v1_pull'))
        self.assertIsInstance(p, BbPull)

    def test_gh_push(self):
        p = get_payload(get_obj('payload_gh_push'))
        self.assertIsInstance(p, GhPush)

    def test_gh_pull(self):
        p = get_payload(get_obj('payload_gh_pull'))
        self.assertIsInstance(p, GhPull)


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
