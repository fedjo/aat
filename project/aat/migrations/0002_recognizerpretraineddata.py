# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-13 23:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecognizerPreTrainedData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('recognizer', models.CharField(max_length=50)),
                ('yml_file', models.FileField(upload_to='recognizer_train_data/')),
            ],
        ),
    ]
