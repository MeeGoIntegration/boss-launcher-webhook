#!/usr/bin/env python
# Copyright (C) 2017 Jolla Ltd.
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


# This is a Django manage.py copy which mocks out the calls to boss launch for
# local testing purposes.

import os
import sys

from mock import patch, DEFAULT


def launch_log(*args, **kwargs):
    params = ", ".join(x for x in [
        ", ".join(repr(x) for x in args),
        ", ".join("\n%s=%s" % (k, repr(v)) for k, v in kwargs.items()),
    ] if x)
    print "launch(%s)" % params
    return DEFAULT


@patch('webhook_launcher.app.boss.launch')
def main(launch_mock):
    launch_mock.side_effect = launch_log
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "webhook_launcher.settings"
    )
    os.environ.setdefault("WEBHOOK_DEVEL", "1")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
