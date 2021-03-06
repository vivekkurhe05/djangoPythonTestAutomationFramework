# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-15 18:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_add_invitation_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='level',
            field=models.IntegerField(choices=[(1, 'Bronze'), (2, 'Silver'), (3, 'Gold'), (4, 'Platinum')], default=1),
        ),
        migrations.AddField(
            model_name='invitation',
            name='status',
            field=models.IntegerField(choices=[(1, 'awaiting_acceptance'), (2, 'pending_submission'), (3, 'submitted')], default=1),
        ),
    ]
