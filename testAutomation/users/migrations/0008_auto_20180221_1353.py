# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-21 13:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20180221_1349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='biography',
            field=models.TextField(blank=True, default='', max_length=300),
        ),
        migrations.AlterField(
            model_name='user',
            name='contact',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
        migrations.AlterField(
            model_name='user',
            name='department_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='description',
            field=models.TextField(blank=True, default='', max_length=300),
        ),
        migrations.AlterField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='mobile',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='user',
            name='province',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='website',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]