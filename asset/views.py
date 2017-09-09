# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView
from django.db.models import Sum, Case, When, BooleanField
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView
from django_filters.views import FilterMixin
from . import models, tables, filters


class AssetTableView(LoginRequiredMixin, FilterMixin, SingleTableView):
    model = models.Asset
    table_class = tables.AssetTable
    filterset_class = filters.AssetTableFilter
    template_name = 'asset/all.html'

    def get(self, *args, **kwargs):
        self.filterset = self.get_filterset(self.get_filterset_class())
        return super(AssetTableView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AssetTableView, self).get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context

    def get_queryset(self):
        return super(AssetTableView, self).get_queryset().annotate(
            scrapped=Sum(Case(
                When(transferlog__status=models.TransferLog.SCRAP, then=1),
                default=0,
                output_field=BooleanField()
            )),
        )

    def get_table_data(self):
        return self.filterset.qs


class AssetDetailView(LoginRequiredMixin, DetailView):
    model = models.Asset
    slug_field = 'label'
    template_name = 'asset/detail.html'
