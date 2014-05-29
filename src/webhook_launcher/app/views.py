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
from rest_framework import viewsets
from utils import handle_payload
from models import WebHookMapping
from serializers import WebHookMappingSerializer
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

    elif request.method == 'POST':
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
            payload = request.body
        elif ctype == "application/x-www-form-urlencoded":
            payload = request.POST.get("payload", None)
        else:
            print "POST with unknown content type %s from %s" % ( ctype , request.META.get("REMOTE_HOST", None))
            print request
            return HttpResponseBadRequest()

        try:
            data = simplejson.loads(payload)
            pprint(data, indent=2, width=80, depth=6)
            handle_payload(data)

        except Exception as e:
            print e
            print "POST with invalid payload from %s" % request.META.get("REMOTE_HOST", None)
            return HttpResponseBadRequest()

        return HttpResponse()

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

class WebHookMappingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WebHookMapping.objects.select_related("obs", "lastseenrevision").exclude(package="")
    serializer_class = WebHookMappingSerializer
