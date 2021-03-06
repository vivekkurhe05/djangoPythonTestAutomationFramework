# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-26 08:55
from __future__ import unicode_literals

import django.contrib.postgres.fields.citext
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_merge_20180326_0732'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userinvitation',
            name='organisation',
        ),
        migrations.RemoveField(
            model_name='userinvitation',
            name='survey',
        ),
        migrations.AddField(
            model_name='invitation',
            name='grantee_email',
            field=django.contrib.postgres.fields.citext.CIEmailField(max_length=511, null=True, verbose_name='Email address'),
        ),
        migrations.AlterField(
            model_name='invitation',
            name='grantee',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grantee', to='users.Organisation'),
        ),
        migrations.AlterField(
            model_name='invitation',
            name='status',
            field=models.IntegerField(choices=[(1, 'Awaiting Acceptance'), (2, 'Pending Submission'), (3, 'Submitted')], default=1),
        ),
        migrations.DeleteModel(
            name='UserInvitation',
        ),
    ]
