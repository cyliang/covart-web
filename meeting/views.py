from django.shortcuts import redirect
from django.views.generic import DetailView, UpdateView
from django.urls import reverse
from django.db.models import ExpressionWrapper, CharField, Value as V, F, Max
from django.db.models.functions import Concat
from django.forms import widgets, modelformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView
from datetime import timedelta, date
from . import tables, models, forms

class ScheduleView(SingleTableView):
    """
    Show the upcoming scheduled meeting specially and other future scheduled
    meetings in a table.
    """
    table_class = tables.ScheduleTable
    template_name = 'meeting/schedule.html'

    def get_queryset(self):
        """
        Generate data (all future meetings) for the table.
        Since only the exact next meeting is in the database, other future
        meetings are calculated in the runtime.
        """
        next_meeting, prev_meeting = models.MeetingHistory.objects.all()[0:2]

        # Get next meeting
        result = [
            {
                'date': next_meeting.date,
                'present_type': presentation.present_type,
                'presenter': presentation.presenter,
            }
            for presentation in next_meeting.presenthistory_set.all()
        ]

        # Get other future meetings.
        date = next_meeting.date
        last_rotation = next_meeting.last_rotation
        counter = 0
        num_rotation = models.PresentRotation.objects.all().count()
        for i in range(num_rotation):
            next_rotation1 = last_rotation.get_after()
            last_rotation = next_rotation1.get_after()

            date = models.MeetingHistory.get_next_meeting_date(date)
            while models.MeetingSkip.objects.filter(date=date).exists():
                skip = models.MeetingSkip.objects.get(date=date)
                result += [{
                    'date': date,
                    'postponed': skip.reason,
                }]

                date = models.MeetingHistory.get_next_meeting_date(date)

            for r in (next_rotation1, last_rotation):
                past = r.presenter.presenthistory_set.filter(is_specially_arranged=False)
                if past.count() > 0:
                    present_type = getattr(
                        past[0],
                        'another_type' if counter < num_rotation else 'present_type'
                    )
                elif counter < num_rotation:
                    present_type = models.PresentHistory.DEFAULT_TYPE
                else:
                    present_type = models.PresentHistory(
                        present_type=models.PresentHistory.DEFAULT_TYPE
                    ).another_type

                result += [{
                    'date': date,
                    'presenter': r.presenter,
                    'present_type': present_type,
                }]
                counter += 1

        return result

    def get_context_data(self, **kwargs):
        """
        Append data specially for the upcoming meeting, which has information
        already stored in the database.
        """
        context = super(ScheduleView, self).get_context_data(**kwargs)

        context['upcoming'] = models.MeetingHistory.objects.all()[0]

        return context

class HistoryView(SingleTableView):
    table_class = tables.HistoryTable
    template_name = 'meeting/history.html'

    def get_queryset(self):
        empty_str = ExpressionWrapper(V(''), output_field=CharField())
        future_meeting = models.MeetingHistory.objects.latest('date')

        return models.PresentHistory.objects.values(
            date=F('meeting__date'),
            presentation_type=F('present_type'),
            presenter_name=F('presenter__name'),
            present_content=F('content'),
        ).exclude(meeting__date=future_meeting.date).order_by().union(
            models.MeetingSkip.objects.all().values(
                'date',
                presentation_type=Concat(V('Postponed: '), 'reason'),
                presenter_name=empty_str,
                present_content=empty_str,
            ).filter(date__lte=date.today()).order_by()
        ).order_by('-date')


class MeetingDetailView(DetailView):
    model = models.MeetingHistory
    template_name = 'meeting/detail.html'
    slug_field = 'date'


class AttendanceEditView(LoginRequiredMixin, MeetingDetailView):
    AttendanceFormSet = modelformset_factory(
        models.MeetingAttendance,
        fields=('meeting', 'member', 'status', 'reason'),
        widgets={
            'meeting': widgets.HiddenInput(),
            'reason': widgets.Textarea(attrs={'rows': 1}),
        },
        can_delete=True,
    )
    template_name = 'meeting/attendance_update.html'

    def get_formset(self):
        kwargs = {}
        if self.request.method == 'POST':
            kwargs = {
                'data': self.request.POST,
                'files': self.request.FILES,
            }

        return self.AttendanceFormSet(
            queryset=self.object.meetingattendance_set.all(),
            initial=[{
                'meeting': self.object,
            }],
            **kwargs
        )

    def formset_valid(self, formset):
        formset.save()
        return redirect(self.request.path)

    def formset_invalid(self, formset):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super(MeetingDetailView, self).get_context_data(**kwargs)
        context['formset'] = self.get_formset()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = self.get_formset()

        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)


class PresentUpdateView(UpdateView):
    model = models.PresentHistory
    form_class = forms.PresentUpdateForm
    template_name = 'meeting/content_update.html'

    def get_success_url(self):
        return self.object.meeting.get_absolute_url()
