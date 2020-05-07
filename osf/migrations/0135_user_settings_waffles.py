# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-10-03 14:20
from __future__ import unicode_literals

from django.db import migrations

from osf import features
from osf.utils.migrations import AddWaffleFlags


USER_SETTINGS_FLAGS = [
    features.EMBER_USER_SETTINGS_ACCOUNTS,
    features.EMBER_USER_SETTINGS_ADDONS,
    features.EMBER_USER_SETTINGS_APPS,
    features.EMBER_USER_SETTINGS_NOTIFICATIONS,
    features.EMBER_USER_SETTINGS_TOKENS,
]


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0134_abstractnode_custom_citation"),
    ]

    operations = [
        AddWaffleFlags(USER_SETTINGS_FLAGS),
    ]
