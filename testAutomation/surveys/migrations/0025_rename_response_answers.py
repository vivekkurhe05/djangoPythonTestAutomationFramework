# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-14 20:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0024_copy_survey_answers'),
    ]

    operations = [
        migrations.RenameField(
            model_name='surveyresponse',
            old_name='answers',
            new_name='answers_old',
        ),
        migrations.AlterField(
            model_name='surveyanswer',
            name='response',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='surveys.SurveyResponse'),
        ),
    ]
