# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-24 19:33
from __future__ import unicode_literals

import logging

from django.db import migrations
from osf.utils.migrations import ensure_licenses, remove_licenses


logger = logging.getLogger(__file__)


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0036_auto_20170605_1520"),
    ]

    operations = [
        migrations.RunPython(ensure_licenses, remove_licenses),
    ]
