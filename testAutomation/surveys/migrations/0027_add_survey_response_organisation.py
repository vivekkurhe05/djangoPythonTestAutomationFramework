# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-21 10:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_user_organisation_required'),
        ('surveys', '0026_additional_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyresponse',
            name='organisation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='users.Organisation'),
        )
    ]
