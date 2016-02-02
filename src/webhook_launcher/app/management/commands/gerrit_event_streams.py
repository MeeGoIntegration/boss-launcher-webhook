from django.core.management.base import BaseCommand, CommandError
from webhook_launcher.app.models import VCSService 
from webhook_launcher.app.misc import giturlparse
from webhook_launcher.app.bureaucrat import launch_queue
from pygerrit.client import GerritClient
from optparse import make_option
import sys, time, json


def listen_streams():
    gerrit_instances = {}
    for inst in VCSService.objects.filter(gerrit=True):
        print "Connecting to gerrit", inst.netloc
        parsed_netloc = giturlparse(inst.netloc)
        gerrit = GerritClient(host=parsed_netloc.netloc, port=parsed_netloc.port)
        try:
            version = gerrit.gerrit_version()
            print "Connected to Gerrit", version, "at", inst.netloc, ", starting event stream"
            gerrit.start_event_stream()
            gerrit_instances[inst.netloc] = gerrit
        except Exception, e:
            print e, "connecting to Gerrit", inst.netloc

    while True:
        for server, gerrit in gerrit_instances.items():
            event = None
            event = gerrit.get_event(block=False, timeout=1)
            if event is not None:
                data = event.json
                data["gerrit"] = server
                launch_queue({"payload" : data})
            else:
                time.sleep(1)

class Command(BaseCommand):
    def handle(self, *args, **options):
        listen_streams()
        sys.exit(0)
