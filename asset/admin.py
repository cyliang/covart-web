# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models

@admin.register(models.Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('label', 'name', 'date', 'custodian', 'description')
    list_filter = ('name', 'date', 'custodian')
    search_fields = ('label', 'description', 'remark')

    def get_changeform_initial_data(self, request):
        from website.models import Member

        try:
            return {
                'custodian': Member.objects.get(identity=Member.ADVISOR),
            }
        except:
            return {}

    def save_model(self, request, obj, form, change):
        super(AssetAdmin, self).save_model(request, obj, form, change)

        if not change:
            obj.transferlog_set.create(status=models.TransferLog.BUY)


@admin.register(models.TransferLog)
class TransferLogAdmin(admin.ModelAdmin):
    list_display = ('asset', 'status', 'time', 'new_user', 'location')
    list_filter = ('time',)
    search_fields = ('asset__label',)
