from __future__ import absolute_import

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'

from webhook_launcher.app.utils import handle_payload
from webhook_launcher.app.utils import relay_payload
from webhook_launcher.celery import app

@app.task
def handle_webhook(workitem):
    """Handle POST request to a webhook."""

    payload = workitem["payload"]["payload"]
    handle_payload(payload)

    return workitem

@app.task
def relay_webhook(workitem):
    """Relay webhook POST request to task queue."""

    payload = workitem["payload"]["payload"]
    relay_payload(payload)

    return workitem
