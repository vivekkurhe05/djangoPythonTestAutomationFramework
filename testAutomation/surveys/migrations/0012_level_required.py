# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-17 09:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0011_surveyresponse_invalid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyresponse',
            name='invited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invites', to=settings.AUTH_USER_MODEL, verbose_name='Grantor'),
        ),
        migrations.AlterField(
            model_name='surveyresponse',
            name='level',
            field=models.IntegerField(blank=True, choices=[(1, 'Bronze'), (2, 'Silver'), (3, 'Gold'), (4, 'Platinum')], default=1),
            preserve_default=False,
        ),
    ]