from xml.etree import ElementTree as ET

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from webhook_launcher.app.models import (
    BuildService, LastSeenRevision, WebHookMapping
)


def _extract_service_file(service_file):
    """ fetch repourl and revision info from OBS _service file """

    url = ""
    revision = ""
    try:
        tree = ET.parse(service_file)
    except ET.ParseError:
        return url, revision

    url = tree.find('.//param[@name="url"]').text
    revision = tree.find('.//param[@name="revision"]').text
    return url, revision


def create_branch_hook(project, package, branch, url, revision):
    # first try to find similar project
    prjs = WebHookMapping.objects.filter(
        project=project, package=package, repourl=url, branch="master"
    )
    if len(prjs) > 0:
        obs = prjs[0].obs
    else:
        # fallback obs
        obs = BuildService.objects.all()[0]

    obj, _ = WebHookMapping.objects.get_or_create(
        project=project,
        branch=branch,
        repourl=url,
        notify=True,
        build=True,
        user=User.objects.get(id=1),
        obs=obs,
        package=package,
    )

    if obj.lastseenrevision_set.count():
        last_seen = obj.lastseenrevision_set.all()[0]
        last_seen.revision = revision
        last_seen.save()
    else:
        LastSeenRevision.objects.create(mapping=obj, revision=revision)

    return obj


class Command(BaseCommand):
    help = 'pre-create webhooks for branched projects'

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--service-file",
            metavar="FILE",
            help="Read OBS _service file from FILE. "
                 "Another option is use --url and --revision"
        )
        parser.add_argument(
            "-b", "--branch",
            help="Define branch name"
        )
        parser.add_argument(
            "-p", "--project",
            help="Define project name"
        )
        parser.add_argument(
            "--package",
            help="Define package name"
        )
        parser.add_argument(
            "-u", "--url",
            help="Define project repourl"
        )
        parser.add_argument(
            "-r", "--revision",
            help="Define package revision"
        )

    def handle(self, *args, **options):

        if (
            options['service_file'] and
            not (options['url'] or options['revision'])
        ):
            url, revision = _extract_service_file(options['service_file'])
            if not url or not revision:
                raise CommandError(
                    "could not parse repourl and revision form: %s" %
                    options['service_file']
                )

        elif (
            options['url'] and options['revision'] and
            not options['service_file']
        ):
            url = options['url']
            revision = options['revision']
        else:
            raise CommandError(
                "please give either --service-file or --url and --revision"
            )

        if options['branch'] and options['project'] and options['package']:
            prj = options['project']
            branch = options['branch']
            package = options['package']
        else:
            raise CommandError(
                "please give --project, --branch, and --package"
            )

        mapping = create_branch_hook(
            project=prj, package=package, branch=branch,
            url=url, revision=revision
        )

        self.stdout.write("created: %s" % mapping)
