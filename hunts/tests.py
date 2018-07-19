import datetime
import random

import freezegun
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized

from accounts.factories import UserProfileFactory
from events.factories import EventFactory, EventFileFactory
from events.test import EventTestCase
from teams.factories import TeamFactory, TeamMemberFactory
from . import runtimes
from .factories import (
    AnnouncementFactory,
    AnswerFactory,
    EpisodeFactory,
    GuessFactory,
    HintFactory,
    PuzzleFactory,
    PuzzleFileFactory,
    TeamDataFactory,
    TeamPuzzleDataFactory,
    UnlockAnswerFactory,
    UnlockFactory,
    UserDataFactory,
    UserPuzzleDataFactory,
)
from .models import PuzzleData, TeamPuzzleData


class FactoryTests(EventTestCase):
    # TODO: Consider reworking RUNTIME_CHOICES so this can be used.
    ANSWER_RUNTIMES = [
        ("static", runtimes.STATIC),
        ("regex", runtimes.REGEX),
        ("lua",  runtimes.LUA)
    ]

    @staticmethod
    def test_puzzle_factory_default_construction():
        PuzzleFactory.create()

    @staticmethod
    def test_puzzle_file_factory_default_construction():
        PuzzleFileFactory.create()

    @staticmethod
    def test_hint_factory_default_construction():
        HintFactory.create()

    @staticmethod
    def test_unlock_factory_default_construction():
        UnlockFactory.create()

    @staticmethod
    def test_unlock_answer_factory_default_construction():
        UnlockAnswerFactory.create()

    @staticmethod
    def test_answer_factory_default_construction():
        AnswerFactory.create()

    @staticmethod
    def test_guess_factory_default_construction():
        GuessFactory.create()

    @parameterized.expand(ANSWER_RUNTIMES)
    def test_guess_factory_correct_guess_generation(self, _, runtime):
        answer = AnswerFactory(runtime=runtime)
        guess = GuessFactory(for_puzzle=answer.for_puzzle, correct=True)
        self.assertTrue(answer.for_puzzle.answered_by(guess.by_team), "Puzzle answered by correct guess")

    @parameterized.expand(ANSWER_RUNTIMES)
    def test_guess_factory_incorrect_guess_generation(self, _, runtime):
        answer = AnswerFactory(runtime=runtime)
        guess = GuessFactory(for_puzzle=answer.for_puzzle, correct=False)
        self.assertFalse(answer.for_puzzle.answered_by(guess.by_team), "Puzzle not answered by incorrect guess")

    @staticmethod
    def test_team_data_factory_default_construction():
        TeamDataFactory.create()

    @staticmethod
    def test_user_data_factory_default_construction():
        UserDataFactory.create()

    @staticmethod
    def test_team_puzzle_data_factory_default_construction():
        TeamPuzzleDataFactory.create()

    @staticmethod
    def test_user_puzzle_data_factory_default_construction():
        UserPuzzleDataFactory.create()

    @staticmethod
    def test_episode_factory_default_construction():
        EpisodeFactory.create()

    @staticmethod
    def test_announcement_factory_default_construction():
        AnnouncementFactory.create()


class HomePageTests(EventTestCase):
    def test_load_homepage(self):
        # Need one default event.
        EventFactory.create()
        url = reverse('index')
        response = self.client.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class StaticValidationTests(EventTestCase):
    @staticmethod
    def test_static_save_answer():
        AnswerFactory(runtime=runtimes.STATIC)

    @staticmethod
    def test_static_save_unlock_answer():
        UnlockAnswerFactory(runtime=runtimes.STATIC)

    def test_static_answers(self):
        answer = AnswerFactory(runtime=runtimes.STATIC)
        guess = GuessFactory(for_puzzle=answer.for_puzzle, correct=True)
        self.assertTrue(answer.validate_guess(guess))
        guess = GuessFactory(for_puzzle=answer.for_puzzle, correct=False)
        self.assertFalse(answer.validate_guess(guess))
        guess = GuessFactory(for_puzzle=answer.for_puzzle, correct=False)
        self.assertFalse(answer.validate_guess(guess))
        guess = GuessFactory(for_puzzle=answer.for_puzzle, correct=False)
        self.assertFalse(answer.validate_guess(guess))


class RegexValidationTests(EventTestCase):
    def test_regex_save_answer(self):
        AnswerFactory(runtime=runtimes.REGEX, answer='[Rr]egex.*')
        with self.assertRaises(ValidationError):
            AnswerFactory(runtime=runtimes.REGEX, answer='[NotARegex')

    def test_regex_save_unlock_answer(self):
        UnlockAnswerFactory(runtime=runtimes.REGEX, guess='[Rr]egex.*')
        with self.assertRaises(ValidationError):
            UnlockAnswerFactory(runtime=runtimes.REGEX, guess='[NotARegex')

    def test_regex_answers(self):
        answer = AnswerFactory(runtime=runtimes.REGEX, answer='cor+ect')
        guess = GuessFactory(guess='correct', for_puzzle=answer.for_puzzle)
        self.assertTrue(answer.validate_guess(guess))
        guess = GuessFactory(guess='correctnot', for_puzzle=answer.for_puzzle)
        self.assertFalse(answer.validate_guess(guess))
        guess = GuessFactory(guess='incorrect', for_puzzle=answer.for_puzzle)
        self.assertFalse(answer.validate_guess(guess))
        guess = GuessFactory(guess='wrong', for_puzzle=answer.for_puzzle)
        self.assertFalse(answer.validate_guess(guess))


class LuaValidationTests(EventTestCase):
    def test_lua_save_answer(self):
        AnswerFactory(runtime=runtimes.LUA, answer='''return {} == nil''')
        with self.assertRaises(ValidationError):
            AnswerFactory(runtime=runtimes.LUA, answer='''@''')

    def test_lua_save_unlock_answer(self):
        UnlockAnswerFactory(runtime=runtimes.LUA, guess='''return {} == nil''')
        with self.assertRaises(ValidationError):
            UnlockAnswerFactory(runtime=runtimes.LUA, guess='''@''')

    def test_lua_answers(self):
        answer = AnswerFactory(runtime=runtimes.LUA, answer='''return guess == "correct"''')
        guess = GuessFactory(guess='correct', for_puzzle=answer.for_puzzle)
        self.assertTrue(answer.validate_guess(guess))
        guess = GuessFactory(guess='correctnot', for_puzzle=answer.for_puzzle)
        self.assertFalse(answer.validate_guess(guess))
        guess = GuessFactory(guess='incorrect', for_puzzle=answer.for_puzzle)
        self.assertFalse(answer.validate_guess(guess))
        guess = GuessFactory(guess='wrong', for_puzzle=answer.for_puzzle)
        self.assertFalse(answer.validate_guess(guess))


class AnswerSubmissionTests(EventTestCase):
    def setUp(self):
        self.puzzle = PuzzleFactory()
        self.episode = self.puzzle.episode_set.get()
        self.event = self.episode.event
        self.user = TeamMemberFactory(team__at_event=self.event)
        self.url = reverse('answer', kwargs={
            'episode_number': self.episode.get_relative_id(),
            'puzzle_number': self.puzzle.get_relative_id()
        },)
        self.client.force_login(self.user.user)

    def test_no_answer_given(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'no answer given')

    def test_answer_cooldown(self):
        with freezegun.freeze_time() as frozen_datetime:
            response = self.client.post(self.url, {
                'last_updated': '0',
                'answer': GuessFactory.build(for_puzzle=self.puzzle, correct=False).guess
            })
            self.assertEqual(response.status_code, 200)
            response = self.client.post(self.url, {
                'last_updated': '0',
                'answer': GuessFactory.build(for_puzzle=self.puzzle, correct=False).guess
            })
            self.assertEqual(response.status_code, 429)
            self.assertTrue(b'error' in response.content)
            frozen_datetime.tick(delta=datetime.timedelta(seconds=5))
            response = self.client.post(self.url, {
                'last_updated': '0',
                'answer': GuessFactory.build(for_puzzle=self.puzzle, correct=False).guess
            })
            self.assertEqual(response.status_code, 200)

    def test_answer_after_end(self):
        self.client.force_login(self.user.user)
        with freezegun.freeze_time() as frozen_datetime:
            self.event.end_date = timezone.now() + datetime.timedelta(seconds=5)
            self.event.save()
            response = self.client.post(self.url, {
                'last_updated': '0',
                'answer': GuessFactory.build(for_puzzle=self.puzzle, correct=False).guess
            })
            self.assertEqual(response.status_code, 200)
            frozen_datetime.tick(delta=datetime.timedelta(seconds=10))
            response = self.client.post(self.url, {
                'last_updated': '0',
                'answer': GuessFactory.build(for_puzzle=self.puzzle, correct=False).guess
            })
            self.assertEqual(response.status_code, 400)


class PuzzleStartTimeTests(EventTestCase):
    def test_start_times(self):
        self.puzzle = PuzzleFactory()
        self.episode = self.puzzle.episode_set.get()
        self.event = self.episode.event
        self.user = TeamMemberFactory(team__at_event=self.event)

        self.client.force_login(self.user.user)

        response = self.client.get(self.puzzle.get_absolute_url())
        self.assertEqual(response.status_code, 200, msg='Puzzle is accessible on absolute url')

        first_time = TeamPuzzleData.objects.get().start_time
        self.assertIsNot(first_time, None, msg='Start time is set on first access to a puzzle')

        response = self.client.get(self.puzzle.get_absolute_url())
        self.assertEqual(response.status_code, 200, msg='Puzzle is accessible on absolute url')

        second_time = TeamPuzzleData.objects.get().start_time
        self.assertEqual(first_time, second_time, msg='Start time does not alter on subsequent access')


class PuzzleAccessTests(EventTestCase):
    def setUp(self):
        self.episode = EpisodeFactory(event=self.tenant, parallel=False)
        self.puzzles = PuzzleFactory.create_batch(3, episode=self.episode)
        self.user = TeamMemberFactory(team__at_event=self.tenant)

    def test_puzzle_view_authorisation(self):
        self.client.force_login(self.user.user)

        def _check_load_callback_answer(puzzle, expected_response):
            kwargs = {
                'episode_number': self.episode.get_relative_id(),
                'puzzle_number': puzzle.get_relative_id(),
            }

            # Load
            resp = self.client.get(reverse('puzzle', kwargs=kwargs))
            self.assertEqual(resp.status_code, expected_response)

            # Callback
            resp = self.client.post(
                reverse('callback', kwargs=kwargs),
                content_type='application/json',
                HTTP_ACCEPT='application/json',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
            self.assertEqual(resp.status_code, expected_response)

            # Answer
            resp = self.client.post(
                reverse('answer', kwargs=kwargs),
                {'answer': 'NOT_CORRECT'},  # Deliberately incorrect answer
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
            self.assertEqual(resp.status_code, expected_response)

            # Solution
            resp = self.client.get(
                reverse('solution_content', kwargs=kwargs),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
            # Solution should always fail with 403 except for the ended case which is separate below
            self.assertEqual(resp.status_code, 403)

        # This test submits two answers on the same puzzle so we have to jump forward 5 seconds
        with freezegun.freeze_time() as frozen_datetime:
            # Create an initial correct guess and wait 5 seconds before attempting other answers.
            GuessFactory(
                by=self.user,
                for_puzzle=self.puzzles[0],
                correct=True
            )
            frozen_datetime.tick(delta=datetime.timedelta(seconds=5))

            # Can load, callback and answer the first two puzzles
            _check_load_callback_answer(self.puzzles[0], 200)
            _check_load_callback_answer(self.puzzles[1], 200)
            # Can't load, callback or answer the third puzzle
            _check_load_callback_answer(self.puzzles[2], 403)

            # Can load third puzzle, but not callback or answer after event ends
            old_time = frozen_datetime()
            frozen_datetime.move_to(self.tenant.end_date + datetime.timedelta(seconds=1))

            # Load
            kwargs = {
                'episode_number': self.episode.get_relative_id(),
                'puzzle_number': self.puzzles[2].get_relative_id(),
            }
            resp = self.client.get(reverse('puzzle', kwargs=kwargs))
            self.assertEqual(resp.status_code, 200)

            # Callback
            resp = self.client.post(
                reverse('callback', kwargs=kwargs),
                content_type='application/json',
                HTTP_ACCEPT='application/json',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
            self.assertEqual(resp.status_code, 400)

            # Answer
            resp = self.client.post(
                reverse('answer', kwargs=kwargs),
                {'answer': 'NOT_CORRECT'},  # Deliberately incorrect answer
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            self.assertEqual(resp.status_code, 400)

            # Solution
            resp = self.client.get(
                reverse('solution_content', kwargs=kwargs),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            self.assertEqual(resp.status_code, 200)

            # Revert to current time
            frozen_datetime.move_to(old_time)

            # Answer the second puzzle after a delay of 5 seconds
            frozen_datetime.tick(delta=datetime.timedelta(seconds=5))
            response = self.client.post(
                reverse('answer', kwargs={
                    'episode_number': self.episode.get_relative_id(),
                    'puzzle_number': self.puzzles[1].get_relative_id()}
                ), {
                    'answer': GuessFactory.build(for_puzzle=self.puzzles[1], correct=True).guess
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            self.assertEqual(response.status_code, 200)
            # Can now load, callback and answer the third puzzle
            _check_load_callback_answer(self.puzzles[2], 200)


class EpisodeBehaviourTest(EventTestCase):
    def test_reuse_puzzle(self):
        puzzles = PuzzleFactory.create_batch(2)
        with self.assertRaises(ValidationError, msg='Reusing a puzzle raises a ValidationError'):
            puzzles[0].episode_set.get().puzzles.add(puzzles[1])

    def test_linear_episodes_are_linear(self):
        linear_episode = EpisodeFactory(parallel=False)
        PuzzleFactory.create_batch(10, episode=linear_episode)
        user = UserProfileFactory()
        team = TeamFactory(at_event=linear_episode.event, members=user)

        # TODO: Scramble puzzle order before starting (so they are not in the order they were created).

        # Check we can start and that it is a linear episode.
        self.assertTrue(linear_episode.unlocked_by(team), msg='Episode is unlocked by team')
        self.assertFalse(linear_episode.parallel, msg='Episode is not set as parallel')

        for i in range(1, linear_episode.puzzles.count() + 1):
            # Test we have unlocked the question, but not answered it yet.
            self.assertTrue(linear_episode.get_puzzle(i).unlocked_by(team), msg=f'Puzzle[{i}] is unlocked')
            self.assertFalse(linear_episode.get_puzzle(i).answered_by(team), msg=f'Puzzle[{i}] is not answered')

            # Test that we have not unlocked the next puzzle before answering.
            if i < linear_episode.puzzles.count():
                self.assertFalse(linear_episode.get_puzzle(i + 1).unlocked_by(team), msg=f'Puzzle[{i + 1}] is not unlocked until previous puzzle answered')

            # Answer the question and assert that it's now answered.
            GuessFactory.create(for_puzzle=linear_episode.get_puzzle(i), by=user, correct=True)
            self.assertTrue(linear_episode.get_puzzle(i).answered_by(team), msg=f'Correct guess has answered puzzle[{i}]')

    def test_can_see_all_parallel_puzzles(self):
        parallel_episode = EpisodeFactory(parallel=True)
        PuzzleFactory.create_batch(5, episode=parallel_episode)
        team = TeamFactory(at_event=parallel_episode.event)

        # Check we can start and that it is a parallel episode.
        self.assertTrue(parallel_episode.unlocked_by(team))
        self.assertTrue(parallel_episode.parallel)

        # Ensure all puzzles in a parallel episode are unlocked.
        for puzzle in parallel_episode.puzzles.all():
            self.assertTrue(puzzle.unlocked_by(team), msg='Puzzle unlocked in parallel episode')

    def test_headstarts(self):
        # TODO: Replace with episode sequence factory?
        episode1 = EpisodeFactory()
        episode2 = EpisodeFactory(event=episode1.event, headstart_from=episode1)
        PuzzleFactory.create_batch(10, episode=episode1)
        user = UserProfileFactory()
        team = TeamFactory(at_event=episode1.event, members=user)

        # Check that the headstart granted is the sum of the puzzle headstarts
        headstart = datetime.timedelta()
        self.assertEqual(episode1.headstart_granted(team), datetime.timedelta(minutes=0), "No headstart when puzzles unanswered")

        for i in range(1, episode1.puzzles.count() + 1):
            # Start answering puzzles
            GuessFactory.create(for_puzzle=episode1.get_puzzle(i), by=user, correct=True)
            self.assertTrue(episode1.get_puzzle(i).answered_by(team), msg=f'Correct guess has answered puzzle[{i}]')

            # Check headstart summing logic.
            headstart += episode1.get_puzzle(i).headstart_granted
            self.assertEqual(episode1.headstart_granted(team), headstart, "Episode headstart is sum of answered puzzle headstarts")

        # All of these headstarts should be applied to the second episode.
        self.assertEqual(episode2.headstart_applied(team), headstart)

        # Test that headstart does not apply in the wrong direction
        self.assertEqual(episode1.headstart_applied(team), datetime.timedelta(minutes=0))

    def test_next_linear_puzzle(self):
        linear_episode = EpisodeFactory(parallel=False)
        PuzzleFactory.create_batch(10, episode=linear_episode)
        user = UserProfileFactory()
        team = TeamFactory(at_event=linear_episode.event, members=user)

        # TODO: Scramble puzzle order before starting (so they are not in the order they were created).

        # Check we can start and that it is a linear episode.
        self.assertTrue(linear_episode.unlocked_by(team), msg='Episode is unlocked by team')
        self.assertFalse(linear_episode.parallel, msg='Episode is not set as parallel')

        for i in range(1, linear_episode.puzzles.count() + 1):
            # Test we have unlocked the question, but not answered it yet.
            self.assertEqual(linear_episode.next_puzzle(team), i, msg=f'Puzzle[{i}]\'s next puzzle is Puzzle[{i + 1}]')

            # Answer the question and assert that it's now answered.
            GuessFactory.create(for_puzzle=linear_episode.get_puzzle(i), by=user, correct=True)
            self.assertTrue(linear_episode.get_puzzle(i).answered_by(team), msg=f'Correct guess has answered puzzle[{i}]')

    def test_next_parallel_puzzle(self):
        parallel_episode = EpisodeFactory(parallel=True)
        PuzzleFactory.create_batch(10, episode=parallel_episode)
        user = UserProfileFactory()
        team = TeamFactory(at_event=parallel_episode.event, members=user)

        # TODO: Scramble puzzle order before starting (so they are not in the order they were created).

        # Check we can start and that it is a linear episode.
        self.assertTrue(parallel_episode.unlocked_by(team), msg='Episode is unlocked by team')
        self.assertTrue(parallel_episode.parallel, msg='Episode is not set as parallel')

        # Answer all questions in a random order.
        answer_order = list(range(1, parallel_episode.puzzles.count() + 1))
        random.shuffle(answer_order)

        for i in answer_order:
            # Should be no 'next' puzzle for parallel episodes, unless there is just one left.
            # TODO: Check that this is the behaviour that we want, never having a next seems more logical.
            if i != answer_order[-1]:
                self.assertIsNone(parallel_episode.next_puzzle(team), msg='Parallel episode has no next puzzle')
            else:
                self.assertEqual(parallel_episode.next_puzzle(team), i, msg='Last unanswered is next puzzle in parallel episode')

            # Answer the question and assert that it's now answered.
            GuessFactory.create(for_puzzle=parallel_episode.get_puzzle(i), by=user, correct=True)
            self.assertTrue(parallel_episode.get_puzzle(i).answered_by(team), msg=f'Correct guess has answered puzzle[{i}]')
        self.assertIsNone(parallel_episode.next_puzzle(team), msg='Parallel episode has no next puzzle when all puzzles are answered')

    def test_puzzle_numbers(self):
        for episode in EpisodeFactory.create_batch(5):
            for i, puzzle in enumerate(PuzzleFactory.create_batch(5, episode=episode)):
                self.assertEqual(puzzle.get_relative_id(), i + 1, msg='Relative ID should match index in episode')
                self.assertEqual(episode.get_puzzle(puzzle.get_relative_id()), puzzle, msg='A Puzzle\'s relative ID should retrieve it from its Episode')


class EpisodeSequenceTests(EventTestCase):
    def setUp(self):
        self.event = self.tenant
        self.episode1 = EpisodeFactory(event=self.event)
        self.episode2 = EpisodeFactory(event=self.event, prequels=self.episode1)
        self.user = TeamMemberFactory(team__at_event=self.event)

    def test_episode_prequel_validation(self):
        # Because we intentionally throw exceptions we need to use transaction.atomic() to avoid a TransactionManagementError
        with self.assertRaises(ValidationError), transaction.atomic():
            self.episode1.prequels.add(self.episode1)
        with self.assertRaises(ValidationError), transaction.atomic():
            self.episode1.prequels.add(self.episode2)

    def test_episode_unlocking(self):
        puzzle = PuzzleFactory(episode=self.episode1)

        self.client.force_login(self.user.user)

        # Can load first episode

        response = self.client.get(
            reverse('episode', kwargs={'episode_number': self.episode1.get_relative_id()}),
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('episode_content', kwargs={'episode_number': self.episode1.get_relative_id()}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

        # Can't load second episode
        response = self.client.get(
            reverse('episode', kwargs={'episode_number': self.episode2.get_relative_id()}),
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.get(
            reverse('episode_content', kwargs={'episode_number': self.episode2.get_relative_id()}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)

        # Can load second episode after event end
        with freezegun.freeze_time() as frozen_datetime:
            frozen_datetime.move_to(self.event.end_date + datetime.timedelta(seconds=1))
            response = self.client.get(
                reverse('episode', kwargs={'episode_number': self.episode2.get_relative_id()}),
            )
            self.assertEqual(response.status_code, 200)
            response = self.client.get(
                reverse('episode_content', kwargs={'episode_number': self.episode2.get_relative_id()}),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            self.assertEqual(response.status_code, 200)

        # Unlock second episode
        GuessFactory(for_puzzle=puzzle, by=self.user, correct=True)

        # Can now load second episode
        response = self.client.get(
            reverse('episode', kwargs={'episode_number': self.episode2.get_relative_id()}),
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('episode_content', kwargs={'episode_number': self.episode2.get_relative_id()}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)


class ClueDisplayTests(EventTestCase):
    def setUp(self):
        self.episode = EpisodeFactory()
        self.user = UserProfileFactory()
        self.puzzle = PuzzleFactory(episode=self.episode)
        self.team = TeamFactory(at_event=self.episode.event, members={self.user})
        self.data = PuzzleData(self.puzzle, self.team, self.user)  # Don't actually need to use a factory here.

    def test_hint_display(self):
        hint = HintFactory(puzzle=self.puzzle)

        with freezegun.freeze_time() as frozen_datetime:
            self.data.tp_data.start_time = timezone.now()
            self.assertFalse(hint.unlocked_by(self.team, self.data), "Hint not unlocked by team at start")

            frozen_datetime.tick(hint.time / 2)
            self.assertFalse(hint.unlocked_by(self.team, self.data), "Hint not unlocked by less than hint time duration.")

            frozen_datetime.tick(hint.time)
            self.assertTrue(hint.unlocked_by(self.team, self.data), "Hint unlocked by team after required time elapsed.")

    def test_unlock_display(self):
        other_team = TeamFactory(at_event=self.episode.event)

        unlock = UnlockFactory(puzzle=self.puzzle)
        GuessFactory.create(for_puzzle=self.puzzle, by=self.user, guess=unlock.unlockanswer_set.get().guess)

        # Check can only be seen by the correct teams.
        self.assertTrue(unlock.unlocked_by(self.team), "Unlock should be visible not it's been guessed")
        self.assertFalse(unlock.unlocked_by(other_team), "Unlock should not be visible to other team")


class FileUploadTests(EventTestCase):
    def setUp(self):
        self.eventfile = EventFileFactory()
        self.user = UserProfileFactory()
        self.client.force_login(self.user.user)

    def test_load_episode_with_eventfile(self):
        episode = EpisodeFactory(flavour=f'${{{self.eventfile.slug}}}')
        response = self.client.get(episode.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.eventfile.file.url)

    def test_load_puzzle_with_eventfile(self):
        puzzle = PuzzleFactory(content=f'${{{self.eventfile.slug}}}')
        response = self.client.get(puzzle.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.eventfile.file.url)

    def test_load_puzzle_with_puzzlefile(self):
        puzzle = PuzzleFactory()
        puzzlefile = PuzzleFileFactory(puzzle=puzzle)
        puzzle.content = f'${{{puzzlefile.slug}}}'
        puzzle.save()
        response = self.client.get(puzzle.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, puzzlefile.slug)  # Puzzle files don't use their URL so just check slug

    def test_puzzlefile_overrides_eventfile(self):
        puzzle = PuzzleFactory()
        puzzlefile = PuzzleFileFactory(puzzle=puzzle)
        puzzle.content = f'${{{puzzlefile.slug}}}'
        puzzle.save()
        response = self.client.get(puzzle.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, puzzlefile.slug)  # Puzzle files don't use their URL so just check slug


class AdminTeamTests(EventTestCase):
    def setUp(self):
        self.event = self.tenant
        self.episode = EpisodeFactory(event=self.event)
        self.admin_user = UserProfileFactory()
        self.admin_team = TeamFactory(at_event=self.event, is_admin=True, members={self.admin_user})

    def test_can_view_episode(self):
        self.client.force_login(self.admin_user.user)
        response = self.client.get(
            reverse('episode', kwargs={'episode_number': self.episode.get_relative_id()}),
        )
        self.assertEqual(response.status_code, 200)

    def test_can_view_guesses(self):
        self.client.force_login(self.admin_user.user)
        response = self.client.get(reverse('guesses'))
        self.assertEqual(response.status_code, 200)


class ProgressionTests(EventTestCase):
    def setUp(self):
        self.episode = EpisodeFactory()
        self.event = self.episode.event
        self.user1 = UserProfileFactory()
        self.user2 = UserProfileFactory()
        self.team1 = TeamFactory(at_event=self.event, members={self.user1})
        self.team2 = TeamFactory(at_event=self.event, members={self.user2})

    def test_answered_by_ordering(self):
        puzzle1 = PuzzleFactory(episode=self.episode)

        # Submit two correct answers, 1 an hour after the other
        with freezegun.freeze_time() as frozen_datetime:
            guess1 = GuessFactory(for_puzzle=puzzle1, by=self.user1, correct=True)
            frozen_datetime.tick(datetime.timedelta(hours=1))
            guess2 = GuessFactory(for_puzzle=puzzle1, by=self.user1, correct=True)

            # Fudge another before the first to test ordering.
            frozen_datetime.tick(datetime.timedelta(hours=-2))
            guess3 = GuessFactory(for_puzzle=puzzle1, by=self.user1, correct=True)

            # Ensure the first given answer is reported first
            self.assertEqual(len(puzzle1.answered_by(self.team1)), 3)
            self.assertEqual(puzzle1.answered_by(self.team1)[0], guess3)
            self.assertEqual(puzzle1.answered_by(self.team1)[1], guess1)
            self.assertEqual(puzzle1.answered_by(self.team1)[2], guess2)

    def test_episode_finishing(self):
        # Ensure at least one puzzle in episode.
        puzzles = PuzzleFactory.create_batch(3, episode=self.episode)

        # Check episode has not been completed
        self.assertFalse(self.episode.finished_by(self.team1))

        # Team 1 answer all questions correctly
        for puzzle in puzzles:
            GuessFactory.create(for_puzzle=puzzle, by=self.user1, correct=True)

        # Ensure this team has finished the episode
        self.assertTrue(self.episode.finished_by(self.team1))

    def test_finish_positions(self):
        puzzle1, puzzle2, puzzle3 = PuzzleFactory.create_batch(3, episode=self.episode)

        # Check there are no winners to begin with
        self.assertFalse(self.episode.finished_by(self.team1))
        self.assertFalse(self.episode.finished_by(self.team2))
        self.assertEqual(len(self.episode.finished_positions()), 0)

        # Answer all the questions correctly for both teams with team 1 ahead to begin with then falling behind
        GuessFactory.create(for_puzzle=puzzle1, by=self.user1, correct=True)
        GuessFactory.create(for_puzzle=puzzle2, by=self.user1, correct=True)

        # Check only the first team has finished the first questions
        self.assertEqual(len(puzzle1.finished_teams(self.event)), 1)
        self.assertEqual(puzzle1.finished_teams(self.event)[0], self.team1)
        self.assertEqual(puzzle1.position(self.team1), 0)
        self.assertEqual(puzzle1.position(self.team2), None)

        # Team 2 completes all answers
        GuessFactory.create(for_puzzle=puzzle1, by=self.user2, correct=True)
        GuessFactory.create(for_puzzle=puzzle2, by=self.user2, correct=True)
        GuessFactory.create(for_puzzle=puzzle3, by=self.user2, correct=True)

        # Ensure this team has finished the questions and is listed as first in the finished teams
        self.assertEqual(len(self.episode.finished_positions()), 1)
        self.assertEqual(self.episode.finished_positions()[0], self.team2)

        # Team 1 finishes as well.
        GuessFactory(for_puzzle=puzzle3, by=self.user1, correct=True)

        # Ensure both teams have finished, and are ordered correctly
        self.assertEqual(len(self.episode.finished_positions()), 2)
        self.assertEqual(self.episode.finished_positions()[0], self.team2)
        self.assertEqual(self.episode.finished_positions()[1], self.team1)

    def test_guesses(self):
        puzzle1 = PuzzleFactory(episode=self.episode)

        # Single incorrect guess
        GuessFactory(for_puzzle=puzzle1, by=self.user1, correct=False)

        # Check we have no correct answers
        self.assertEqual(len(puzzle1.first_correct_guesses(self.event)), 0)

        # Add two correct guesses after each other
        with freezegun.freeze_time() as frozen_datetime:
            first_correct_guess = GuessFactory(for_puzzle=puzzle1, by=self.user1, correct=True)
            frozen_datetime.tick(datetime.timedelta(hours=1))
            GuessFactory.create(for_puzzle=puzzle1, by=self.user1, correct=True)

        # Ensure that the first correct guess is correctly returned
        self.assertEqual(puzzle1.first_correct_guesses(self.event)[self.team1], first_correct_guess)


class CorrectnessCacheTests(EventTestCase):
    def setUp(self):
        self.episode = EpisodeFactory()
        self.event = self.episode.event
        self.user1 = UserProfileFactory()
        self.user2 = UserProfileFactory()
        self.team1 = TeamFactory(at_event=self.event, members={self.user1})
        self.team2 = TeamFactory(at_event=self.event, members={self.user2})
        self.puzzle1 = PuzzleFactory(episode=self.episode)
        self.puzzle2 = PuzzleFactory(episode=self.episode)
        self.answer1 = self.puzzle1.answer_set.get()

    def test_changing_answers(self):
        # Check starting state
        self.assertFalse(self.puzzle1.answered_by(self.team1))
        self.assertFalse(self.puzzle2.answered_by(self.team2))

        # Add a correct guess and check it is marked correct
        guess1 = GuessFactory(for_puzzle=self.puzzle1, by=self.user1, correct=True)
        self.assertTrue(guess1.correct_current)
        self.assertTrue(self.puzzle1.answered_by(self.team1))

        # Add an incorrect guess and check
        guess2 = GuessFactory(for_puzzle=self.puzzle2, by=self.user2, correct=False)
        self.assertTrue(guess2.correct_current)
        self.assertFalse(self.puzzle2.answered_by(self.team2))

        # Alter the answer and check only the first guess is invalidated
        self.answer1.answer = AnswerFactory.build(runtime=self.answer1.runtime).answer
        self.answer1.save()
        guess1.refresh_from_db()
        guess2.refresh_from_db()
        self.assertFalse(guess1.correct_current)
        self.assertTrue(guess2.correct_current)
        self.assertFalse(guess1.get_correct_for())
        self.assertFalse(self.puzzle1.answered_by(self.team1))

        # Update the first guess and check
        guess1.guess = GuessFactory.build(for_puzzle=self.puzzle1, correct=True).guess
        guess1.save()
        self.assertTrue(self.puzzle1.answered_by(self.team1))

        # Delete the first answer and check
        self.answer1.delete()
        guess1.refresh_from_db()
        guess2.refresh_from_db()
        self.assertFalse(guess1.correct_current)
        self.assertTrue(guess2.correct_current)
        self.assertFalse(guess1.get_correct_for())
        self.assertFalse(self.puzzle1.answered_by(self.team1))

        # Add an answer that matches guess 2 and check
        AnswerFactory(for_puzzle=self.puzzle2, runtime=runtimes.STATIC, answer=guess2.guess).save()
        guess1.refresh_from_db()
        guess2.refresh_from_db()
        self.assertTrue(guess1.correct_current)
        self.assertFalse(guess2.correct_current)
        self.assertFalse(self.puzzle1.answered_by(self.team1))
        self.assertTrue(guess2.get_correct_for())
        self.assertTrue(self.puzzle2.answered_by(self.team2))


class GuessTeamDenormalisationTests(EventTestCase):
    def setUp(self):
        self.episode = EpisodeFactory()
        self.user1 = UserProfileFactory()
        self.user2 = UserProfileFactory()
        self.team1 = TeamFactory(at_event=self.episode.event, members={self.user1})
        self.team2 = TeamFactory(at_event=self.episode.event, members={self.user2})
        self.puzzle1 = PuzzleFactory(episode=self.episode)
        self.puzzle2 = PuzzleFactory(episode=self.episode)

    def test_adding_guess(self):
        guess1 = GuessFactory(for_puzzle=self.puzzle1, by=self.user1, correct=False)
        guess2 = GuessFactory(for_puzzle=self.puzzle2, by=self.user2, correct=False)

        # Check by_team denormalisation.
        self.assertEqual(guess1.by_team, self.team1, "by_team denormalisation consistent with user's team")
        self.assertEqual(guess2.by_team, self.team2, "by_team denormalisation consistent with user's team")

    def test_join_team_updates_guesses(self):
        guess1 = GuessFactory(for_puzzle=self.puzzle1, by=self.user1, correct=False)
        guess2 = GuessFactory(for_puzzle=self.puzzle2, by=self.user2, correct=False)

        # Swap teams and check the guesses update
        self.team1.members.set([])
        self.team2.members.set([self.user1])
        self.team1.save()
        self.team2.save()
        self.team1.members.set([self.user2])
        self.team1.save()

        # Refresh the retrieved Guesses and ensure they are consistent.
        guess1.refresh_from_db()
        guess2.refresh_from_db()
        self.assertEqual(guess1.by_team, self.team2, "by_team denormalisation consistent with user's team")
        self.assertEqual(guess2.by_team, self.team1, "by_team denormalisation consistent with user's team")
