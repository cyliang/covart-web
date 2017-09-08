# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required, user_passes_test
from django_tables2 import SingleTableView
from . import models, tables


class AssetTableView(SingleTableView):
    model = models.Asset
    table_class = tables.AssetTable
    template_name = 'asset/all.html'
