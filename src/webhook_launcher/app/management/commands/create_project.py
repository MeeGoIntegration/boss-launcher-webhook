from django.core.management.base import BaseCommand, CommandError

from webhook_launcher.app.models import BuildService, Project


class Command(BaseCommand):
    help = """Create new project.
    Optional --based-on will copy the values from given reference project.
    If project already exist it will modify values based on --based-on project
    given.

    Madatory arguments are --project and --obs
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            required=True,
            help="Project name to be created"
        )
        parser.add_argument(
            "--obs",
            required=True,
            help="OBS namespace"
        )
        parser.add_argument(
            "--based-on",
            dest="based_on",
            help="Create project based on values from another project"
        )

    def handle(self, *args, **options):
        if not options['based_on']:
            try:
                obs = BuildService.objects.get(namespace=options['obs'])
                prj, created = Project.objects.get_or_create(
                    name=options['project'], obs=obs
                )
            except BuildService.DoesNotExist:
                raise CommandError(
                    "Cannot find obs namespace: %s" % options['obs']
                )
        else:
            try:
                base_prj = Project.objects.get(
                    name=options['based_on'], obs__namespace=options['obs']
                )
            except Project.DoesNotExist:
                raise CommandError(
                    "Cannot find project %s (with obs namespace %s)" % (
                        options['based_on'], options['obs'])
                )
            prj, created = Project.objects.get_or_create(
                name=options['project'], obs=base_prj.obs
            )
            prj.official = base_prj.official
            prj.allowed = base_prj.allowed
            prj.gated = base_prj.gated
            prj.match = base_prj.match
            if not created:
                # if project is modified,
                # clear first old realtionships to groups and vcsnamescpaces
                prj.groups.clear()
                prj.vcsnamespaces.clear()
            for group in base_prj.groups.all():
                prj.groups.add(group)
            for vcsnamespace in base_prj.vcsnamespaces.all():
                prj.vcsnamespaces.add(vcsnamespace)
            prj.save()

        self.stdout.write(
            "%s: %s" % ("Created" if created else "Modified", prj)
        )
