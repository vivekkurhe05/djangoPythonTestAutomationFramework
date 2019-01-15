# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-01 13:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0035_remove_user_location'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisation',
            name='registration_authority',
        ),
        migrations.AddField(
            model_name='organisation',
            name='acronym',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='organisation',
            name='annual_expenditure',
            field=models.CharField(blank=True, choices=[('0-20K', 'USD < 20K'), ('20K-100K', 'USD 20K - 100K'), ('100K-500K', 'USD 100K - 500K'), ('500K-5M', 'USD 500K - 5M'), ('5M-100M', 'USD 5M - 100M'), ('100M+', 'USD >100M')], default='', max_length=30, verbose_name='Annual Expenditure'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='biography',
            field=models.TextField(blank=True, default='', verbose_name='Biography'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='iati_uid',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='IATI UID'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='landmark',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='organisation',
            name='other_social_media',
            field=models.URLField(blank=True, default='', max_length=100, verbose_name='Other social media'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='po_box',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='PO Box'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='size',
            field=models.CharField(blank=True, choices=[('0-10', '0 - 10'), ('11-50', '11 - 50'), ('51-250', '51 - 250'), ('250+', '250+')], default='', max_length=30, verbose_name='Size'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='social_media',
            field=models.URLField(blank=True, default='', max_length=100, verbose_name='Social Media'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='supporting_file',
            field=models.FileField(blank=True, default='', max_length=255, upload_to='registration/supporting', verbose_name='Registration supporting file'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='city',
            field=models.CharField(default='', max_length=100, verbose_name='City / Town'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='known_as',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Organization name'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='legal_name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Organization / Legal entity'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='parent_organisation',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Parent / umbrella organization'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='province',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='County/Province/District/State'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='type',
            field=models.CharField(choices=[('academic_training_and_research', 'Academic, Training and Research'), ('charitable', 'Charitable'), ('community_based', 'Community Based'), ('community_societal', 'Community Societal'), ('foundation', 'Foundation'), ('government', 'Government'), ('international_ngo', 'International NGO'), ('multilateral', 'Multilateral'), ('national_ngo', 'National NGO'), ('other_public_sector', 'Other Public Sector'), ('private_sector', 'Private Sector'), ('public_private_partnership', 'Public Private Partnership'), ('regional_ngo', 'Regional NGO'), ('other', 'Other')], max_length=255, verbose_name='Type of organization'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='zip',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Postal code / ZIP'),
        ),
    ]
