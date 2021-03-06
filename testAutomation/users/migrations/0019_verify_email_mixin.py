# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-01 08:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_types_of_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False, help_text='Indicates if the email address has been verified.', verbose_name='Email verified?'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=False, verbose_name='active'),
        ),
    ]
