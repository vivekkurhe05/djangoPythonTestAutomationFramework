# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-11 11:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='language',
            field=models.CharField(choices=[('en-gb', 'English')], default='en-gb', max_length=10, verbose_name='language'),
        ),
    ]