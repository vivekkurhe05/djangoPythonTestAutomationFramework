# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-10 13:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0005_create_blank_responses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyresponse',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
