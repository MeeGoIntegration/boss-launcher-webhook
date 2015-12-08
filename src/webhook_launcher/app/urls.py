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

from django.conf.urls import url, include
from django.contrib import admin
admin.autodiscover()
from rest_framework import routers
from webhook_launcher.app import views

router = routers.DefaultRouter()
router.register(r'webhookmappings', views.WebHookMappingViewSet)
router.register(r'buildservices', views.BuildServiceViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(router.urls)),
    url(r'^login/', views.remotelogin_redirect, name='redirect'),
    url(r'^landing/$', views.index, name='index'),
    url(r'$', views.index, name='index'),
]
