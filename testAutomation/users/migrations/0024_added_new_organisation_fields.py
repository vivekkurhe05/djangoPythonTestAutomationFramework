# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-12 14:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_removed_default_from_organisation_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisation',
            name='description',
        ),
        migrations.AddField(
            model_name='organisation',
            name='parent_organisation',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='organisation',
            name='registration_authority',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='organisation',
            name='registration_number',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='organisation',
            name='type',
            field=models.CharField(choices=[('non_government', 'Non Governmental'), ('international_non_governmental', 'International Non Governmental'), ('governmental', 'Governmental'), ('community_based', 'Community Based'), ('community_societal', 'Community Societal'), ('research_or_technology', 'Research / Technology'), ('charitable', 'Charitable'), ('foundation', 'Foundation'), ('other', 'Other')], default='charitable', max_length=255),
        ),
    ]
