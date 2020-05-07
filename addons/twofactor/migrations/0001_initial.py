# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-23 20:34
from __future__ import unicode_literals

from django.db import migrations, models
import osf.models.base


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "_id",
                    models.CharField(
                        db_index=True,
                        default=osf.models.base.generate_object_id,
                        max_length=24,
                        unique=True,
                    ),
                ),
                ("deleted", models.BooleanField(default=False)),
                ("totp_secret", models.TextField(blank=True, null=True)),
                ("totp_drift", models.IntegerField()),
                ("is_confirmed", models.BooleanField(default=False)),
            ],
            options={"abstract": False,},
        ),
    ]
