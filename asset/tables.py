# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_tables2 as tables
from . import models

class AssetTable(tables.Table):
    date = tables.DateColumn(format='Y-m-d')
    current_user = tables.Column('目前使用人', accessor='latest_log.new_user', orderable=False)

    class Meta:
        model = models.Asset
        attrs = {'class': 'ts selectable fixed single line table'}
        fields = ('label', 'name', 'date', 'years', 'custodian', 'description', 'remark', 'current_user')
