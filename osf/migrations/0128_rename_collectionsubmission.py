# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-24 18:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0127_merge_20180822_1927"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="CollectedGuidMetadata", new_name="CollectionSubmission",
        ),
        migrations.AlterField(
            model_name="collectionsubmission",
            name="subjects",
            field=models.ManyToManyField(
                blank=True, related_name="collectionsubmissions", to="osf.Subject"
            ),
        ),
    ]
