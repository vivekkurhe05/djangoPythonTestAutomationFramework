# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-01 14:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0040_remove_organisation_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganisationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, db_index=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
        ),
        migrations.AddField(
            model_name='organisation',
            name='types',
            field=models.ManyToManyField(to='users.OrganisationType', verbose_name='Type of organization'),
        ),
    ]
