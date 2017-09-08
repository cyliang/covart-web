# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-30 13:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0009_hidden_publications'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(help_text='Ex: Awards and Honors', max_length=255)),
                ('title', models.CharField(help_text='Ex: Best Teaching Award', max_length=255)),
                ('year', models.IntegerField(help_text='Ex: 2017')),
                ('meta', models.TextField(blank=True, help_text='Ex: National Chiao-Tung University')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.Member')),
            ],
            options={
                'ordering': ['category', '-year'],
            },
        ),
        migrations.AlterField(
            model_name='publication',
            name='authors',
            field=models.CharField(help_text='Comma-separated. Ex: Chih-Chen Kao, Wei-Chung Hsu', max_length=255),
        ),
        migrations.AlterField(
            model_name='publication',
            name='hidden',
            field=models.BooleanField(default=False, help_text='Check this if the paper is not that important.'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='slug',
            field=models.SlugField(help_text='This is generated automatically.'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='venue',
            field=models.CharField(help_text='Ex: VEE', max_length=255),
        ),
        migrations.AlterField(
            model_name='publication',
            name='year',
            field=models.IntegerField(help_text='Ex: 2017'),
        ),
    ]