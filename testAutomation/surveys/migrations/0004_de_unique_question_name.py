# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-08 10:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0003_larger_question_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyquestion',
            name='name',
            field=models.TextField(),
        ),
    ]
