from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView
from . import views

urlpatterns = [
    url(r'^schedule$', views.ScheduleView.as_view(), name='schedule'),
    url(r'^history$', TemplateView.as_view(template_name='meeting/base.html'), name='history'),
    url(r'^$', RedirectView.as_view(pattern_name='meeting:schedule')),
]

app_name = 'meeting'
