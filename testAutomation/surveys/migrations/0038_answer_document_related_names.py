# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-23 07:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0037_copy_question_documents'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyanswerdocument',
            name='answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='surveys.SurveyAnswer'),
        ),
        migrations.AlterField(
            model_name='surveyanswerdocument',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='questions', to='documents.Document'),
        ),
    ]
