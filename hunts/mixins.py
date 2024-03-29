# Copyright (C) 2018 The Hunter2 Contributors.
#
# This file is part of Hunter2.
#
# Hunter2 is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# Hunter2 is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with Hunter2.  If not, see <http://www.gnu.org/licenses/>.


from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from . import rules
from . import utils
from .models import Puzzle

# If PuzzleUnlockedMixin inherits from EpisodeUnlockedMixin the dispatch methods execute in the wrong order


class EpisodeUnlockedMixin():
    def dispatch(self, request, episode_number, *args, **kwargs):
        # Views using this mixin inevitably want the episode object so keep it on the request
        request.episode = utils.event_episode(request.tenant, episode_number)
        request.admin = rules.is_admin_for_episode(request.user, request.episode)

        if not request.episode.started(request.team) and not request.admin:
            if request.is_ajax():
                raise PermissionDenied
            return TemplateResponse(
                request,
                'hunts/episodenotstarted.html',
                context={
                    'episode': request.episode.name,
                    'startdate': request.episode.start_date - request.episode.headstart_applied(request.team),
                    'headstart': request.episode.headstart_applied(request.team),
                },
                status=403,
            )

        # TODO: May need caching of progress to avoid DB load
        if not request.episode.unlocked_by(request.team) and not request.admin:
            if request.is_ajax():
                raise PermissionDenied
            return TemplateResponse(
                request, 'hunts/episodelocked.html', status=403
            )

        return super().dispatch(request, *args, episode_number=episode_number, **kwargs)


class PuzzleUnlockedMixin():
    def dispatch(self, request, episode_number, puzzle_number, *args, **kwargs):
        # Views using this mixin inevitable want the episode and puzzle objects so keep it on the request
        request.episode, request.puzzle = utils.event_episode_puzzle(request.tenant, episode_number, puzzle_number)
        request.admin = rules.is_admin_for_puzzle(request.user, request.puzzle)

        if (not request.episode.started(request.team) or not request.episode.unlocked_by(request.team)) and not request.admin:
            if request.is_ajax():
                raise PermissionDenied
            event_url = reverse('event')
            return redirect(f'{event_url}#episode-{episode_number}')

        if not request.puzzle.started(request.team) and not request.admin:
            if request.is_ajax():
                raise PermissionDenied
            return TemplateResponse(
                request,
                'hunts/puzzlenotstarted.html',
                context={
                    'startdate': request.puzzle.start_date
                },
                status=403,
            )

        if not request.puzzle.unlocked_by(request.team) and not request.admin:
            if request.is_ajax():
                raise PermissionDenied
            return TemplateResponse(
                request, 'hunts/puzzlelocked.html', status=403
            )

        return super().dispatch(request, *args, episode_number=episode_number, puzzle_number=puzzle_number, **kwargs)


class PuzzleAdminMixin():
    def dispatch(self, request, puzzle_id, *args, **kwargs):
        try:
            request.puzzle = Puzzle.objects.get(pk=puzzle_id)
        except Puzzle.DoesNotExist:
            raise PermissionDenied
        request.admin = rules.is_admin_for_puzzle(request.user, request.puzzle)
        if not request.admin:
            raise PermissionDenied
        return super().dispatch(request, *args, puzzle_id=puzzle_id, *args, **kwargs)
