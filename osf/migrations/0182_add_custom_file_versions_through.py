# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-07 23:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0181_osfuser_contacted_deactivation"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseFileVersionsThrough",
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
                ("version_name", models.TextField(blank=True)),
                (
                    "basefilenode",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="osf.BaseFileNode",
                    ),
                ),
                (
                    "fileversion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="osf.FileVersion",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="basefileversionsthrough",
            unique_together=set([("basefilenode", "fileversion")]),
        ),
        migrations.AlterIndexTogether(
            name="basefileversionsthrough",
            index_together=set([("basefilenode", "fileversion")]),
        ),
    ]
