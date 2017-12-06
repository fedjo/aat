# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-29 18:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aat', '0004_configuration_current'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recognizerpretraineddata',
            name='faces_path',
        ),
        migrations.AddField(
            model_name='recognizerpretraineddata',
            name='faces',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]