# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-28 21:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import osf.models.base


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0164_add_guardian_to_nodes"),
    ]

    operations = [
        migrations.CreateModel(
            name="OSFGroup",
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
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("name", models.TextField()),
                (
                    "creator",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="osfgroups_created",
                        to=settings.AUTH_USER_MODEL,
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
            ],
            options={
                "permissions": (
                    ("view_group", "Can view group details"),
                    ("member_group", "Has group membership"),
                    ("manage_group", "Can manage group membership"),
                ),
            },
        ),
        migrations.CreateModel(
            name="OSFGroupGroupObjectPermission",
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
                    "content_object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="osf.OSFGroup"
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="auth.Group"
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.Permission",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="OSFGroupUserObjectPermission",
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
                    "content_object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="osf.OSFGroup"
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.Permission",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.AlterUniqueTogether(
            name="osfgroupgroupobjectpermission",
            unique_together=set([("group", "permission", "content_object")]),
        ),
        migrations.AlterUniqueTogether(
            name="osfgroupuserobjectpermission",
            unique_together=set([("user", "permission", "content_object")]),
        ),
        migrations.CreateModel(
            name="OSFGroupLog",
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
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
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
                ("action", models.CharField(db_index=True, max_length=255)),
                (
                    "params",
                    osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONField(
                        default=dict,
                        encoder=osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONEncoder,
                    ),
                ),
                ("should_hide", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-created"], "get_latest_by": "created",},
        ),
        migrations.AddField(
            model_name="osfgroup",
            name="last_logged",
            field=osf.utils.fields.NonNaiveDateTimeField(
                blank=True, db_index=True, default=django.utils.timezone.now, null=True
            ),
        ),
        migrations.AddField(
            model_name="osfgrouplog",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="logs",
                to="osf.OSFGroup",
            ),
        ),
        migrations.AddField(
            model_name="osfgrouplog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="group_logs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="osfuser",
            name="group_connected_email_records",
            field=osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONField(
                blank=True,
                default=dict,
                encoder=osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONEncoder,
            ),
        ),
        migrations.AddField(
            model_name="osfuser",
            name="member_added_email_records",
            field=osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONField(
                blank=True,
                default=dict,
                encoder=osf.utils.datetime_aware_jsonfield.DateTimeAwareJSONEncoder,
            ),
        ),
    ]
