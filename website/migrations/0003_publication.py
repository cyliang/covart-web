# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-19 09:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_activity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authors', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField()),
                ('date', models.DateField()),
                ('at', models.CharField(max_length=255)),
                ('index', models.CharField(blank=True, max_length=255)),
                ('best_paper', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
