# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-14 11:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import osf.models.base
import osf.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("osf", "0059_merge_20170914_1100"),
        ("guardian", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Action",
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
                (
                    "_id",
                    models.CharField(
                        db_index=True,
                        default=osf.models.base.generate_object_id,
                        max_length=24,
                        unique=True,
                    ),
                ),
                (
                    "trigger",
                    models.CharField(
                        choices=[
                            ("accept", "Accept"),
                            ("edit_comment", "Edit_Comment"),
                            ("reject", "Reject"),
                            ("submit", "Submit"),
                        ],
                        max_length=31,
                    ),
                ),
                (
                    "from_state",
                    models.CharField(
                        choices=[
                            ("accepted", "Accepted"),
                            ("initial", "Initial"),
                            ("pending", "Pending"),
                            ("rejected", "Rejected"),
                        ],
                        max_length=31,
                    ),
                ),
                (
                    "to_state",
                    models.CharField(
                        choices=[
                            ("accepted", "Accepted"),
                            ("initial", "Initial"),
                            ("pending", "Pending"),
                            ("rejected", "Rejected"),
                        ],
                        max_length=31,
                    ),
                ),
                ("comment", models.TextField(blank=True)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "date_created",
                    osf.utils.fields.NonNaiveDateTimeField(auto_now_add=True),
                ),
                (
                    "date_modified",
                    osf.utils.fields.NonNaiveDateTimeField(auto_now=True),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.AlterModelOptions(
            name="preprintprovider",
            options={
                "permissions": (
                    ("view_submissions", "Can view all submissions to this provider"),
                    (
                        "add_moderator",
                        "Can add other users as moderators for this provider",
                    ),
                    (
                        "view_actions",
                        "Can view actions on submissions to this provider",
                    ),
                    (
                        "add_reviewer",
                        "Can add other users as reviewers for this provider",
                    ),
                    (
                        "review_assigned_submissions",
                        "Can submit reviews for submissions to this provider which have been assigned to this user",
                    ),
                    (
                        "assign_reviewer",
                        "Can assign reviewers to review specific submissions to this provider",
                    ),
                    ("set_up_moderation", "Can set up moderation for this provider"),
                    (
                        "view_assigned_submissions",
                        "Can view submissions to this provider which have been assigned to this user",
                    ),
                    (
                        "edit_reviews_settings",
                        "Can edit reviews settings for this provider",
                    ),
                    ("accept_submissions", "Can accept submissions to this provider"),
                    ("reject_submissions", "Can reject submissions to this provider"),
                    (
                        "edit_review_comments",
                        "Can edit comments on actions for this provider",
                    ),
                    ("view_preprintprovider", "Can view preprint provider details"),
                )
            },
        ),
        migrations.AddField(
            model_name="preprintprovider",
            name="reviews_comments_anonymous",
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name="preprintprovider",
            name="reviews_comments_private",
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name="preprintprovider",
            name="reviews_workflow",
            field=models.CharField(
                blank=True,
                choices=[
                    (None, "None"),
                    ("pre-moderation", "Pre-Moderation"),
                    ("post-moderation", "Post-Moderation"),
                ],
                max_length=15,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="preprintservice",
            name="date_last_transitioned",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="preprintservice",
            name="reviews_state",
            field=models.CharField(
                choices=[
                    ("accepted", "Accepted"),
                    ("initial", "Initial"),
                    ("pending", "Pending"),
                    ("rejected", "Rejected"),
                ],
                db_index=True,
                default="initial",
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="action",
            name="target",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions",
                to="osf.PreprintService",
            ),
        ),
    ]
