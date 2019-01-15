# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-21 10:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_add_users_to_organisations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='organisation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Organisation'),
        ),
    ]
