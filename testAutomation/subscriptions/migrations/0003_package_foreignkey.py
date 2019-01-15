# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-27 06:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_order_subsription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentpackage',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='assessmentpurchase',
            name='package',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='subscriptions.AssessmentPackage'),
        ),
        migrations.AlterField(
            model_name='order',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]
