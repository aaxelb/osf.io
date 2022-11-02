# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-08-17 19:40
from __future__ import unicode_literals

from django.db import migrations
import osf.models.admin_log_entry


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0002_logentry_remove_auto_add'),
        ('osf', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminLogEntry',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('admin.logentry',),
            managers=[
                ('objects', osf.models.admin_log_entry.AdminLogEntryManager()),
            ],
        ),
    ]