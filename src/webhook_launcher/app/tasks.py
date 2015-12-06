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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import json
import urlparse

from django.conf import settings

from webhook_launcher.app.payload import get_payload
from webhook_launcher.app.boss import launch_notify, launch_build

def relay_payload(data):

    payload = get_payload(data)
    payload.relay()

def handle_payload(data):

    payload = get_payload(data)

    #TODO: move to DB based service whitelist
    if ((not settings.SERVICE_WHITELIST) or
        (settings.SERVICE_WHITELIST and
         urlparse.urlparse(payload.url).netloc in settings.SERVICE_WHITELIST)):
        payload.handle()

def handle_commit(mapobj, lsr, user, notify=False):

    lsr.tag = ""
    lsr.handled = False
    lsr.save()

    if not notify:
        return

    message = "%s commit(s) pushed by %s to %s branch of %s" % (len(lsr.payload["commits"]), user, mapobj.branch, mapobj.repourl)
    if not mapobj.mapped:
        message = "%s, which is not mapped yet. Please map it." % message

    fields = mapobj.to_fields()
    fields['msg'] = message
    fields['payload'] = lsr.payload
    print message
    launch_notify(fields)

def handle_pr(mapobj, data, payload):

    message = "Pull request #%s by %s from %s / %s to %s %s (%s)" % (
        data['id'], data['username'], data['source_repourl'],
        data['source_branch'], mapobj, data['action'], data['url'])

    if mapobj.notify:

        fields = mapobj.to_fields()
        fields['msg'] = message
        fields['payload'] = payload
        print message
        launch_notify(fields)

def handle_build(mapobj, user=None, lsr=None, force=None, skipped=False, delayed=False, qp=None):

    build = mapobj.build and mapobj.mapped

    if lsr is None:
        lsr = mapobj.lsr
  
    if user is None:
        user = mapobj.user.username
  
    if lsr.tag:
        message = "Tag %s" % lsr.tag
        if force:
            message = "Forced build trigger for %s" % lsr.tag
    else:
        message = "%s" % mapobj.rev_or_head
        if force:
            message = "Forced build trigger for %s" % mapobj.rev_or_head
  
    message = "%s by %s in %s branch of %s" % (message, user, mapobj.branch,
                                               mapobj.repourl)
    if not mapobj.mapped:
        message = "%s, which is not mapped yet. Please map it." % message
    elif build:
        message = ("%s, which will trigger build in project %s package "
                   "%s (%s/package/show?package=%s&project=%s)" % (message,
                    mapobj.project, mapobj.package, mapobj.obs.weburl,
                    mapobj.package, mapobj.project))
  
    elif skipped:
        message = "%s, which was already handled; skipping" % message
    elif qp and delayed:
        message = "%s, which will be delayed by %s" % (message, qp)
        if qp.comment:
            message = "%s\n%s" % (message, qp.comment)
  
    if mapobj.notify:
        fields = mapobj.to_fields()
        fields['msg'] = message
        fields['payload'] = json.loads(lsr.payload)
        launch_notify(fields)
  
    if build:
        fields = mapobj.to_fields()
        fields['branch'] = mapobj.branch
        fields['revision'] = lsr.revision
        fields['payload'] = json.loads(lsr.payload)
        launch_build(fields)
        lsr.handled = True

    lsr.save()
 
    return message

