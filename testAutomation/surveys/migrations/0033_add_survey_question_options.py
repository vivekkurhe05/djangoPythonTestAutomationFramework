# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-16 12:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0032_question_name_richtext'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyQuestionOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='surveys.SurveyQuestion')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
        ),
        migrations.AddField(
            model_name='surveyanswer',
            name='options',
            field=models.ManyToManyField(blank=True, null=True, related_name='answers', to='surveys.SurveyQuestionOption'),
        ),
        migrations.AlterUniqueTogether(
            name='surveyquestionoption',
            unique_together=set([('question', 'name')]),
        ),
    ]
