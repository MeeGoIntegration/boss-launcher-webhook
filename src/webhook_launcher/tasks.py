from __future__ import absolute_import

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'

from webhook_launcher.celery import app
from webhook_launcher.app.payload import get_payload

@app.task
def handle_webhook(workitem):
    """Handle POST request to a webhook."""

    payload = get_payload(workitem["payload"]["payload"])
    payload.handle()

    return workitem

@app.task
def relay_webhook(workitem):
    """Relay webhook POST request to task queue."""

    payload = get_payload(workitem["payload"]["payload"])
    payload.relay()

    return workitem
