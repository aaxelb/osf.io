# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-20 18:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0041_auto_20170706_1024"),
    ]

    operations = [
        migrations.AddField(
            model_name="preprintprovider",
            name="share_title",
            field=models.TextField(blank=True, default=b""),
        ),
    ]
