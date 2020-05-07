# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-12 17:18
from __future__ import unicode_literals

import logging

from django.db import migrations

from osf.management.commands.migrate_pagecounter_data import FORWARD_SQL, REVERSE_SQL
from website.settings import DEBUG_MODE

logger = logging.getLogger(__name__)


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0175_pagecounter_schema"),
    ]

    if DEBUG_MODE:
        operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
    else:
        operations = []
        logger.info(
            "The automatic migration only runs in DEBUG_MODE. Use management command migrate_pagecount_data instead"
        )
