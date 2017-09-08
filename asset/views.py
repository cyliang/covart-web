# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView
from . import models, tables


class AssetTableView(LoginRequiredMixin, SingleTableView):
    model = models.Asset
    table_class = tables.AssetTable
    template_name = 'asset/all.html'


class AssetDetailView(LoginRequiredMixin, DetailView):
    model = models.Asset
    slug_field = 'label'
    template_name = 'asset/detail.html'
