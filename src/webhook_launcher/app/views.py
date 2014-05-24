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

""" webhook view """

import urlparse
from collections import defaultdict
from django.http import ( HttpResponse, HttpResponseBadRequest,
                          HttpResponseForbidden, HttpResponseNotAllowed )
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.conf import settings
from utils import bitbucket_webhook_launch, github_webhook_launch, github_pull_request
from models import WebHookMapping, get_or_none
from pprint import pprint
import struct, socket

def index(request):
    """
    GET: returns 403

    POST: process a webhook callback from bitbucket or github
    """

    if request.method == 'GET':
        print "GET from %s" % request.META.get("REMOTE_HOST", None)
        if not settings.PUBLIC_LANDING_PAGE and not request.user.is_authenticated():
            return HttpResponseForbidden()

        mappings = defaultdict(list)
        #TODO: filter with privileged projects
        maps = WebHookMapping.objects.exclude(package="")
        for mapobj in maps:
            repourl = urlparse.urlparse(mapobj.repourl)
            mappings[repourl.netloc].append({ "path" : repourl.path,
                                         "branch" : mapobj.branch,
                                         "project" : mapobj.project,
                                         "package" : mapobj.package})
        return render_to_response('app/index.html', {'mappings' : dict(mappings)},
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        #TODO: Move to database ip filter list
        # Use the ip_filter to decide whether to accept a post
        if settings.POST_IP_FILTER:
            # If behind a rev-proxy then use XFF header
            if settings.POST_IP_FILTER_HAS_REV_PROXY:
                # Take the last value only to avoid spoofing
                ip = request.META["HTTP_X_FORWARDED_FOR"].split(",")[-1]
                print "Using %s as IP from HTTP_X_FORWARDED_FOR: %s" % ( ip, request.META["HTTP_X_FORWARDED_FOR"] )
            else:
                ip = request.META["REMOTE_IP"]
            ipaddr = struct.unpack('<L', socket.inet_aton(ip))[0]
            ip_ok = False
            for netmask in settings.NETMASKS:
                if ipaddr & netmask == netmask:
                    ip_ok = True
                    break
            if not ip_ok:
                print "POST from %s not in settings.post_ip_filter" % ( ip )
                return HttpResponseBadRequest()

        ctype = request.META.get("CONTENT_TYPE", None)
        if ctype == "application/json":
            payload = request.raw_post_data
        elif ctype == "application/x-www-form-urlencoded":
            payload = request.POST.get("payload", None)
        else:
            print "POST with unknown content type %s from %s" % ( ctype , request.META.get("REMOTE_HOST", None))
            print request
            return HttpResponseBadRequest()

        try:
            data = simplejson.loads(payload)
        except Exception as e:
            print "POST with invalid JSON payload from %s" % request.META.get("REMOTE_HOST", None)
            return HttpResponseBadRequest()

        pprint(data, indent=2, width=80, depth=6)

        url = None
        func = None
        repo = data.get('repository', None)
        gh_pull_request = data.get('pull_request', None)

        #TODO: support more payload types
        if gh_pull_request:
            # Github pull request event
            func = github_pull_request
            url = data['pull_request']['html']

        elif repo:
            if repo.get('absolute_url', None):
                # bitbucket type payload
                url = repo.get('absolute_url', None)
                canon_url = data.get('canon_url', None)
                if canon_url and url:
                    print "bitbucket payload from %s" % request.META.get("REMOTE_HOST", None)
                    if url.endswith('/'):
                        url = url[:-1]
                    url = urlparse.urljoin(canon_url, url)
                    if not url.endswith(".git"):
                        url = url + ".git"
                    func = bitbucket_webhook_launch
            elif repo.get('url', None):
                # github type payload
                url = repo.get('url', None)
                if url:
                    print "github payload from %s" % request.META.get("REMOTE_HOST", None)
                    if not url.endswith(".git"):
                        url = url + ".git"
                    func = github_webhook_launch

        if not url or not func:

            if data.get('zen', None) and data.get('hook_id', None):
                # Github ping event, just say Hi
                return HttpResponse()

            else:
                print "unknown payload from %s" % request.META.get("REMOTE_HOST", None)
                return HttpResponseBadRequest()

        #TODO: move to DB based service whitelist
        if ((not settings.SERVICE_WHITELIST) or
            (settings.SERVICE_WHITELIST and
             urlparse.urlparse(url).netloc in settings.SERVICE_WHITELIST)):
            func(url, data)

        return HttpResponse()

    return HttpResponseNotAllowed(['GET', 'POST'])
