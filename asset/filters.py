# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_filters as filters
from . import models

class AssetTableFilter(filters.FilterSet):
    scrapped_choice = (
        (False, '未報廢'),
    )

    scrapped = filters.ChoiceFilter(label='篩選', choices=scrapped_choice, empty_label='全部')

    class Meta:
        model = models.Asset
        fields = ('scrapped', )


    def __init__(self, data, **kwargs):
        if not data:
            data = {'scrapped': 'False'}

        super(AssetTableFilter, self).__init__(data=data, **kwargs)
