import django_tables2 as tables
from django_tables2 import A
from django.urls import reverse
from . import models

class ScheduleTable(tables.Table):
    date = tables.DateColumn(verbose_name='Scheduled Date')
    present_type = tables.Column(verbose_name='Type', empty_values=())
    presenter = tables.Column(verbose_name='Presenter')

    class Meta:
        orderable = False
        attrs = {'class': 'ts table'}
        row_attrs = {
            'class': lambda record: 'disabled' if 'postponed' in record
                else 'indicated ' + (
                    'info' if record['present_type'] == models.MeetingHistory.type_choices[0][1]
                    else 'negative'
                )
        }

    def render_present_type(self, value, record):
        return value if value else 'Postponed (%s)' % record['postponed']


class HistoryTable(tables.Table):
    date = tables.DateColumn()
    present_type = tables.Column(verbose_name='Type')
    presenter = tables.Column(accessor='presenter_name')
    content = tables.Column(accessor='present_content')

    class Meta:
        orderable = False
        attrs = {'class': 'ts selectable fixed single line table'}
        row_attrs = {
            'class': lambda record: 'disabled' if 'Postponed' in record['present_type']
                else ('clickable indicated ' + (
                    'info' if record['present_type'] == models.MeetingHistory.type_choices[0][0]
                    else 'negative'
                )
            ),
            'onclick': lambda record: "window.location='%s';" % reverse(
                'meeting:detail', args=[record['date']]
            ) if 'Postponed' not in record['present_type'] else '',
        }

    type_tr = dict(models.MeetingHistory.type_choices)

    def render_present_type(self, value, record):
        if 'Postponed' not in value:
            value = self.type_tr[value]
        return value
