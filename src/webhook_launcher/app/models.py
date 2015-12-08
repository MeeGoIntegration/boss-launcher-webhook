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

import datetime
import os
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.utils import timezone

from webhook_launcher.app.misc import giturlparse, get_or_none

class BuildService(models.Model):

    def __unicode__(self):
        return self.weburl

    namespace = models.CharField(max_length=50, unique=True, help_text="This is also used to identify the OBS alias in BOSS processes")
    apiurl = models.CharField(max_length=250, unique=True)
    weburl = models.CharField(max_length=250, unique=True)


class VCSService(models.Model):

    def __unicode__(self):
        return self.netloc

    name = models.CharField(max_length=50, unique=True, help_text="Friendly name of this VCS hosting service")
    netloc = models.CharField(max_length=200, unique=True, help_text="Network location from payload (for example: git@git.merproject.org:1234)")
    ips = models.TextField(blank=True, null=True, help_text="Known IP adresses of this service (optional)")

class VCSNameSpace(models.Model):

    def __unicode__(self):
        return "%s%s" % (self.service, self.path)

    @staticmethod
    def find(repourl):
        url = giturlparse(repourl)
        return get_or_none(VCSNameSpace, service__netloc = url.netloc,
                           path=os.path.dirname(url.path))

    service = models.ForeignKey(VCSService, help_text="VCS service where this namespace is hosted")
    path = models.CharField(max_length=200, help_text="the network path (gitlab group or github organization eg. /mer-core)")
    default_project = models.ForeignKey("Project", blank=True, null=True, help_text="Default project for webhook placeholder creation")

class Project(models.Model):

    def __unicode__(self):
        return "%s on %s" % (self.name, self.obs)

    class Meta:
        unique_together = (("name", "obs"),)

    def is_repourl_allowed(self, repourl):

        repourl = giturlparse(repourl)
        netloc = repourl.netloc
        path = repourl.path.rsplit("/", 1)[1]
        if self.vcsnamespaces.count():
            return self.vcsnamespaces.filter(path=path, service__netloc=netloc).count()
        else:
            return True

    def is_user_allowed(self, user):

        user_groups = set(user.groups.all())
        groups = set(self.groups.all())
        if groups and (user_groups & groups):
            return True
        else:
            return False

    def matches(self, proj_name):
        # Update if/when https://pypi.python.org/pypi/django-regex-field/0.1.4 is used
        if proj_name == self.name:
            return True
        if self.match: # ie not None and not ""
            reg = re.compile(self.match) # this is optimised to a cache in regex-field
            if reg.match(proj_name):
                return True
        return False

    name = models.CharField(max_length=250, help_text="The OBS project name. eg nemo:mw")
    obs = models.ForeignKey(BuildService)
    official = models.BooleanField(default=True, help_text="If set then only valid namespaces can be used for the git repo")
    allowed = models.BooleanField(default=True, help_text="If not set then webhooks are not allowed for this project. This is useful for projects which should only have specific versions of packages promoted to them.")
    gated = models.BooleanField(default=False, help_text="If set then webhooks pointing at this project will be triggered to a side project instead and then an autopromotion attempted. This is useful for projects which apply formal entry checks and/or QA.")
    groups = models.ManyToManyField(Group, blank=True, null=True)
    vcsnamespaces = models.ManyToManyField(VCSNameSpace, blank=True, null=True)
    match = models.CharField(max_length=250, blank=True, null=True, help_text="If set then used as well as name to re.match() project names")

class WebHookMapping(models.Model):

    def __unicode__(self):
        return "%s/%s -> %s/%s" % (self.repourl, self.branch, self.project, self.package)

    @property
    def tag(self):
        lsr = self.lsr
        if lsr:
            return lsr.tag

    @property
    def revision(self):
        lsr = self.lsr
        if lsr:
            return lsr.revision

    @property
    def lsr(self):
        _lsr = self.lastseenrevision_set.all()
        if _lsr:
            return _lsr[0]

    @property
    def mapped(self):
        return self.project and self.package

    @property
    def rev_or_head(self):
        return self.revision or self.branch

    @property
    def project_disabled(self):
        # Just search all Projects for a match
        for project in Project.objects.all():
            if project.matches(self.project):
                print "Project disable check: project %s matches rules in %s" %(self.project, project.name)
                if project and not project.allowed: # Disabled if Project is marked not-allowed
                    return True
                if project and project.official: # Disabled if Project is official and namespace is not valid
                    repourl = giturlparse(self.repourl)
                    service = get_or_none(VCSService, netloc = repourl.netloc)
                    if not service:
                        return True
                    namespace = get_or_none(VCSNameSpace, service = service, path = os.path.dirname(repourl.path))
                    if not namespace:
                        return True

        return False

    def clean(self, exclude=None):
        self.repourl = self.repourl.strip()
        self.branch = self.branch.strip()
        self.project = self.project.strip()
        self.package = self.package.strip()

        if WebHookMapping.objects.exclude(pk=self.pk).filter(project=self.project, package=self.package, obs=self.obs).count():
            raise ValidationError('A mapping object with the same parameters already exists')

        repourl = giturlparse(self.repourl)
        service = get_or_none(VCSService, netloc = repourl.netloc)

        if settings.SERVICE_WHITELIST:
            if not service:
                raise ValidationError('%s is not an allowed service' % repourl.netloc)

        project = get_or_none(Project, name = self.project)

        if project and not project.allowed:
            raise ValidationError('Project %s does not allow mappings' % project)

        if project and project.official:
            namespace = get_or_none(VCSNameSpace, service = service, path = os.path.dirname(repourl.path))
            if not service or not namespace:
                raise ValidationError('Official project %s allows mapping from known service namespaces only' % project)

        if settings.STRICT_MAPPINGS:

            if project and not project.is_repourl_allowed(self.repourl):
                raise ValidationError("Webhook mapping repourl is not allowed by %s's strict rules" % project)

            if project and not project.is_user_allowed(self.user):
                raise ValidationError("Webhook mapping to %s not allowed for %s" % (project, self.user))

            if not self.project.startswith("home:%s" % self.user.username) and not self.user.is_superuser:
                raise ValidationError("Webhook mapping to %s not allowed for %s" % (project, self.user))

    def to_fields(self):
        fields = {}
        fields['repourl'] = self.repourl
        fields['branch'] = self.branch
        fields['pk'] = self.pk
        if self.project:
            fields['project'] = self.project
            fields['package'] = self.package
            fields['ev'] = { 'namespace' : self.obs.namespace }
        if self.token:
            fields['token'] = self.token
        if self.debian:
            fields['debian'] = self.debian
        if self.dumb:
            fields['dumb'] = self.dumb
        if self.revision:
            fields['revision'] = self.revision
        if self.tag:
            fields['tag'] = self.tag
        return fields

    # If any fields are added/removed then ensure they are handled
    # correctly in to_fields
    repourl = models.CharField(max_length=200, help_text="url of git repo to clone from. Should be a remote http[s]")
    branch = models.CharField(max_length=100, default="master", help_text="name of branch to use. If not specified default branch (or currently checked out one) will be used")
    project = models.CharField(max_length=250, default=settings.DEFAULT_PROJECT, help_text="name of an existing project under which to create or update the package")
    package = models.CharField(max_length=250, help_text="name of the package to create or update in OBS")
    token = models.CharField(max_length=100, default="", null=True, blank=True, help_text="a token that should exist in tag names and changelog entry headers to enable handling them")
    debian = models.CharField(max_length=2, default="", null=True, blank=True, choices = (('N','N'),('Y','Y')), help_text="Choose Y to turn on debian packaging support")
    dumb = models.CharField(max_length=2, default="", null=True, blank=True, choices = (('N','N'),('Y','Y')), help_text="Choose Y to take content of revision as-is without automatic processing (example: tarballs in git)")
    notify = models.BooleanField(default=True, help_text="Enable IRC notifications of events")
    build = models.BooleanField(default=True, help_text="Enable OBS build triggering")
    comment = models.TextField(blank=True, null=True, default="")
    user = models.ForeignKey(User, editable=False)
    obs = models.ForeignKey(BuildService)

class LastSeenRevision(models.Model):

    def __unicode__(self):
        return "%s @ %s/%s" % ( self.revision, self.mapping.repourl, self.mapping.branch )

    mapping = models.ForeignKey(WebHookMapping)
    revision = models.CharField(max_length=250)
    tag = models.CharField(max_length=50, blank=True, null=True)
    handled = models.BooleanField(default=False, editable=False)
    timestamp = models.DateTimeField(auto_now=True)
    emails = models.TextField(blank=True, null=True, editable=False)
    payload = models.TextField(blank=True, null=True, editable=False)

class QueuePeriod(models.Model):

    def __unicode__(self):
        return "Queue period from %s %s to %s %s for %s" % ( self.start_date or "", self.start_time,
                                                             self.end_date or "", self.end_time,
                                                             ",".join([str(prj) for prj in self.projects.all()]))

    class Meta:
        permissions = (("can_override_queueperiod", "Can override queue periods"),)


    def override(self, user):
        if not user:
            return False

        if user.has_perm("app.can_override_queueperiod"):
            return True

    def delay(self, dto=timezone.now()):
        if self.start_time <= self.end_time:
            if not (self.start_time <= dto.time() <= self.end_time):
                return False # wrong time of day

        if self.start_time >= self.end_time:
            if (self.start_time >= dto.time() >= self.end_time):
                return False # wrong time of day

        if self.start_date and (dto.date() < self.start_date):
            return False # not started yet

        if self.end_date and (dto.date() > self.end_date):
            return False # already ended

        return True

    start_time = models.TimeField(default=datetime.datetime.now())
    end_time = models.TimeField(default=datetime.datetime.now())
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    recurring = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)
    projects = models.ManyToManyField(Project)

class RelayTarget(models.Model):

    def __unicode__(self):
        return "%s webhook relay" % self.name

    active = models.BooleanField(default=True, help_text="Whether this relay will fire on matching events")
    name = models.CharField(max_length=50, help_text="Friendly name of recipient, for example: Organization name")
    url = models.CharField(max_length=200, help_text="HTTP(S) endpoint which will receive POST of GIT events (for example http://webhook.example.com/webhook/)")
    verify_SSL = models.BooleanField(default=True, help_text="Turn on SSL certificate verification")
    sources = models.ManyToManyField(VCSNameSpace, help_text="List of VCS namespaces (for example github organization or gitlab groups)")

