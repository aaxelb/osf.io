# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-15 19:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0150_fix_deleted_preprints"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="preprint",
            options={
                "permissions": (
                    ("view_preprint", "Can view preprint details in the admin app"),
                    ("read_preprint", "Can read the preprint"),
                    ("write_preprint", "Can write the preprint"),
                    ("admin_preprint", "Can manage the preprint"),
                )
            },
        ),
    ]
