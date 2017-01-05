# -*- coding: utf-8 -*-
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

import os, sys
from distutils.core import setup

from setuptools import find_packages

static_files=[('/etc/skynet', ['src/webhook_launcher/webhook.conf']),
                ('/usr/share/webhook_launcher/processes', 
                   ['src/webhook_launcher/processes/VCSCOMMIT_NOTIFY',
                    'src/webhook_launcher/processes/VCSCOMMIT_BUILD',
                    'src/webhook_launcher/processes/VCSCOMMIT_QUEUE',
                   ]
                )
             ]

setup(
    name = "webhook_launcher",
    version = "0.2.0",
    url = '',
    license = 'GPLv2',
    description = "webhook launcher",
    author = 'Islam Amer <pharon@gmail.com>',
    packages = ['webhook_launcher',
                'webhook_launcher.app',
                'webhook_launcher.app.templatetags',
                'webhook_launcher.app.migrations',
                'webhook_launcher.app.management',
                'webhook_launcher.app.management.commands',
                ],    
    package_dir = {'':'src'},
    package_data = { 'webhook_launcher.app' : ['templates/admin/*.html',
                                               'templates/app/*.html',
                                               'static/images/*.png',
                                               'static/*.gif',
                                               'static/*.css',
                                               'static/*.js',
                                              ]
                   },
    data_files = static_files,
)
