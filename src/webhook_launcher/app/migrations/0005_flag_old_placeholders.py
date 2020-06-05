# -*- coding: utf-8 -*-


from functools import partial

from django.db import migrations


def flag_old_placeholders(apps, schema_editori, flag=True):
    WebHookMapping = apps.get_model('app', 'WebHookMapping')
    for whm in WebHookMapping.objects.filter(
        build=False,
        notify=False,
        user_id=1,
        placeholder=not flag,
    ):
        whm.placeholder = flag
        whm.save()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_webhookmapping_placeholder'),
    ]

    operations = [
        migrations.RunPython(
            # Forward
            flag_old_placeholders,
            # Backward
            partial(flag_old_placeholders, flag=False)
        ),
    ]
