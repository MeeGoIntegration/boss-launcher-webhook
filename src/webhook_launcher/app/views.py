# Copyright (C) 2013-2017 Jolla Ltd.
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

""" webhook view """

import json
import socket
import struct
from collections import defaultdict
from pprint import pprint

import django_filters
from django.conf import settings
from django.db.models import Q
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed,
    HttpResponseRedirect
)
from django.shortcuts import render
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from webhook_launcher.app.boss import launch_queue
from webhook_launcher.app.models import BuildService, Project, WebHookMapping
from webhook_launcher.app.serializers import (
    BuildServiceSerializer, WebHookMappingSerializer
)


def remotelogin_redirect(request):
    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)


def index(request):
    """
    GET: returns 403

    POST: process a webhook callback from bitbucket or github
    """

    if request.method == 'GET':
        if (
            not settings.PUBLIC_LANDING_PAGE and
            not request.user.is_authenticated
        ):
            return HttpResponseRedirect(settings.LOGIN_URL)

        mappings = defaultdict(dict)
        off_prjs = set([
            prj.name for prj in
            Project.objects.filter(official=True, allowed=True)
        ])
        maps = WebHookMapping.objects.exclude(package="").filter(
            Q(project__in=off_prjs) | Q(user=request.user)
        ).prefetch_related("obs", "lastseenrevision_set")
        for mapobj in maps:
            if mapobj.project not in mappings:
                mappings[mapobj.project] = {
                    "personal": mapobj.user.pk == request.user.pk,
                    "official": mapobj.project in off_prjs,
                    "obsweburl": mapobj.obs.weburl,
                    "packages": []
                }

            mappings[mapobj.project]["packages"].append(mapobj.to_fields())

        return render(
            request, 'app/index.html', {'mappings': dict(mappings)}
        )

    elif request.method == 'POST':
        # TODO: Move to database ip filter list
        # Use the ip_filter to decide whether to accept a post
        if settings.POST_IP_FILTER:
            # If behind a rev-proxy then use XFF header
            if settings.POST_IP_FILTER_HAS_REV_PROXY:
                # Take the last value only to avoid spoofing
                ip = request.META["HTTP_X_FORWARDED_FOR"].split(",")[-1]
                print "Using %s as IP from HTTP_X_FORWARDED_FOR: %s" % (
                    ip, request.META["HTTP_X_FORWARDED_FOR"]
                )
            else:
                ip = request.META["REMOTE_IP"]
            ipaddr = struct.unpack('<L', socket.inet_aton(ip))[0]
            ip_ok = False
            for netmask in settings.NETMASKS:
                if ipaddr & netmask == netmask:
                    ip_ok = True
                    break
            if not ip_ok:
                print "POST from %s not in settings.post_ip_filter" % (ip,)
                return HttpResponseBadRequest()

        ctype = request.META.get("CONTENT_TYPE", None)
        if ctype == "application/json":
            payload = request.body
        elif ctype == "application/x-www-form-urlencoded":
            payload = request.POST.get("payload", None)
        else:
            print "POST with unknown content type %s" % (ctype)
            return HttpResponseBadRequest()

        try:
            data = json.loads(payload)
            # merge in GET params
            get = {}
            for key, values in request.GET.lists():
                get[key] = values
            data['webhook_parameters'] = get

            print "Payload to launch:"
            pprint(data, indent=2, width=80, depth=6)
            launch_queue({"payload": data})
            print "launched"

        except Exception as e:
            print e
            print "POST with invalid payload from %s" % \
                request.META.get("REMOTE_HOST", None)
            return HttpResponseBadRequest()

        return HttpResponse()

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


class WebHookMappingFilter(django_filters.FilterSet):
    obs = django_filters.CharFilter(name='obs__namespace')
    user = django_filters.CharFilter(name='user__username')

    class Meta:
        model = WebHookMapping
        fields = {
            "package": ['exact'],
            "project": ['exact'],
            "repourl": ['exact'],
            "build": ['exact'],
        }


class WebHookMappingViewSet(viewsets.ModelViewSet):
    queryset = WebHookMapping.objects.select_related("obs").exclude(package="")
    serializer_class = WebHookMappingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_class = WebHookMappingFilter

    def pre_save(self, obj):
        obj.user = self.request.user

    @detail_route(
        methods=['put'],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def trigger(self, request, pk=None):
        try:
            hook = WebHookMapping.objects.get(pk=pk)
            msg = hook.trigger_build()
            return Response({'WebHookMapping Triggered by API': msg})
        except WebHookMapping.DoesNotExist:
            return Response(
                {'WebHookMapping': 'Not found'},
                status=status.HTTP_404_NOT_FOUND,
            )


class BuildServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BuildService.objects.all()
    serializer_class = BuildServiceSerializer
