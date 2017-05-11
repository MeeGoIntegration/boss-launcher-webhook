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
# along with this program; if not, write to
# the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import re

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from webhook_launcher.app.boss import launch_notify, launch_build
from webhook_launcher.app.misc import get_or_none, giturlparse


# FIXME: All null=True + blank=True text fields
#   Unless it is intentional that text field can be set to either NULL or ''
#   (emtpy string), then it is recommended not to use null=True, to avoid
#   situatioon where the field has two possible values for empty. As that can
#   problematic for example in lookups where NULL and '' behave differently

class BuildService(models.Model):
    namespace = models.CharField(
        max_length=50,
        unique=True,
        help_text="This is also used to identify the OBS alias "
                  "in BOSS processes",
    )
    apiurl = models.CharField(
        max_length=250,
        unique=True,
    )
    weburl = models.CharField(
        max_length=250,
        unique=True,
    )

    def __unicode__(self):
        return self.weburl


class VCSService(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Friendly name of this VCS hosting service",
    )
    netloc = models.CharField(
        max_length=200,
        unique=True,
        help_text="Network location from payload "
                  "(for example: git@git.merproject.org:1234)",
    )
    ips = models.TextField(
        blank=True,
        null=True,
        help_text="Known IP adresses of this service (optional)",
    )

    def __unicode__(self):
        return self.netloc


class VCSNameSpace(models.Model):
    service = models.ForeignKey(
        VCSService,
        help_text="VCS service where this namespace is hosted",
    )
    path = models.CharField(
        max_length=200,
        help_text="the network path "
                  "(gitlab group or github organization eg. /mer-core)",
    )
    default_project = models.ForeignKey(
        "Project",
        blank=True,
        null=True,
        help_text="Default project for webhook placeholder creation",
    )

    def __unicode__(self):
        return "%s%s" % (self.service, self.path)

    @staticmethod
    def find(repourl):
        url = giturlparse(repourl)
        return get_or_none(
            VCSNameSpace,
            service__netloc=url.netloc,
            path=os.path.dirname(url.path)
        )


class Project(models.Model):
    name = models.CharField(
        max_length=250,
        help_text="The OBS project name. eg nemo:mw",
    )
    obs = models.ForeignKey(
        BuildService,
    )
    official = models.BooleanField(
        default=True,
        help_text="If set then only valid namespaces can be used for the "
                  "git repo",
    )
    allowed = models.BooleanField(
        default=True,
        help_text="If not set then webhooks are not allowed for this project. "
                  "This is useful for projects which should only have "
                  "specific versions of packages promoted to them.",
    )
    gated = models.BooleanField(
        default=False,
        help_text="If set then webhooks pointing at this project will be "
                  "triggered to a side project instead and then "
                  "an autopromotion attempted. This is useful for projects "
                  "which apply formal entry checks and/or QA.",
    )
    groups = models.ManyToManyField(
        Group,
        blank=True,
    )
    vcsnamespaces = models.ManyToManyField(
        VCSNameSpace,
        blank=True,
    )
    match = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text="If set then used as well as name to re.match() "
                  "project names",
    )

    class Meta:
        unique_together = (("name", "obs"),)

    def __unicode__(self):
        return "%s on %s" % (self.name, self.obs)

    def is_repourl_allowed(self, repourl):

        repourl = giturlparse(repourl)
        netloc = repourl.netloc
        path = repourl.path.rsplit("/", 1)[1]
        if self.vcsnamespaces.count():
            return self.vcsnamespaces.filter(
                path=path,
                service__netloc=netloc,
            ).count()
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
        # TODO Update if/when
        # https://pypi.python.org/pypi/django-regex-field/0.1.4 is used
        if proj_name == self.name:
            return True
        if self.match:
            # this is optimised to a cache in regex-field
            reg = re.compile(self.match)
            if reg.match(proj_name):
                return True
        return False

    @classmethod
    def get_matching(cls, name, apiurl):
        # Search all Projects for a match
        # Exception raised if more than one match found
        found=None
        for project in Project.objects.filter(obs__apiurl=apiurl):
            if project.matches(name):
                if found is not None:
                    raise MultipleObjectsReturned("Project %s matches both %s and %s (possibly more)" %
                                                  (name, found.name, project.name))
                found = project
        return found

class WebHookMapping(models.Model):
    # If any fields are added/removed then ensure they are handled
    # correctly in to_fields and the webhook_diff.py
    repourl = models.CharField(
        max_length=200,
        help_text="url of git repo to clone from. Should be a remote http[s]",
    )
    branch = models.CharField(
        max_length=100,
        default="master",
        help_text="name of branch to use. If not specified default branch "
                  "(or currently checked out one) will be used",
    )
    project = models.CharField(
        max_length=250,
        default=settings.DEFAULT_PROJECT,
        help_text="name of an existing project under which to create "
                  "or update the package",
    )
    package = models.CharField(
        max_length=250,
        help_text="name of the package to create or update in OBS",
    )
    token = models.CharField(
        max_length=100,
        default="",
        null=True,
        blank=True,
        help_text="a token that should exist in tag names and "
                  "changelog entry headers to enable handling them",
    )
    debian = models.CharField(
        max_length=2,
        default="",
        null=True,
        blank=True,
        choices=(
            ('N', 'N'),
            ('Y', 'Y'),
        ),
        help_text="Choose Y to turn on debian packaging support",
    )
    dumb = models.CharField(
        max_length=2,
        default="",
        null=True,
        blank=True,
        choices=(
            ('N', 'N'),
            ('Y', 'Y'),
        ),
        help_text="Choose Y to take content of revision as-is without "
                  "automatic processing (example: tarballs in git)",
    )
    notify = models.BooleanField(
        default=True,
        help_text="Enable IRC notifications of events",
    )
    build = models.BooleanField(
        default=True,
        help_text="Enable OBS build triggering",
    )
    comment = models.TextField(
        blank=True,
        null=True,
        default="",
    )
    user = models.ForeignKey(
        User,
        editable=False,
    )
    obs = models.ForeignKey(
        BuildService,
    )

    class Meta:
        unique_together = (("project", "package", "obs"),)

    def __unicode__(self):
        return "%s/%s -> %s/%s" % (
            self.repourl, self.branch, self.project, self.package
        )

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
        # TODO: refactor the WebHookMapping and LastSeenRevision relation
        if not hasattr(self, '_lsr'):
            if self.pk:
                self._lsr, _ = LastSeenRevision.objects.get_or_create(
                    mapping=self
                )
            else:
                return None
        return self._lsr

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
                print "Project disable check: %s matches rules in %s" % (
                    self.project, project.name
                )
                if project and not project.allowed:
                    # Disabled if Project is marked not-allowed
                    return True
                if project and project.official:
                    # Disabled if Project is official and namespace is not
                    # valid
                    repourl = giturlparse(self.repourl)
                    service = get_or_none(
                        VCSService,
                        netloc=repourl.netloc,
                    )
                    if not service:
                        return True
                    namespace = get_or_none(
                        VCSNameSpace,
                        service=service,
                        path=os.path.dirname(repourl.path),
                    )
                    if not namespace:
                        return True

        return False

    def clean(self, exclude=None):
        self.repourl = self.repourl.strip()
        self.branch = self.branch.strip()
        self.project = self.project.strip()
        self.package = self.package.strip()

        if WebHookMapping.objects.exclude(pk=self.pk).filter(
            project=self.project,
            package=self.package,
            obs=self.obs
        ).count():
            raise ValidationError(
                'A mapping object with the same parameters already exists'
            )

        repourl = giturlparse(self.repourl)
        service = get_or_none(VCSService, netloc=repourl.netloc)

        if settings.SERVICE_WHITELIST and service is None:
            raise ValidationError(
                '%s is not an allowed service' % repourl.netloc
            )

        project = get_or_none(Project, name=self.project)

        if project and not project.allowed:
            raise ValidationError(
                'Project %s does not allow mappings' % project
            )

        if project and project.official:
            namespace = get_or_none(
                VCSNameSpace,
                service=service,
                path=os.path.dirname(repourl.path),
            )
            if not service or not namespace:
                raise ValidationError(
                    'Official project %s allows mapping from known service '
                    'namespaces only' % project
                )

        if settings.STRICT_MAPPINGS:
            if project and not project.is_repourl_allowed(self.repourl):
                raise ValidationError(
                    "Webhook mapping repourl is not allowed by %s's "
                    "strict rules" % project
                )
            if project and not project.is_user_allowed(self.user):
                raise ValidationError(
                    "Webhook mapping to %s not allowed for %s" %
                    (project, self.user)
                )
            if (
                not self.project.startswith("home:%s" % self.user.username) and
                not self.user.is_superuser
            ):
                raise ValidationError(
                    "Webhook mapping to %s not allowed for %s" %
                    (project, self.user)
                )

    def trigger_build(self, user=None, tag=None, force=False):
        if not self.pk:
            raise RuntimeError(
                "trigger_build() on unsaved WebHookMapping"
            )

        # Only fire for projects which allow webhooks. We can't just
        # rely on validation since a Project may forbid hooks after
        # the hook was created
        if self.project_disabled:
            print "Project has build disabled"
            return

        handled = self.lsr.handled and self.lsr.tag == tag and not force
        if handled:
            print "build already handled, skipping"
        build = self.build and self.mapped and not handled
        qp = None
        if user is None:
            user = self.user.username

        if build:
            if tag:
                self.lsr.tag = tag

            # Find possible queue period objects
            qps = QueuePeriod.objects.filter(
                projects__name=self.project,
                projects__obs=self.obs,
            )
            for qp in qps:
                if qp.delay() and not qp.override(webuser=user):
                    print "Build trigger for %s delayed by %s" % (self, qp)
                    print qp.comment
                    build = False
                    break
            else:
                qp = None

        message = self._get_build_message(user, force, handled, qp)
        fields = self.to_fields()
        fields['msg'] = message

        if self.notify:
            launch_notify(fields)

        if build:
            fields = self.to_fields()
            launch_build(fields)
            self.lsr.handled = True

        self.lsr.save()

        return message

    def _get_build_message(self, user, force=None, handled=False, qp=None):

        parts = []
        if force:
            parts.append("Forced build trigger:")

        if self.tag:
            parts.append("Tag %s" % self.tag)
        else:
            parts.append(self.revision)

        parts.append(
            "by %s in %s branch of %s" % (
                user, self.branch, self.repourl,
            )
        )
        if not self.mapped:
            parts.append("- which is not mapped yet. Please map it.")

        elif self.build:
            parts.append(
                "- which will trigger build in project %s package "
                "%s (%s/package/show/%s/%s)" % (
                    self.project, self.package, self.obs.weburl,
                    self.project, self.package,
                )
            )

        elif handled:
            parts.append("- which was already handled; skipping")

        elif qp:
            parts.append("- which will be delayed by %s" % qp)
            if qp.comment:
                parts.append("(%s)" % qp.comment)

        return " ".join(parts)

    def handle_commit(self, user=None, notify=None):
        if not self.pk:
            raise RuntimeError(
                "handle_commit() on unsaved WebHookMapping"
            )

        if user is None:
            user = self.user.username
        if notify is None:
            notify = self.notify

        self.lsr.tag = ""
        self.lsr.handled = False
        self.lsr.save()

        if not notify:
            return

        message = "Commit(s) pushed by %s to %s branch of %s" % (
            user, self.branch, self.repourl
        )
        if not self.mapped:
            message = "%s, which is not mapped yet. Please map it." % message

        fields = self.to_fields()
        fields['msg'] = message
        print message
        launch_notify(fields)

    def to_fields(self):
        fields = {}
        fields['repourl'] = self.repourl
        fields['branch'] = self.branch
        fields['pk'] = self.pk
        if self.project:
            fields['project'] = self.project
            fields['package'] = self.package
            fields['ev'] = {
                'namespace': self.obs.namespace
            }
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


class LastSeenRevision(models.Model):
    mapping = models.ForeignKey(
        WebHookMapping,
    )
    revision = models.CharField(
        max_length=250,
    )
    tag = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    handled = models.BooleanField(
        default=False,
        editable=False,
    )
    timestamp = models.DateTimeField(
        auto_now=True,
    )
    emails = models.TextField(
        blank=True,
        null=True,
        editable=False,
    )
    payload = models.TextField(
        blank=True,
        null=True,
        editable=False,
    )

    def __unicode__(self):
        return "%s @ %s/%s" % (
            self.revision, self.mapping.repourl, self.mapping.branch
        )


class QueuePeriod(models.Model):
    start_time = models.TimeField(
        default=timezone.now,
    )
    end_time = models.TimeField(
        default=timezone.now,
    )
    start_date = models.DateField(
        blank=True,
        null=True,
    )
    end_date = models.DateField(
        blank=True,
        null=True,
    )
    recurring = models.BooleanField(
        default=False,
    )
    comment = models.TextField(
        blank=True,
        null=True,
    )
    projects = models.ManyToManyField(
        Project,
    )

    class Meta:
        permissions = (
            ("can_override_queueperiod", "Can override queue periods"),
        )

    def __unicode__(self):
        return "Queue period from %s %s to %s %s for %s" % (
            self.start_date or "", self.start_time, self.end_date or "",
            self.end_time,
            ",".join([str(prj) for prj in self.projects.all()])
        )

    def override(self, user):
        if not user:
            return False

        if user.has_perm("app.can_override_queueperiod"):
            return True

    def delay(self, dto=timezone.now()):
        if self.start_time <= self.end_time:
            if not (self.start_time <= dto.time() <= self.end_time):
                # wrong time of day
                return False

        if self.start_time >= self.end_time:
            if (self.start_time >= dto.time() >= self.end_time):
                # wrong time of day
                return False

        if self.start_date and (dto.date() < self.start_date):
            # not started yet
            return False

        if self.end_date and (dto.date() > self.end_date):
            # already ended
            return False

        return True


class RelayTarget(models.Model):
    active = models.BooleanField(
        default=True,
        help_text="Whether this relay will fire on matching events",
    )
    name = models.CharField(
        max_length=50,
        help_text="Friendly name of recipient, for example: Organization name",
    )
    url = models.CharField(
        max_length=200,
        help_text="HTTP(S) endpoint which will receive POST of GIT events "
                  "(for example http://webhook.example.com/webhook/)",
    )
    verify_SSL = models.BooleanField(
        default=True,
        help_text="Turn on SSL certificate verification",
    )
    sources = models.ManyToManyField(
        VCSNameSpace,
        help_text="List of VCS namespaces "
                  "(for example github organization or gitlab groups)",
    )

    def __unicode__(self):
        return "%s webhook relay" % self.name
