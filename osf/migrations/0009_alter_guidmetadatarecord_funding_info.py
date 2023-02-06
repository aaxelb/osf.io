# Generated by Django 3.2.15 on 2023-01-27 15:54

from django.db import migrations, models
import osf.models.validators


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0008_guid_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guidmetadatarecord',
            name='funding_info',
            field=models.JSONField(blank=True, default=list, validators=[osf.models.validators.JsonschemaValidator({'items': {'additionalProperties': False, 'properties': {'award_number': {'type': 'string'}, 'award_title': {'type': 'string'}, 'award_uri': {'format': 'uri', 'type': 'string'}, 'funder_identifier': {'type': 'string'}, 'funder_identifier_type': {'enum': ['ISNI', 'GRID', 'Crossref Funder ID', 'ROR', 'Other'], 'type': 'string'}, 'funder_name': {'type': 'string'}}, 'required': ['funder_name'], 'type': 'object'}, 'type': 'array'})]),
        ),
    ]
