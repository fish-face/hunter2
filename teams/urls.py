from django.conf.urls import include, url
from . import views

teampatterns = [
    url(r'^$', views.TeamView.as_view(), name='team'),
    url(r'^invite$', views.Invite.as_view(), name='invite'),
    url(r'^cancelinvite$', views.CancelInvite.as_view(), name='cancelinvite'),
    url(r'^acceptinvite$', views.AcceptInvite.as_view(), name='acceptinvite'),
    url(r'^denyinvite$', views.DenyInvite.as_view(), name='denyinvite'),
    url(r'^request$', views.Request.as_view(), name='request'),
    url(r'^cancelrequest$', views.CancelRequest.as_view(), name='cancelrequest'),
    url(r'^acceptrequest$', views.AcceptRequest.as_view(), name='acceptrequest'),
    url(r'^denyrequest$', views.DenyRequest.as_view(), name='denyrequest'),
]

eventpatterns = [
    url(r'^team/$', views.ManageTeamView.as_view(), name='manage_team'),
    url(r'^team/create$', views.CreateTeamView.as_view(), name='create_team'),
    url(r'^team/(?P<team_id>[1-9]\d*)/', include(teampatterns), name='team'),
]

urlpatterns = [
    url(r'^event/(?P<event_id>[1-9]\d*)/', include(eventpatterns)),
    url(r'^team_autocomplete$', views.TeamAutoComplete.as_view(), name='team_autocomplete'),
]
