# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-12 17:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # CREATE INDEX CONCURRENTLY cannot be run in a txn

    dependencies = [
        ("osf", "0176_pagecounter_data"),
    ]

    operations = [
        migrations.RunSQL(
            [
                "CREATE INDEX CONCURRENTLY page_counter_idx ON osf_pagecounter (action, resource_id, file_id, version);",
            ],
            ["DROP INDEX IF EXISTS page_counter_idx, RESTRICT;"],
        )
    ]
