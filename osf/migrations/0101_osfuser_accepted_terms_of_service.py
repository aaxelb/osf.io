# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-09 18:55
from __future__ import unicode_literals

from django.db import migrations
import osf.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0100_set_access_request_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="osfuser",
            name="accepted_terms_of_service",
            field=osf.utils.fields.NonNaiveDateTimeField(blank=True, null=True),
        ),
    ]
