# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-24 09:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_publication_format'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('help_text', models.CharField(blank=True, max_length=255)),
                ('link', models.URLField()),
                ('update_time', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-update_time'],
            },
        ),
    ]