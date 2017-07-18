from django.views.generic import DetailView
from django_tables2 import SingleTableView
from datetime import timedelta
from . import tables, models

class ScheduleView(SingleTableView):
    table_class = tables.ScheduleTable
    template_name = 'meeting/schedule.html'

    def get_queryset(self):
        next_meeting, prev_meeting = models.MeetingHistory.objects.all()[0:2]

        result = [
            {
                'date': p.meeting.date,
                'present_type': p.meeting.get_present_type_display(),
                'presenter': p.presenter
            }
            for p in models.PresentHistory.objects.filter(meeting=next_meeting)
        ]

        type1, type2 = [
            [m.get_present_type_display(), m.last_rotation]
            for m in (prev_meeting, next_meeting)
        ]
        date = next_meeting.date
        for i in range(5):
            for t in (type1, type2):
                next_rotation1 = t[1].get_after()
                next_rotation2 = next_rotation1.get_after()
                t[1] = next_rotation2

                date += timedelta(days=7)

                for r in (next_rotation1, next_rotation2):
                    result += [{
                        'date': date,
                        'present_type': t[0],
                        'presenter': r.presenter
                    }]

        return result

    def get_context_data(self, **kwargs):
        context = super(ScheduleView, self).get_context_data(**kwargs)

        meeting = models.MeetingHistory.objects.all()[0]
        context['upcoming'] = {
            'presentations': models.PresentHistory.objects.filter(meeting=meeting),
            'meeting': meeting,
        }
        return context

class HistoryView(SingleTableView):
    table_class = tables.HistoryTable
    template_name = 'meeting/history.html'

    def get_queryset(self):
        return models.PresentHistory.objects.order_by('meeting')[2:]


class MeetingDetailView(DetailView):
    model = models.MeetingHistory
    template_name = 'meeting/detail.html'
    slug_field = 'date'

    def get_context_data(self, **kwargs):
        context = super(MeetingDetailView, self).get_context_data(**kwargs)

        context['presentations'] = models.PresentHistory.objects.filter(
            meeting=self.object
        )

        return context
