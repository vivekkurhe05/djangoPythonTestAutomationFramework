# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-23 11:57
from __future__ import unicode_literals

from django.db import migrations


def copy_answer_documents(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    SurveyAnswer = apps.get_model('surveys', 'SurveyAnswer')
    SurveyAnswerDocument = apps.get_model('surveys', 'SurveyAnswerDocument')

    answers = SurveyAnswer.objects.exclude(document='', document__isnull=False)
    for answer in answers:
        document = Document.objects.create(
            organisation=answer.response.organisation,
            name=answer.document.name.split('/')[-1],
            file=answer.document,
        )
        SurveyAnswerDocument.objects.create(
            answer=answer,
            document=document,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0038_answer_document_related_names'),
        ('documents', '0006_remove_question_document'),
    ]

    operations = [
        migrations.RunPython(copy_answer_documents, migrations.RunPython.noop),
    ]