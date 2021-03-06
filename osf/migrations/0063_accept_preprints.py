# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-27 19:13
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import F

from reviews.workflow import States


# When a preprint provider is set up with a reviews/moderation workflow,
# make sure all existing preprints will be in a public state.
def accept_all_published_preprints(apps, schema_editor):
    Preprint = apps.get_model('osf', 'PreprintService')
    published_preprints = Preprint.objects.filter(is_published=True, reviews_state=States.INITIAL.value)
    published_preprints.update(reviews_state=States.ACCEPTED.value, date_last_transitioned=F('date_published'))


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0062_auto_20171004_1506'),
    ]

    operations = [
        migrations.RunPython(
            accept_all_published_preprints
        ),
    ]
