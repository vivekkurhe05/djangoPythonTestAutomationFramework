# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-27 13:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0013_add_surveyresponse_submitted'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='surveyresponse',
            options={'ordering': ('created',)},
        ),
        migrations.RenameField('surveyresponse', 'date', 'created'),
        migrations.AlterField(
            model_name='surveyresponse',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]
