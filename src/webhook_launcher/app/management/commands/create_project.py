from django.core.management.base import BaseCommand
from webhook_launcher.app.models import Project, BuildService
from optparse import make_option
import sys

def create_project(opt):

    if not opt['based_on']:
        try:
            obs = BuildService.objects.get(namespace=opt['obs'])
            return  Project.objects.get_or_create(name=opt['project'], obs=obs)
        except BuildService.DoesNotExist as e:
            print "Cannot find obs namespace: %s" % obs
            return None, None
    else:
        try:
            base_prj = Project.objects.get(name=opt['based_on'], obs__namespace=opt['obs'])
        except Project.DoesNotExist as e:
            print "Cannot find %s" % opt['based_on']
            return None, None
        prj, created = Project.objects.get_or_create(name=opt['project'], obs=base_prj.obs)
        prj.official = base_prj.official
        prj.allowed = base_prj.allowed
        prj.gated = base_prj.gated
        prj.match = base_prj.match
        if not created:
            # if project is modified, clear first old realtionships to groups and vcsnamescpaces
            prj.groups.clear()
            prj.vcsnamespaces.clear()
        for group in base_prj.groups.all():
            prj.groups.add(group)
        for vcsnamespace in base_prj.vcsnamespaces.all():
            prj.vcsnamespaces.add(vcsnamespace)
        prj.save()

    return prj, created

class Command(BaseCommand):
    help = """
    Create new project. Optional --based-on will copy the values from given reference project.
    If project already exist it will modify values based on --based-on project given

    Madatory arguments are --project and --obs"""

    option_list = BaseCommand.option_list + (
        make_option("--project", action='store', dest="project", help="Project name to be created"),
        make_option("--obs", action='store', dest="obs", help="OBS namespace"),
        make_option("--based-on", action='store', dest="based_on", help="Create project based on values from another project"),
        )

    def handle(self, *args, **options):

        if not options['project'] or not options['obs']:
            print "Please give both mandatory arguments --project and --obs"
            sys.exit(1)
        prj, created = create_project(options)
        if prj:
            print "%s: %s" % ("Created" if created else "Modified", prj)
            sys.exit(0)
        else:
            sys.exit(1)
