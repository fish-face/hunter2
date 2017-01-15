from teams.models import Team

import rules


@rules.predicate
def is_admin_for_event(user, event):
    try:
        admin_team = event.teams.filter(is_admin=True).get()
    except Team.DoesNotExist:
        return False
    return user.profile in admin_team.users.all()

rules.add_perm('ihunt.change_event', is_admin_for_event)


@rules.predicate
def is_admin_for_episode(user, episode):
    return is_admin_for_event(user, episode.event)

rules.add_perm('ihunt.change_episode', is_admin_for_episode)
rules.add_perm('ihunt.delete_episode', is_admin_for_episode)


@rules.predicate
def is_admin_for_puzzle(user, puzzle):
    return any(
        [is_admin_for_episode(user, ep) for ep in puzzle.episodes.all()]
    )

rules.add_perm('ihunt.change_puzzle', is_admin_for_puzzle)
rules.add_perm('ihunt.delete_puzzle', is_admin_for_puzzle)


@rules.predicate
def is_admin_for_clue(user, clue):
    return is_admin_for_puzzle(user, clue.puzzle)

rules.add_perm('ihunt.change_hint', is_admin_for_clue)
rules.add_perm('ihunt.delete_hint', is_admin_for_clue)
rules.add_perm('ihunt.change_unlock', is_admin_for_clue)
rules.add_perm('ihunt.delete_unlock', is_admin_for_clue)


@rules.predicate
def is_user_for_userdata(user, userdata):
    return user is userdata.user

rules.add_perm('ihunt.change_userdata', is_user_for_userdata)
rules.add_perm('ihunt.delete_userdata', is_user_for_userdata)


@rules.predicate
def is_user_for_teamdata(user, teamdata):
    return user in teamdata.team.users

rules.add_perm('ihunt.change_teamdata', is_user_for_teamdata)
rules.add_perm('ihunt.delete_teamdata', is_user_for_teamdata)
