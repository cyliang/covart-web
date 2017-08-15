from django.conf.urls import url
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    url(r'^schedule$', views.ScheduleView.as_view(), name='schedule'),
    url(r'^history$', views.HistoryView.as_view(), name='history'),
    url(r'^history/(?P<slug>\d{4}-\d{2}-\d{2})$', views.MeetingDetailView.as_view(), name='detail'),
    url(r'^history/(?P<pk>\d+)/update$', views.PresentUpdateView.as_view(), name='content-update'),
    url(r'^attendance/(?P<slug>\d{4}-\d{2}-\d{2})/update$', views.AttendanceEditView.as_view(), name='attendance-update'),
    url(r'^attendance/(?P<meeting>\d{4}-\d{2}-\d{2})/leave$', views.TakeLeaveView.as_view(), name='take-leave'),
    url(r'^$', RedirectView.as_view(pattern_name='meeting:schedule')),
]

app_name = 'meeting'
