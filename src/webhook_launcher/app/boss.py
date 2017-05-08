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

from django.conf import settings
from RuoteAMQP import Launcher

def launch(process, fields):
    """ BOSS process launcher

    :param process: process definition file
    :param fields: dict of workitem fields
    """
    with open(process, mode='r') as process_file:
        pdef = process_file.read()

    launcher = Launcher(amqp_host = settings.BOSS_HOST,
                        amqp_user = settings.BOSS_USER,
                        amqp_pass = settings.BOSS_PASS,
                        amqp_vhost = settings.BOSS_VHOST)

    print "launching to (%s,%s)" %(settings.BOSS_HOST, settings.BOSS_VHOST)
    launcher.launch(pdef, fields)

def launch_queue(fields):
    launch(settings.VCSCOMMIT_QUEUE, fields)

def launch_notify(fields):
    launch(settings.VCSCOMMIT_NOTIFY, fields)

def launch_build(fields):
    launch(settings.VCSCOMMIT_BUILD, fields)

def launch_mirror(fields):
    launch(settings.VCSCOMMIT_MIRROR, fields)
