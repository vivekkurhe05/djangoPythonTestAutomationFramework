# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-23 07:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0037_copy_question_documents'),
        ('documents', '0005_document_attach_project'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questiondocument',
            name='answer',
        ),
        migrations.RemoveField(
            model_name='questiondocument',
            name='document',
        ),
        migrations.DeleteModel(
            name='QuestionDocument',
        ),
    ]
