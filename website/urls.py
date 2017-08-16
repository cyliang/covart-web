from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^member$', views.MemberListView.as_view(), name='members'),
    url(r'^member/(?P<pk>\d+)-(?P<name>[^/]+)$', views.MemberDetailView.as_view(), name='member-detail'),
    url(r'^member/(?P<pk>\d+)-(?P<name>[^/]+)/update$', views.MemberUpdateView.as_view(), name='member-update'),
    url(r'^publication$', views.PublicationListView.as_view(), name='publications'),
    url(r'^publication/import$', views.PublicationImportView.as_view(), name='publication-import'),
    url(r'^activity$', views.ActivityListView.as_view(), name='activities'),
    url(r'^activity/(?P<slug>[-\w]+)$', views.ActivityDetailView.as_view(), name='activity-detail'),
    url(r'^links$', views.LinkListView.as_view(), name='links'),
]

app_name = 'website'
