# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-17 19:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0033_add_survey_question_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyanswer',
            name='options',
            field=models.ManyToManyField(blank=True, related_name='answers', to='surveys.SurveyQuestionOption'),
        ),
    ]
