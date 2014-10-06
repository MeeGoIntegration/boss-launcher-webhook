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
import json
from pprint import pprint
import struct, socket
from collections import defaultdict

from django.http import ( HttpResponse, HttpResponseBadRequest, HttpResponseRedirect,
                          HttpResponseForbidden, HttpResponseNotAllowed )
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework import status
import rest_framework_filters as filters

from webhook_launcher.app.boss import launch_queue
from webhook_launcher.app.models import WebHookMapping, BuildService, LastSeenRevision, Project
from webhook_launcher.app.serializers import WebHookMappingSerializer, BuildServiceSerializer, LastSeenRevisionSerializer


def remotelogin_redirect(request):
    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

def index(request):
    """
    GET: returns 403

    POST: process a webhook callback from bitbucket or github
    """

    if request.method == 'GET':
        if not settings.PUBLIC_LANDING_PAGE and not request.user.is_authenticated():
            return HttpResponseRedirect(settings.LOGIN_URL)

        mappings = defaultdict(dict)
        off_prjs = set([prj.name for prj in Project.objects.filter(official=True, allowed=True)])
        maps = WebHookMapping.objects.exclude(package="").filter(Q(project__in=off_prjs) | Q(user=request.user)).prefetch_related("obs", "lastseenrevision_set")
        for mapobj in maps:
            if not mapobj.project in mappings:
                mappings[mapobj.project] = {"personal" : mapobj.user.pk == request.user.pk,
                                            "official" : mapobj.project in off_prjs,
                                            "obsweburl" : mapobj.obs.weburl, "packages" : []}

            mappings[mapobj.project]["packages"].append(mapobj.to_fields())

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
            print "POST with unknown content type %s" % (ctype)
            return HttpResponseBadRequest()

        try:
            data = json.loads(payload)
            # merge in GET params
            get = {}
            for key, values in request.GET.lists():
                get[key] = values
            data['webhook_parameters'] = get

            pprint(data, indent=2, width=80, depth=6)
            launch_queue({"payload" : data})

        except Exception as e:
            print e
            print "POST with invalid payload from %s" % request.META.get("REMOTE_HOST", None)
            return HttpResponseBadRequest()

        return HttpResponse()

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

class WebHookMappingFilter(filters.FilterSet):
    package = filters.AllLookupsFilter(name='package')
    project = filters.AllLookupsFilter(name='project')
    repourl = filters.AllLookupsFilter(name='repourl')
    branch = filters.AllLookupsFilter(name='branch')
    user = filters.AllLookupsFilter(name='user__username')
    
    class Meta:
        model = WebHookMapping
        fields = ["package", "project", "repourl", "user__username", "build"]

class WebHookMappingViewSet(viewsets.ModelViewSet):
    queryset = WebHookMapping.objects.select_related("obs", "lastseenrevision").exclude(package="")
    serializer_class = WebHookMappingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_class = WebHookMappingFilter

    def pre_save(self, obj):
        obj.user = self.request.user

    def post_save(self, obj, created=False):
        request = self.get_renderer_context()['request']
        revision = request.DATA.get('revision', None)
        if revision is None:
            return
        tag = request.DATA.get('tag', None)

        if created:
            lsr = LastSeenRevision(mapping = obj, revision = revision, tag=tag)
        else:
            lsr = obj.lsr
            lsr.revision = revision
            if tag:
                lsr.tag = tag
            
        lsr.save()

    # PUT / trigger webhook
    def update(self, request, pk=None):
        try:
            hook = WebHookMapping.objects.get(pk=pk)
        except WebHookMapping.DoesNotExist:
            return Response({'cannot find webhook id' : pk }, status=status.HTTP_404_NOT_FOUND)

        msg = hook.trigger_build()
        return Response({ 'WebHookMapping Triggered by API': msg })

    # PATCH / update webhook
    def partial_update(self, request, pk=None):
        try:
            hook = WebHookMapping.objects.get(pk=pk)
        except WebHookMapping.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = WebHookMappingSerializer(hook)

        #first take the original data
        patched_data = serializer.data

        # patch keys from request.DATA
        for key, value in request.DATA.items():
            patched_data[key] = value

        # for obs input is namespace but we store more.
        obs = request.DATA.get('obs', None)
        if not obs and patched_data.get('obs', None):
            patched_data['obs'] = patched_data['obs']['namespace']

        serializer = WebHookMappingSerializer(hook, data=patched_data)

        lsr_data = request.DATA.get('lsr', None)
        revision = request.DATA.get('revision', None)

        if lsr_data or revision:
            # in rare case there is no mapping to lsr from hook we create one
            if not hook.lsr:
                if revision:
                    LastSeenRevision.objects.get_or_create(mapping=hook, revision=revision)
                else:
                    return Response({"detail": "no LastSeenRevision mapped to object. Please give also 'revision'"},
                                    status=status.HTTP_400_BAD_REQUEST)

            lsr_serializer = LastSeenRevisionSerializer(hook.lsr, data=lsr_data)
            lsr_patch_data = lsr_serializer.data

            if lsr_data:
                for key, value in lsr_data.items():
                    lsr_patch_data[key] = value
            if revision:
                lsr_patch_data['revision'] = revision

            lsr_serializer = LastSeenRevisionSerializer(hook.lsr, data=lsr_patch_data)

        if serializer.is_valid():
             if lsr_data or revision:
                if lsr_serializer.is_valid():
                    serializer.save()
                    lsr_serializer.save()
             else:
                serializer.save()
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)

    @detail_route(methods=['get'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def find(self, request, obsname, project, package):
        qs = WebHookMapping.objects.get(obs__namespace=obsname, project=project, package=package)
        ser = WebHookMappingSerializer(qs)
        return Response(ser.data)

class LastSeenRevisionViewSet(viewsets.ModelViewSet):
    queryset = LastSeenRevision.objects.all()
    serializer_class = LastSeenRevisionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

# Now to add a function access to trigger a webhook
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, ))
def trigger(request, format=None, pk=None):
    if pk:
        hook = WebHookMapping(id=pk)
        hook.trigger()
        content = { 'status': 'Webhook was triggered' }
    elif 'id' in request.DATA:
        id = request.DATA['id']
        hook = WebHookMapping(id=id)
        hook.trigger()
        content = { 'status': 'Webhook was triggered' }
    else:
        content = { 'status': 'Webhook not found' }
            
    return Response(content)

class BuildServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BuildService.objects.all()
    serializer_class = BuildServiceSerializer

