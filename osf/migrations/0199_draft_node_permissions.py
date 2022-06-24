# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-14 19:04
from __future__ import unicode_literals
import logging
from django.db import migrations
from django.core.management.sql import emit_post_migrate_signal

from osf.migrations.sql.draft_nodes_migration import (
    add_draft_read_write_admin_auth_groups,
    remove_draft_auth_groups,
    add_permissions_to_draft_registration_groups,
    drop_draft_reg_group_object_permission_table)

logger = logging.getLogger(__name__)


def post_migrate_signal(state, schema):
    # this is to make sure that the draft registration permissions created earlier exist!
    emit_post_migrate_signal(3, False, 'default')

class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0198_draft_node_models'),
    ]

    operations = [
        migrations.RunSQL(add_draft_read_write_admin_auth_groups, remove_draft_auth_groups),
        migrations.RunSQL(add_permissions_to_draft_registration_groups, drop_draft_reg_group_object_permission_table),
    ]
