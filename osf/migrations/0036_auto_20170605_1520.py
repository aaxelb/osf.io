# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-05 20:20
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0035_metaschema_active"),
    ]

    operations = [
        migrations.RemoveField(model_name="preprintprovider", name="banner_name",),
        migrations.RemoveField(model_name="preprintprovider", name="header_text",),
        migrations.RemoveField(model_name="preprintprovider", name="logo_name",),
        migrations.AddField(
            model_name="preprintprovider",
            name="additional_providers",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="preprintprovider",
            name="allow_submissions",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="preprintprovider",
            name="footer_links",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="preprintprovider",
            name="advisory_board",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="preprintprovider",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
