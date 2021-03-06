# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-10 18:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('website', '0011_publication_members'),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Ex: xxxxxxxxxx-yyyyy', max_length=100, unique=True, verbose_name='\u7522\u6a19\u7de8\u865f')),
                ('name', models.CharField(help_text='Ex: \u884c\u52d5\u96fb\u8a71\u6a5f', max_length=100, verbose_name='\u7269\u54c1\u985e\u5225')),
                ('date', models.DateField(verbose_name='\u7522\u6a19\u65e5\u671f')),
                ('years', models.SmallIntegerField(verbose_name='\u5e74\u9650')),
                ('custodian', models.CharField(help_text='Ex: \u5f90\u6170\u4e2d', max_length=50, verbose_name='\u4fdd\u7ba1\u4eba')),
                ('description', models.CharField(help_text='Ex: iPhone 6 plus', max_length=100, verbose_name='\u63cf\u8ff0')),
                ('remark', models.TextField(blank=True, help_text='Ex: \u5bc6\u78bc\u662fxxxx', verbose_name='\u5099\u8a3b')),
            ],
            options={
                'verbose_name': '\u8ca1\u7522',
                'verbose_name_plural': '\u8ca1\u7522',
            },
        ),
        migrations.CreateModel(
            name='TransferLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('BUY', '\u8cfc\u5165'), ('TRANSFER', '\u8f49\u79fb/\u53d6\u7528'), ('RETURN', '\u6b78\u9084'), ('SCRAP', '\u5831\u5ee2')], max_length=20)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('location', models.CharField(blank=True, help_text='Ex: \u5ea7\u4f4d', max_length=255)),
                ('remark', models.CharField(blank=True, help_text='\u7269\u54c1\u72c0\u614b(\u58de\u4e86?)\u3001\u7528\u9014\u8aaa\u660e', max_length=255)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.Asset')),
                ('new_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='website.Member')),
            ],
            options={
                'ordering': ['-time'],
                'get_latest_by': 'time',
            },
        ),
        migrations.AlterUniqueTogether(
            name='transferlog',
            unique_together=set([('asset', 'time')]),
        ),
    ]
