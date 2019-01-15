# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-07-24 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0008_subscription_values'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created']},
        ),
        migrations.AddField(
            model_name='order',
            name='paid_date',
            field=models.DateTimeField(editable=False, null=True),
        ),
    ]
