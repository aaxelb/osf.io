# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-17 20:11
from __future__ import unicode_literals

from django.db import migrations


def noop(*args):
    # This migration used to add permissions,
    # which is now handled by the post_migrate signal
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0077_bannerimage_scheduledbanner"),
    ]

    operations = [
        migrations.RunPython(noop, noop),
    ]
