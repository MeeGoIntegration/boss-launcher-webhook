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

import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.contrib.auth.backends import RemoteUserBackend

class BuildService(models.Model):

    namespace = models.CharField(max_length=50, unique=True)
    apiurl = models.CharField(max_length=250, unique=True)

    def __unicode__(self):
        return self.apiurl

class WebHookMapping(models.Model):    

    def __unicode__(self):
        return "%s/%s -> %s/%s" % (self.repourl, self.branch, self.project, self.package)

    @property
    def revision(self):
        _lsr = self.lastseenrevision_set.all()
        if _lsr:
            return _lsr[0].revision

    def clean(self, exclude=None):
        self.repourl = self.repourl.strip()
        self.branch  = self.branch.strip()
        self.project = self.project.strip()
        self.package = self.package.strip()

        if WebHookMapping.objects.exclude(pk=self.pk).filter(project=self.project, package=self.package).count():
            raise ValidationError('A mapping object with the same parameters already exists')
        if settings.SERVICE_WHITELIST:
            service = urlparse.urlparse(self.repourl).netloc
            if service not in settings.SERVICE_WHITELIST:
                raise ValidationError('%s is not an allowed service' % service)

    def to_fields(self):
        fields = {}
        fields['repourl'] = self.repourl
        fields['branch'] = self.branch
        if self.project:
            fields['project'] = self.project
            fields['package'] =  self.package
            fields['ev'] = { 'namespace' : self.obs.namespace }
        if self.token:
            fields['token'] = self.token
        if self.debian:
            fields['debian'] = self.debian
        if self.dumb:
            fields['dumb'] = self.dumb
        return fields
        
    repourl = models.CharField(max_length=200, help_text="url of git repo to clone from. Should be a remote http[s]")
    branch = models.CharField(max_length=100, default="master", help_text="name of branch to use. If not specified default branch (or currently checked out one) will be used")
    project = models.CharField(max_length=250, default=settings.DEFAULT_PROJECT, help_text="name of an existing project under which to create or update the package")
    package = models.CharField(max_length=250, help_text="name of the package to create or update in OBS")
    token = models.CharField(max_length=100, default="", blank=True, help_text="a token that should exist in tag names and changelog entry headers to enable handling them")
    debian = models.CharField(max_length=2, default="", blank=True, choices = (('N','N'),('Y','Y')), help_text="Choose Y to turn on debian packaging support")
    dumb = models.CharField(max_length=2, default="", blank=True, choices = (('N','N'),('Y','Y')), help_text="Choose Y to take content of revision as-is without automatic processing (example: tarballs in git)")
    notify = models.BooleanField(default=True, help_text="Enable IRC notifications of events")
    build = models.BooleanField(default=False, help_text="Enable OBS build triggering")
    comment = models.TextField(blank=True, null=True, default="")
    user = models.ForeignKey(User)
    obs = models.ForeignKey(BuildService)

class LastSeenRevision(models.Model):

    def __unicode__(self):
        return "%s @ %s/%s" % ( self.revision, self.mapping.repourl, self.mapping.branch )

    mapping = models.ForeignKey(WebHookMapping)
    revision = models.CharField(max_length=250)

def default_perms(sender, **kwargs):
    if kwargs['created']:
        user = kwargs['instance']
        # Set the is_staff flag in a transaction-safe way, while
        # working around django_auth_ldap which saves unsafely.
        User.objects.filter(id=user.id).update(is_staff=True)
        user.is_staff = True
        try:
            user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_add_permission()))
            user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_change_permission()))
            user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_delete_permission()))
            user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_add_permission()))
            user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_change_permission()))
            user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_delete_permission()))
        except Permission.DoesNotExist:
            # we're probably creating the superuser during syncdb
            pass

class RemoteStaffBackend(RemoteUserBackend):

    def configure_user(self, user):

        user.is_staff = True
        user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_add_permission()))
        user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_change_permission()))
        user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_delete_permission()))
        user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_add_permission()))
        user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_change_permission()))
        user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_delete_permission()))
        return user

post_save.connect(default_perms, sender=User, weak=False,
                  dispatch_uid="default_perms")
