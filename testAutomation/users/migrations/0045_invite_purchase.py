# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-07-12 17:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0006_subscription_field'),
        ('users', '0044_add_terms_privacy_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='purchase',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='subscriptions.AssessmentPurchase'),
        ),
    ]
