from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^publication$', views.PublicationListView.as_view(), name='publications'),
    url(r'^activity/?$', views.ActivityListView.as_view(), name='activities'),
    url(r'^activity/(?P<slug>[-\w]+)$', views.ActivityDetailView.as_view(), name='activity-detail'),
]

app_name = 'website'
