from __future__ import absolute_import

from bureaucrat.launcher import Launcher

from django.conf import settings

def launch(process_path, fields):
    """Bureaucrat process launcher.

    :param process_path: path to process definition file
    :param fields: dict of workitem fields
    """

    launcher = Launcher({
        "host": settings.AMQP_HOST,
        "launcher_routing_key": settings.AMQP_ROUTING_KEY
    })
    launcher.launch(process_path, fields)

def launch_queue(fields):
    launch(settings.VCSCOMMIT_QUEUE, fields)

def launch_notify(fields):
    launch(settings.VCSCOMMIT_NOTIFY, fields)

def launch_build(fields):
    launch(settings.VCSCOMMIT_BUILD, fields)

