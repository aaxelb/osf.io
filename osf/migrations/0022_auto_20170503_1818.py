# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-03 23:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0021_unique_notificationsettings__ids"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationsubscription",
            name="_id",
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
    ]
