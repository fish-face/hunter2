from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone
from events.models import Event
from sortedm2m.fields import SortedManyToManyField
from .runtimes.registry import RuntimesRegistry as rr

import events
import teams


class Puzzle(models.Model):
    title = models.CharField(max_length=255, unique=True)
    runtime = models.CharField(
        max_length=1, choices=rr.RUNTIME_CHOICES, default=rr.STATIC
    )
    content = models.TextField()
    cb_runtime = models.CharField(
        max_length=1, choices=rr.RUNTIME_CHOICES, default=rr.STATIC
    )
    cb_content = models.TextField(blank=True, default='')

    def __str__(self):
        return f'<Puzzle: {self.title}>'

    def unlocked_by(self, team):
        episode = self.episode_set.get(event=team.at_event)
        return episode.unlocked_by(team) and \
            episode._puzzle_unlocked_by(self, team)

    def answered_by(self, team, data=None):
        if data is None:
            data = PuzzleData(self, team)
        guesses = Guess.objects.filter(
            by__in=team.members.all()
        ).filter(
            for_puzzle=self
        ).order_by(
            '-given'
        )

        return [g for g in guesses if any([a.validate_guess(g, data) for a in self.answer_set.all()])]


class PuzzleFile(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    slug = models.SlugField()
    file = models.FileField(upload_to='puzzles/')


class Clue(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    text = models.TextField()

    class Meta:
        abstract = True


class Hint(Clue):
    time = models.DurationField()

    def unlocked_by(self, team, data):
        if data.tp_data.start_time:
            return data.tp_data.start_time + self.time < timezone.now()
        else:
            return False


class Unlock(Clue):
    def unlocked_by(self, team, data):
        guesses = Guess.objects.filter(
            by__in=team.members.all()
        ).filter(
            for_puzzle=self.puzzle
        )
        return [g for g in guesses if any([u.validate_guess(g, data) for u in self.unlockguess_set.all()])]


class UnlockGuess(models.Model):
    unlock = models.ForeignKey(Unlock, on_delete=models.CASCADE)
    runtime = models.CharField(
        max_length=1, choices=rr.RUNTIME_CHOICES, default=rr.STATIC
    )
    guess = models.TextField()

    def validate_guess(self, guess, data):
        return rr.validate_guess(
            self.runtime,
            self.guess,
            guess.guess,
            data.tp_data,
            data.t_data,
        )


class Answer(models.Model):
    for_puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    runtime = models.CharField(
        max_length=1, choices=rr.RUNTIME_CHOICES, default=rr.STATIC
    )
    answer = models.TextField()

    def __str__(self):
        return f'<Answer: {self.answer}>'

    def validate_guess(self, guess, data):
        return rr.validate_guess(
            self.runtime,
            self.answer,
            guess.guess,
            data.tp_data,
            data.t_data,
        )


class Guess(models.Model):
    for_puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    by = models.ForeignKey(teams.models.UserProfile, on_delete=models.CASCADE)
    guess = models.TextField()
    given = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Guesses'

    def __str__(self):
        return f'<Guess: {self.guess} by {self.by}>'


class TeamData(models.Model):
    team = models.ForeignKey(teams.models.Team, on_delete=models.CASCADE)
    data = JSONField(default={})

    class Meta:
        verbose_name_plural = 'Team puzzle data'

    def __str__(self):
        return f'<TeamData: {self.team.name} - {self.puzzle.title}>'


class UserData(models.Model):
    event = models.ForeignKey(events.models.Event, on_delete=models.CASCADE)
    user = models.ForeignKey(teams.models.UserProfile, on_delete=models.CASCADE)
    data = JSONField(default={})

    class Meta:
        verbose_name_plural = 'User puzzle data'

    def __str__(self):
        return f'<UserData: {self.user.name} - {self.puzzle.title}>'


class TeamPuzzleData(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    team = models.ForeignKey(teams.models.Team, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True)
    data = JSONField(default={})

    class Meta:
        verbose_name_plural = 'Team puzzle data'

    def __str__(self):
        return f'<TeamPuzzleData: {self.team.name} - {self.puzzle.title}>'


class UserPuzzleData(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    user = models.ForeignKey(teams.models.UserProfile, on_delete=models.CASCADE)
    data = JSONField(default={})

    class Meta:
        verbose_name_plural = 'User puzzle data'

    def __str__(self):
        return f'<UserPuzzleData: {self.user.name} - {self.puzzle.title}>'


# Convenience class for using all the above data objects together
class PuzzleData:
    from .models import TeamData, UserData, TeamPuzzleData, UserPuzzleData

    def __init__(self, puzzle, team, user=None):
        self.t_data, created = TeamData.objects.get_or_create(team=team)
        self.tp_data, created = TeamPuzzleData.objects.get_or_create(
            puzzle=puzzle, team=team
        )
        if user:
            self.u_data, created = UserData.objects.get_or_create(
                event=team.at_event, user=user
            )
            self.up_data, created = UserPuzzleData.objects.get_or_create(
                puzzle=puzzle, user=user
            )

    def save(self):
        self.t_data.save()
        self.tp_data.save()
        if self.u_data:
            self.u_data.save()
        if self.up_data:
            self.up_data.save()


class Episode(models.Model):
    puzzles = SortedManyToManyField(Puzzle, blank=True)
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('event', 'start_date'),)

    def __str__(self):
        return f'<Episode: {self.event.name} - {self.name}>'

    def get_puzzle(self, puzzle_number):
        n = int(puzzle_number)
        return self.puzzles.all()[n - 1:n].get()

    def get_relative_id(self):
        episodes = self.event.episode_set.order_by('start_date')
        for index, e in enumerate(episodes):
            if e == self:
                return index + 1
        return -1

    def unlocked_by(self, team):
        prequels = Episode.objects.filter(
            event=self.event,
            start_date__lt=self.start_date
        )
        return all([episode.finished_by(team) for episode in prequels])

    def finished_by(self, team):
        return all([puzzle.answered_by(team) for puzzle in self.puzzles.all()])

    def _puzzle_unlocked_by(self, puzzle, team):
        for p in self.puzzles.all():
            if p == puzzle:
                return True
            if not p.answered_by(team):
                return False
