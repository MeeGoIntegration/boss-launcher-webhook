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

from django.conf.urls import *
from django.contrib import admin
admin.autodiscover()
from rest_framework import routers
from  webhook_launcher.app import views

router = routers.DefaultRouter()
router.register(r'webhookmappings', views.WebHookMappingViewSet)
router.register(r'lastseenrevisions', views.LastSeenRevisionViewSet)

# The .../find view supports an alternate pk lookup
find = views.WebHookMappingViewSet.as_view({'get': 'find', 'put': 'find'})
router.register(r'buildservices', views.BuildServiceViewSet)

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(router.urls)),
    url(r'^api/webhookmappings/(?P<obsname>.*)/(?P<project>.*)/(?P<package>.*)/find', find),
    url(r'^api/webhookmappings/(?P<pk>[0-9]+)/trigger/', views.trigger),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^$', 'webhook_launcher.app.views.index', name='index'),
)
