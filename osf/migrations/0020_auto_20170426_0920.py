# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-26 14:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0019_merge_20170424_1956"),
    ]

    operations = [
        migrations.AlterField(
            model_name="preprintprovider",
            name="domain",
            field=models.URLField(blank=True, default=b""),
        ),
    ]
