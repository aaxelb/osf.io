# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-08-28 20:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0185_basefilenode_versions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pagecounter",
            name="action",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="pagecounter",
            name="file",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pagecounters",
                to="osf.BaseFileNode",
            ),
        ),
        migrations.AlterField(
            model_name="pagecounter",
            name="resource",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pagecounters",
                to="osf.Guid",
            ),
        ),
    ]
