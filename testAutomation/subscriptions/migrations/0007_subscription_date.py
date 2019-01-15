# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-07-14 13:49
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import subscriptions.models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0006_subscription_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='end_date',
            field=models.DateField(default=subscriptions.models.get_end_date),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='start_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]