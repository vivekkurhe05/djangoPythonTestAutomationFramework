# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-01 13:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('admin', 'Admin/Secretariat'), ('auditor', 'Auditor'), ('grantee', 'Grantee'), ('grantor', 'Grantor')], default='grantee', max_length=255),
        ),
    ]
