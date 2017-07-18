from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView
from . import views

urlpatterns = [
    url(r'^schedule$', views.ScheduleView.as_view(), name='schedule'),
    url(r'^history$', views.HistoryView.as_view(), name='history'),
    url(r'^history/(?P<slug>\d{4}-\d{2}-\d{2})$', views.MeetingDetailView.as_view(), name='detail'),
    url(r'^$', RedirectView.as_view(pattern_name='meeting:schedule')),
]

app_name = 'meeting'
