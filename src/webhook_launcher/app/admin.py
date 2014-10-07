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

import operator
from django.http import HttpResponseRedirect
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin, messages
from django.forms import TextInput
from django.core.urlresolvers import reverse
from django.conf import settings

from webhook_launcher.app.models import ( LastSeenRevision, WebHookMapping, 
                                          BuildService, Project, VCSService,
                                          VCSNameSpace, QueuePeriod,
                                          RelayTarget, get_or_none )

class LastSeenRevisionInline(admin.StackedInline):
    model = LastSeenRevision 
    extra = 1
    max_num = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "revision":
            if "request" in kwargs:
                revision = kwargs["request"].GET.get("revision")
                if revision:
                    kwargs['initial'] = revision

        return super(LastSeenRevisionInline, self).formfield_for_dbfield(db_field, **kwargs)

class WebHookMappingAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("extra.css",)
        }

    list_display = ( 'repourl', 'branch', 'project', 'package', 'notify', 'build', 'user')
    list_display_links = ( 'repourl', )
    list_filter = ( 'project', 'user', 'notify', 'build' )
    search_fields = ( 'user__username', 'user__email', 'repourl', 'project', 'package' )
    inlines = [LastSeenRevisionInline]
    actions = ['trigger_build']
    formfield_overrides = { models.CharField: {'widget' : TextInput(attrs={ 'size' : '100' })}, }
    save_on_top = True

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def response_change(self, request, obj):
        if "_triggerbuild" in request.POST:
            opts = obj._meta
            module_name = opts.module_name
            pk_value = obj._get_pk_val()

            self.trigger_build(request, [obj])
            return HttpResponseRedirect(reverse('admin:%s_%s_change' %
                                        (opts.app_label, module_name),
                                        args=(pk_value,),
                                        current_app=self.admin_site.name))
        else:
            return super(WebHookMappingAdmin, self).response_change(request, obj)

    def trigger_build(self, request, mappings):
        for mapobj in mappings:

            lsr = mapobj.lsr
            if not lsr:
                lsr, created = LastSeenRevision.objects.get_or_create(mapping=mapobj)

            to_build = mapobj.tag
            if not to_build:
                to_build = mapobj.rev_or_head

            mapobj.handle_tag(lsr, request.user.username, {}, to_build, webuser=request.user)
            msg = 'Build triggered for %(rev)s @ "%(obj)s" .' % {'obj': mapobj, 'rev': mapobj.rev_or_head}
            self.message_user(request, msg)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
            kwargs['initial'] = request.user.id
        if db_field.name == "obs":
            bss = BuildService.objects.all()
            if bss.count():
                kwargs['initial'] = bss[0]
        return super(WebHookMappingAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        mapping = WebHookMapping.objects.get(pk__exact = object_id)
        if mapping.comment:
            messages.warning(request, mapping.comment)
        return super(WebHookMappingAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)

class BuildServiceAdmin(admin.ModelAdmin):
    pass

class LastSeenRevisionAdmin(admin.ModelAdmin):
    readonly_fields = ("timestamp",)

class ProjectAdmin(admin.ModelAdmin):
    filter_horizontal = ("groups", "vcsnamespaces",)

class QueuePeriodAdmin(admin.ModelAdmin):
    pass

class RelayTargetAdmin(admin.ModelAdmin):

    def trigger_relay(self, request, relaytargets):
        payloads = []
        for rt in relaytargets:
            urls=set([str(src) for src in rt.sources])
            mapobjs = WebHookMapping.objects.filter(reduce(operator.or_,
                                                (models.Q(repourl__contains=u)
                                                 for u in urls)))
            for mapobj in mapobjs:
                lsr = mapobj.lsr
                if lsr and lsr.payload:
                    payloads.append(Payload(lsr.payload))

        for pld in payloads:
            pld.relay(relays=relaytargets)

    def response_change(self, request, obj):
        if "_triggerrelay" in request.POST:
            opts = obj._meta
            module_name = opts.module_name
            pk_value = obj._get_pk_val()

            self.trigger_relay(request, [obj])
            return HttpResponseRedirect(reverse('admin:%s_%s_change' %
                                        (opts.app_label, module_name),
                                        args=(pk_value,),
                                        current_app=self.admin_site.name))
        else:
            return super(RelayTargetAdmin, self).response_change(request, obj)

admin.site.register(WebHookMapping, WebHookMappingAdmin)
admin.site.register(BuildService, BuildServiceAdmin)
admin.site.register(LastSeenRevision, LastSeenRevisionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(VCSNameSpace)
admin.site.register(VCSService)
admin.site.register(QueuePeriod, QueuePeriodAdmin)
admin.site.register(RelayTarget, RelayTargetAdmin)
