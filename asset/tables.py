# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_tables2 as tables
from . import models

def asset_table_row_class(record):
    if record.scrapped:
        return 'negative'
    if not record.latest_log.new_user:
        return 'positive'
    return ''

class AssetTable(tables.Table):
    label = tables.LinkColumn()
    date = tables.DateColumn(format='Y-m-d')
    current_user = tables.Column('目前使用人', accessor='latest_log.new_user', orderable=False)

    class Meta:
        model = models.Asset
        fields = ('label', 'name', 'date', 'years', 'custodian', 'description', 'remark', 'current_user')
        attrs = {'class': 'ts selectable fixed single line table'}
        row_attrs = {
            'class': asset_table_row_class,
        }
