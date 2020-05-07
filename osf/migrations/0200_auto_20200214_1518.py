# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-02-14 15:18
from __future__ import unicode_literals

from django.db import migrations, models
import osf.models.validators


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0199_draft_node_permissions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="draftregistration",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("analysis", "Analysis"),
                    ("communication", "Communication"),
                    ("data", "Data"),
                    ("hypothesis", "Hypothesis"),
                    ("instrumentation", "Instrumentation"),
                    ("methods and measures", "Methods and Measures"),
                    ("procedure", "Procedure"),
                    ("project", "Project"),
                    ("software", "Software"),
                    ("other", "Other"),
                    ("", "Uncategorized"),
                ],
                default="",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="draftregistration",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="draftregistration",
            name="title",
            field=models.TextField(
                blank=True,
                default="",
                validators=[osf.models.validators.validate_title],
            ),
        ),
    ]
