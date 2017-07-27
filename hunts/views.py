from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from string import Template
from . import models
import teams
from . import rules
from .runtimes.registry import RuntimesRegistry as rr
from . import utils

import events


class Index(View):
    def get(self, request):
        return TemplateResponse(
            request,
            'hunts/index.html',
        )


@method_decorator(login_required, name='dispatch')
class Episode(View):
    def get(self, request, episode_number):
        episode = utils.event_episode(request.event, episode_number)
        admin = rules.is_admin_for_episode(request.user, episode)

        if not episode.started(request.team) and not admin:
            return TemplateResponse(
                request,
                'hunts/episodenotstarted.html',
                context={
                    'episode': episode.name,
                    'startdate': episode.start_date - episode.headstart_applied(request.team),
                    'headstart': episode.headstart_applied(request.team),
                }
            )

        # TODO: May need caching of progress to avoid DB load
        if not episode.unlocked_by(request.team):
            return TemplateResponse(
                request, 'hunts/episodelocked.html', status=403
            )

        all_puzzles = episode.puzzles.all()
        puzzles = []
        for p in all_puzzles:
            if p.unlocked_by(request.team):
                puzzles.append(p)

        positions = episode.finished_positions()
        if request.team in positions:
            position = positions.index(request.team)
            if position < 3:
                position = {0: 'first', 1: 'second', 2: 'third'}[position]
            else:
                position += 1
                position = f'in position {position}'
        else:
            position = None

        return TemplateResponse(
            request,
            'hunts/episode.html',
            context={
                'admin': admin,
                'episode': episode.name,
                'position': position,
                'episode_number': episode_number,
                'event_id': request.event.pk,
                'puzzles': puzzles,
            }
        )


@method_decorator(login_required, name='dispatch')
class Guesses(View):
    def get(self, request):
        admin = rules.is_admin_for_event(request.user, request.event)

        if not admin:
            raise PermissionDenied

        return TemplateResponse(
            request,
            'hunts/guesses.html',
        )


@method_decorator(login_required, name='dispatch')
class GuessesContent(View):
    def get(self, request):
        admin = rules.is_admin_for_event(request.user, request.event)

        if not admin:
            return HttpResponseForbidden()

        episode = request.GET.get('episode')
        puzzle = request.GET.get('puzzle')
        team = request.GET.get('team')

        puzzles = models.Puzzle.objects.filter(episode__event=request.event)
        if puzzle:
            puzzles = puzzles.filter(id=puzzle)
        if episode:
            puzzles = puzzles.filter(episode=episode)

        all_guesses = models.Guess.objects.filter(
            for_puzzle__in=puzzles
        ).order_by(
            '-given'
        )

        if team:
            team = teams.models.Team.objects.get(id=team)
            all_guesses = all_guesses.filter(by__in=team.members.all())

        guess_pages = Paginator(all_guesses, 50)
        page = request.GET.get('page')
        try:
            guesses = guess_pages.page(page)
        except PageNotAnInteger:
            guesses = guess_pages.page(1)
        except EmptyPage:
            guesses = guess_pages.page(guess_pages.num_pages)

        for g in guesses:
            g_data = models.PuzzleData(g.for_puzzle, g.by_team(), g.by)
            answers = models.Answer.objects.filter(for_puzzle=g.for_puzzle)
            if any([a.validate_guess(g, g_data) for a in answers]):
                g.correct = True
                continue

            if request.GET.get('highlight_unlocks'):
                unlockanswers = models.UnlockAnswer.objects.filter(unlock__puzzle=g.for_puzzle)
                if any([a.validate_guess(g, g_data) for a in unlockanswers]):
                    g.unlocked = True

        return TemplateResponse(
            request,
            'hunts/guesses_content.html',
            context={
                'event_id': request.event.pk,
                'guesses': guesses,
            }
        )


@method_decorator(login_required, name='dispatch')
class EventDirect(View):
    def get(self, request):
        event = events.models.Event.objects.filter(current=True).get()

        return redirect(
            'event',
            event_id=event.id,
        )


@method_decorator(login_required, name='dispatch')
class EventIndex(View):
    def get(self, request):

        event = request.event

        episodes = models.Episode.objects \
                                 .filter(event=event.id) \
                                 .filter(start_date__lte=timezone.now()) \

        return TemplateResponse(
            request,
            'events/index.html',
            context={
                'event_title':  event.name,
                'event_id':     event.id,
                'episodes':     list(episodes),
            }
        )


@method_decorator(login_required, name='dispatch')
class Puzzle(View):
    def get(self, request, episode_number, puzzle_number):
        episode, puzzle = utils.event_episode_puzzle(
            request.event, episode_number, puzzle_number
        )
        admin = rules.is_admin_for_puzzle(request.user, puzzle)

        # Make the puzzle available on the request object
        request.puzzle = puzzle

        # If episode has not started redirect to episode holding page
        if episode.start_date > timezone.now() and not admin:
            if request.event:
                return redirect(
                    'episode',
                    event_id=request.event.pk,
                    episode_number=episode_number,
                )
            else:
                return redirect('episode', episode_number=episode_number)

        # TODO: May need caching of progress to avoid DB load
        if not puzzle.unlocked_by(request.team):
            return TemplateResponse(
                request, 'hunts/puzzlelocked.html', status=403
            )

        data = models.PuzzleData(puzzle, request.team, request.user.profile)

        if not data.tp_data.start_time:
            data.tp_data.start_time = timezone.now()

        answered = reversed(puzzle.answered_by(request.team, data))
        hints = [
            h for h in puzzle.hint_set.all() if h.unlocked_by(request.team, data)
        ]
        unlocks = [
            {
                'guesses': u.unlocked_by(request.team, data),
                'text': u.text
            }
            for u in puzzle.unlock_set.all()
        ]
        unlocks = [u for u in unlocks if len(u['guesses'])]

        files = {f.slug: f.file.url for f in puzzle.puzzlefile_set.all()}

        text = Template(rr.evaluate(
            runtime=puzzle.runtime,
            script=puzzle.content,
            team_puzzle_data=data.tp_data,
            user_puzzle_data=data.up_data,
            team_data=data.t_data,
            user_data=data.u_data,
        )).safe_substitute(**files)

        response = TemplateResponse(
            request,
            'hunts/puzzle.html',
            context={
                'answered': answered,
                'admin': admin,
                'hints': hints,
                'title': puzzle.title,
                'text': text,
                'unlocks': unlocks,
            }
        )

        data.save()

        return response


@method_decorator(login_required, name='dispatch')
class Answer(View):
    def post(self, request, episode_number, puzzle_number):
        episode, puzzle = utils.event_episode_puzzle(
            request.event, episode_number, puzzle_number
        )

        given_answer = request.POST['answer']
        guess = models.Guess(
            guess=given_answer,
            for_puzzle=puzzle,
            by=request.user.profile
        )
        guess.save()

        if request.event:
            return redirect(
                'puzzle',
                event_id=request.event.pk,
                episode_number=episode_number,
                puzzle_number=puzzle_number,
            )
        else:
            return redirect(
                'episode',
                episode_number=episode_number,
                puzzle_number=puzzle_number,
            )


@method_decorator(login_required, name='dispatch')
class Callback(View):
    def post(self, request, episode_number, puzzle_number):
        if request.content_type != 'application/json':
            return HttpResponse(status=415)
        if 'application/json' not in request.META['HTTP_ACCEPT']:
            return HttpResponse(status=406)

        episode, puzzle = utils.event_episode_puzzle(
            request.event, episode_number, puzzle_number
        )

        data = models.PuzzleData(puzzle, request.team, request.user)

        response = HttpResponse(
            rr.evaluate(
                runtime=puzzle.cb_runtime,
                script=puzzle.cb_content,
                team_puzzle_data=data.tp_data,
                user_puzzle_data=data.up_data,
                team_data=data.t_data,
                user_data=data.u_data,
            )
        )

        data.save()

        return response


class PuzzleInfo(View):
    """View for translating a UUID "token" into information about a user's puzzle attempt"""
    def get(self, request):
        token = request.GET.get('token')
        if token is None:
            return JsonResponse({
                'result': 'Bad Request',
                'message': 'Must provide token',
            }, status=400)
        try:
            up_data = models.UserPuzzleData.objects.get(token=token)
        except ValidationError:
            return JsonResponse({
                'result': 'Bad Request',
                'message': 'Token must be a UUID',
            }, status=400)
        except models.UserPuzzleData.DoesNotExist:
            return JsonResponse({
                'result': 'Not Found',
                'message': 'No such token',
            }, status=404)
        user = up_data.user
        team = up_data.team()
        return JsonResponse({
            'result': 'Success',
            'team_id': team.pk,
            'user_id': user.pk,
        })
