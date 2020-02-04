
from django.contrib.admin.templatetags.admin_modify import register
from django.contrib.admin.templatetags.admin_modify import \
    submit_row as original_submit_row
from django.forms.models import model_to_dict

from webhook_launcher.app.models import RelayTarget, WebHookMapping


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def submit_row(context):
    """
    Add some things in the submit row context
    """
    ctx = original_submit_row(context)
    prefill = ""
    original = context.get('original')
    show_trigger_build = False
    show_trigger_relay = False
    if original and isinstance(original, WebHookMapping):
        show_trigger_build = True
        prefill = "?"
        data = model_to_dict(original, fields=[], exclude=[])
        for key, value in data.items():
            if value is False:
                value = ""
            prefill += "%s=%s&" % (key, value)
        if original.revision:
            prefill += "revision=%s" % (original.revision)
    elif original and isinstance(original, RelayTarget):
        show_trigger_relay = True

    ctx.update({
        'show_trigger_build': show_trigger_build,
        'show_trigger_relay': show_trigger_relay,
        'prefill': prefill,
    })
    return ctx
