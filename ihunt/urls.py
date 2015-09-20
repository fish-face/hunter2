from django.conf.urls import patterns, include, url

import ihunt.views

eventpatterns = patterns(
    '',
)

urlpatterns = patterns(
    '',
    url(r'^hunt$', ihunt.views.hunt, name="hunt"),
    url(r'^help$', ihunt.views.help, name="help"),
    url(r'^faq$', ihunt.views.faq, name="faq"),
    url(r'^login$', ihunt.views.login_view, name="login"),
    url(r'^logout$', ihunt.views.logout_view, name="logout"),
    url(r'^event/(?P<event_id>[0-9]+)/', include(eventpatterns)),
    url(r'', include(eventpatterns)),
    url(r'^$', ihunt.views.index, name="index"),
)
