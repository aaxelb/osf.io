# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-19 18:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0016_preprintprovider_domain_redirect_enabled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="preprintprovider",
            name="domain",
            field=models.URLField(blank=True, default=b"", null=True),
        ),
    ]
