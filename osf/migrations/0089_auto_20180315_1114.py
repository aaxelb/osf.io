# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-03-15 16:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0008_alter_user_username_max_length"),
        ("osf", "0088_post_migrate_collections"),
    ]

    operations = [
        migrations.CreateModel(
            name="CollectionGroupObjectPermission",
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
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="CollectionUserObjectPermission",
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
            ],
            options={"abstract": False,},
        ),
        migrations.AlterModelOptions(
            name="collection",
            options={
                "permissions": (
                    ("read_collection", "Read Collection"),
                    ("write_collection", "Write Collection"),
                    ("admin_collection", "Admin Collection"),
                )
            },
        ),
        migrations.AddField(
            model_name="collectionuserobjectpermission",
            name="content_object",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="osf.Collection"
            ),
        ),
        migrations.AddField(
            model_name="collectionuserobjectpermission",
            name="permission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="auth.Permission"
            ),
        ),
        migrations.AddField(
            model_name="collectionuserobjectpermission",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="collectiongroupobjectpermission",
            name="content_object",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="osf.Collection"
            ),
        ),
        migrations.AddField(
            model_name="collectiongroupobjectpermission",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="auth.Group"
            ),
        ),
        migrations.AddField(
            model_name="collectiongroupobjectpermission",
            name="permission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="auth.Permission"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="collectionuserobjectpermission",
            unique_together=set([("user", "permission", "content_object")]),
        ),
        migrations.AlterUniqueTogether(
            name="collectiongroupobjectpermission",
            unique_together=set([("group", "permission", "content_object")]),
        ),
    ]
