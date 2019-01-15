# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-21 10:00
from __future__ import unicode_literals

import django.contrib.postgres.fields.citext
from django.contrib.postgres.operations import CITextExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_type'),
    ]

    operations = [
        CITextExtension(),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=django.contrib.postgres.fields.citext.CIEmailField(max_length=511, unique=True, verbose_name='Email address'),
        ),
    ]
