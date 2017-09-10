# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, Http404
from django.views.generic import DetailView, CreateView
from django.db.models import Sum, Case, When, BooleanField
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
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


class AssetLoggingMixin(object):
    asset_url_kwarg = 'asset'

    def get_asset(self):
        return get_object_or_404(
            models.Asset,
            label=self.kwargs[self.asset_url_kwarg],
        )

    def dispatch(self, request, *args, **kwargs):
        self.asset = self.get_asset()
        if self.asset.latest_log.status == models.TransferLog.SCRAP:
            raise Http404('This is not a mutable asset.')

        return super(AssetLoggingMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AssetLoggingMixin, self).get_context_data(**kwargs)
        context['asset'] = self.asset
        return context

    def get_success_url(self):
        return self.asset.get_absolute_url()


class LogTransferFormView(LoginRequiredMixin, AssetLoggingMixin, CreateView):
    model = models.TransferLog
    fields = ('location', 'remark')
    template_name = 'asset/member_transfer.html'

    def get_form_kwargs(self):
        kwargs = super(LogTransferFormView, self).get_form_kwargs()

        if self.asset.latest_log.new_user != self.request.user.member:
            kwargs['instance'] = self.model(
                status=models.TransferLog.TRANSFER,
                asset=self.asset,
                new_user=self.request.user.member,
            )
        else:
            kwargs['instance'] = self.model(
                status=models.TransferLog.RETURN,
                asset=self.asset,
                new_user=None,
            )

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LogTransferFormView, self).get_context_data(**kwargs)
        context['action'] = ['take', 'return'][self.asset.latest_log.new_user == self.request.user.member]
        return context
