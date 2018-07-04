from django.urls import include, path
from django.views.generic import TemplateView

from . import views

eventadminpatterns = [
    path('episode_list', views.EpisodeList.as_view(), name='episode_list'),
    path('guesses', views.Guesses.as_view(), name='guesses'),
    path('guesses_content', views.GuessesContent.as_view(), name='guesses_content'),
    path('stats', views.Stats.as_view(), name='stats'),
    path('stats_content/<int:episode_id>', views.StatsContent.as_view(), name='stats_content'),
]

urlpatterns = [
]

puzzlepatterns = [
    path('', views.Puzzle.as_view(), name='puzzle'),
    path('an', views.Answer.as_view(), name='answer'),
    path('cb', views.Callback.as_view(), name='callback'),
    path('media/<slug:file_slug>', views.PuzzleFile.as_view(), name='puzzle_file'),
]

episodepatterns = [
    path('', views.Episode.as_view(), name='episode'),
    path('content', views.EpisodeContent.as_view(), name='episode_content'),
    path('pz/<int:puzzle_number>/', include(puzzlepatterns)),
]

eventpatterns = [
    path('', views.EventIndex.as_view(), name='event'),
    path('about', views.AboutView.as_view(), name='about'),
    path('rules', views.RulesView.as_view(), name='rules'),
    path('help', views.HelpView.as_view(), name='help'),
    path('examples', views.ExamplesView.as_view(), name='examples'),
    path('ep/<int:episode_number>/', include(episodepatterns)),
]

urlpatterns = [
    path(
        r'',
        views.Index.as_view(),
        name='index'
    ),
    path(
        r'faq',
        TemplateView.as_view(template_name='hunts/faq.html'),
        name='faq'
    ),
    path(
        r'help',
        TemplateView.as_view(template_name='hunts/help.html'),
        name='help'
    ),
    path('hunt/', include(eventpatterns)),
    path('huntadmin/', include(eventadminpatterns)),
    path('puzzle_info', views.PuzzleInfo.as_view(), name='puzzle_info'),
]
