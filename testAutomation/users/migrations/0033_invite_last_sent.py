# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-27 05:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_update_organisation_type_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='last_sent',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
