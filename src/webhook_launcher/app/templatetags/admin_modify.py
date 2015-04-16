from django import template
from django.forms.models import model_to_dict
from django.contrib.admin.templatetags.admin_modify import *
from webhook_launcher.app.models import WebHookMapping, RelayTarget

@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def submit_row(context):
    """
    Displays the row of buttons for delete and save.
    """
    prefill = ""
    original = context.get('original')
    show_trigger_build = False
    show_trigger_relay = False
    if original and isinstance(original, WebHookMapping):
        show_trigger_build = True
        prefill = "?"
        data = model_to_dict(original, fields=[], exclude=[])
        for key, value in data.items():
            if value == False:
                value=""
            prefill += "%s=%s&" % (key, value)
        if original.revision:
            prefill += "revision=%s" % (original.revision)
    elif original and isinstance(original, RelayTarget):
        show_trigger_relay = True

    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    return {
        'onclick_attrib': (opts.get_all_related_objects() and change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and change and context.get('show_delete', True)),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and
                            not is_popup and (not save_as or context['add']),
        'show_trigger_build': show_trigger_build,
        'show_trigger_relay': show_trigger_relay,
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'opts': opts,
        'prefill': prefill,
    }
