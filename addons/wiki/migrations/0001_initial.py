# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-23 20:34
from __future__ import unicode_literals

import addons.wiki.models
import django.contrib.postgres.fields
from django.db import migrations, models
import django.utils.timezone
import osf.models.base
import osf.utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NodeSettings",
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
                (
                    "is_publicly_editable",
                    models.BooleanField(db_index=True, default=False),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="NodeWikiPage",
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
                    "guid_string",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            blank=True, max_length=255, null=True
                        ),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                ("content_type_pk", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "page_name",
                    models.CharField(
                        max_length=200,
                        validators=[addons.wiki.models.validate_page_name],
                    ),
                ),
                ("version", models.IntegerField(default=1)),
                (
                    "date",
                    osf.utils.fields.NonNaiveDateTimeField(
                        default=django.utils.timezone.now
                    ),
                ),
                ("content", models.TextField(blank=True, default="")),
            ],
            options={"abstract": False,},
        ),
    ]
