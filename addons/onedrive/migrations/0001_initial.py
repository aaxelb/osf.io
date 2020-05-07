# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-21 16:50
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import osf.models.base
import osf.utils.datetime_aware_jsonfield


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("osf", "0067_auto_20171121_1050"),
    ]

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
                ("folder_id", models.TextField(blank=True, null=True)),
                ("folder_path", models.TextField(blank=True, null=True)),
                (
                    "external_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addons_onedrive_node_settings",
                        to="osf.ExternalAccount",
                    ),
                ),
                (
                    "owner",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addons_onedrive_node_settings",
                        to="osf.AbstractNode",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
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
                (
                    "oauth_grants",
                    osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONField(
                        blank=True,
                        default=dict,
                        encoder=osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONEncoder,
                    ),
                ),
                (
                    "owner",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addons_onedrive_user_settings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.AddField(
            model_name="nodesettings",
            name="user_settings",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="addons_onedrive.UserSettings",
            ),
        ),
    ]
