# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-15 21:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("addons_wiki", "0010_migrate_node_wiki_pages"),
    ]

    operations = [
        migrations.RemoveField(model_name="nodewikipage", name="node",),
        migrations.RemoveField(model_name="nodewikipage", name="user",),
        migrations.DeleteModel(name="NodeWikiPage",),
    ]
