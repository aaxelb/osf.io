# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-01 21:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("osf", "0121_merge_20180801_1458"),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name="basefilenode",
            index_together=set([("target_content_type", "target_object_id")]),
        ),
    ]
