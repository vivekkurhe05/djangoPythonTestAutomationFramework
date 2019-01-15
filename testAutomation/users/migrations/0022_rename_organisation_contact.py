# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-07 10:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_merge_user_organisation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organisation',
            old_name='organisation_contact',
            new_name='phone_number',
        ),
        migrations.AlterField(
            model_name='organisation',
            name='organisation_name',
            field=models.CharField(default='', max_length=100, unique=True),
        ),
    ]