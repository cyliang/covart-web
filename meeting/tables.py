import django_tables2 as tables
from django_tables2 import A
from django.urls import reverse
from . import models

type_tr = dict(models.PresentHistory.type_choices)

class ScheduleTable(tables.Table):
    date = tables.DateColumn(verbose_name='Scheduled Date', short=False)
    present_type = tables.Column(verbose_name='Type', empty_values=())
    presenter = tables.Column(verbose_name='Presenter')

    class Meta:
        orderable = False
        attrs = {'class': 'ts table'}
        row_attrs = {
            'class': lambda record: 'disabled' if 'postponed' in record
                else 'indicated ' + (
                    'info' if record['present_type'] == models.PresentHistory.PAPER_PRESENTATION
                    else 'negative'
                )
        }


    def render_present_type(self, value, record):
        return type_tr[value] if value else 'Postponed (%s)' % record['postponed']


class HistoryTable(tables.Table):
    date = tables.DateColumn(short=False)
    present_type = tables.Column(verbose_name='Type', accessor='presentation_type')
    presenter = tables.Column(accessor='presenter_name')
    content = tables.Column(accessor='present_content')

    class Meta:
        orderable = False
        attrs = {'class': 'ts selectable fixed single line table'}
        row_attrs = {
            'class': lambda record: 'disabled' if 'Postponed' in record['presentation_type']
                else ('clickable indicated ' + (
                    'info' if record['presentation_type'] == models.PresentHistory.PAPER_PRESENTATION
                    else 'negative'
                )
            ),
            'onclick': lambda record: "window.location='%s';" % reverse(
                'meeting:detail', args=[record['date']]
            ) if 'Postponed' not in record['presentation_type'] else '',
        }

    def render_present_type(self, value, record):
        if 'Postponed' not in value:
            value = type_tr[value]
        return value


class MemberPresentHistoryTable(tables.Table):
    class Meta:
        model = models.PresentHistory
        fields = ['meeting.date', 'present_type', 'content']
        attrs = {'class': 'ts selectable fixed single line table'}
        row_attrs = {
            'class': lambda record: 'clickable indicated ' + (
                'info' if record.present_type == record.PAPER_PRESENTATION
                else 'negative'
            ),
            'onclick': lambda record: "window.location='%s';" % record.meeting.get_absolute_url(),
        }
