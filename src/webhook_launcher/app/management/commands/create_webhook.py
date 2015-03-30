from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from webhook_launcher.app.models import WebHookMapping, BuildService, LastSeenRevision
from optparse import make_option
import sys
from xml.etree import ElementTree as ET

def _extract_service_file(service_file):
    """ fetch repourl and revision info from OBS _service file """

    url = ""
    revision = ""
    try:
        tree = ET.parse(service_file)
    except ET.ParseError as e:
        return url, revision

    url = tree.find('.//param[@name="url"]').text
    revision = tree.find('.//param[@name="revision"]').text
    return url, revision

def create_branch_hook(project, package, branch, url, revision):
    # first try to find similar project
    prjs = WebHookMapping.objects.filter(project=project, package=package, repourl=url, branch="master")
    if len(prjs) > 0:
        obs = prjs[0].obs
    else:
        # fallback obs
        obs = BuildService.objects.all()[0]

    obj, _ = WebHookMapping.objects.get_or_create(project=project,
                                                  branch=branch,
                                                  repourl=url,
                                                  notify=True,
                                                  build=True,
                                                  user=User.objects.get(id=1),
                                                  obs=obs,
                                                  package=package)

    if obj.lastseenrevision_set.count():
        last_seen = obj.lastseenrevision_set.all()[0]
        last_seen.revision = revision
        last_seen.save()
    else:
        LastSeenRevision.objects.create(mapping=obj, revision=revision)

    return obj

class Command(BaseCommand):
    help = 'pre-create webhooks for branched projects'

    option_list = BaseCommand.option_list + (
        make_option("-s", "--service-file", dest="service_file", metavar="FILE",
                    help="Read OBS _service file from FILE. Another option is use --url and --revision"),
        make_option("-b", "--branch", dest="branch",
                    help="Define branch name"),
        make_option("-p", "--project", dest="project",
                    help="Define project name"),
        make_option("--package", dest="package",
                    help="Define package name"),
        make_option("-u", "--url", dest="url",
                    help="Define project repourl"),
        make_option("-r", "--revision", dest="revision",
                    help="Define package revision"),

        )
    def handle(self, *args, **options):

        if options['service_file'] and not (options['url'] or options['revision']):
            url, revision = _extract_service_file(options['service_file'])
            if not url or not revision:
                print "could not parse repourl and revision form: %s" % options['service_file']
                sys.exit(1)

        elif options['url'] and options['revision'] and not options['service_file']:
            url = options['url']
            revision = options['revision']
        else:
            print "please give either --service-file or --url and --revision"
            sys.exit(1)

        if options['branch'] and options['project'] and options['package']:
            prj = options['project']
            branch = options['branch']
            package = options['package']
        else:
            print "please give --project, --branch, and --package"
            sys.exit(1)

        mapping = create_branch_hook(project=prj, package=package, branch=branch,
                                     url=url, revision=revision)

        print "created: %s" % mapping
