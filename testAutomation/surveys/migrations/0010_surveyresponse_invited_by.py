# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-02 13:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('surveys', '0009_surveyquestion_upload_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyresponse',
            name='invited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invites', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='surveyresponse',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to=settings.AUTH_USER_MODEL),
        ),
    ]