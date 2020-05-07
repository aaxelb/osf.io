# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-14 14:32
from __future__ import unicode_literals

from django.db import migrations


def update_metaschema_active(*args, **kwargs):
    MetaSchema = args[0].get_model("osf", "metaschema")
    MetaSchema.objects.filter(schema_version__lt=2).update(active=False)


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0054_add_file_version_indices"),
    ]

    operations = [
        migrations.RunPython(update_metaschema_active,),
    ]
