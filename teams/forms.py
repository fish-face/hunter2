from dal import autocomplete
from django import forms
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory, modelform_factory
from . import models

UserForm = modelform_factory(User, fields=('email', ))

UserProfileFormset = inlineformset_factory(User, models.UserProfile, fields=('seat', ), can_delete=False)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ['seat']

    field_order = ['username', 'email', 'password1', 'password2', 'seat']

    def signup(self, request, user):
        user.profile = models.UserProfile(user=user)
        user.profile.seat = self.cleaned_data['seat']
        user.profile.save()
        user.save()


class InviteForm(forms.Form):
    user = forms.ModelChoiceField(
        label='Search for a user:',
        queryset=models.UserProfile.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='userprofile_autocomplete',
            attrs={
                'data-minimum-input-length': 1,
            },
        ),
    )


class RequestForm(forms.Form):
    team = forms.ModelChoiceField(
        label='Search for a team:',
        queryset=models.Team.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='team_autocomplete',
            attrs={
                'data-minimum-input-length': 1,
            },
        ),
    )


class CreateTeamForm(forms.ModelForm):
    """Teams are never really created explicitly. Creating a team really means giving a name to your team."""
    class Meta:
        model = models.Team
        fields = ['name']
        labels = {
            'name': 'Choose a name for your team:',
        }


class TeamForm(forms.ModelForm):
    # Hidden unless someone tries to add someone who's already on a team
    move_user = forms.BooleanField(required=False, widget=forms.HiddenInput(), label="Yes, move user")
    scrub_help_text_fields = ('members', 'invites', 'requests')

    class Meta:
        model = models.Team
        fields = ('name', 'at_event', 'members', 'move_user', 'invites', 'requests')
        widgets = {
            'members': autocomplete.ModelSelect2Multiple(
                url='userprofile_autocomplete',
                attrs={'data-minimum-input-length': 1}
            ),
            'invites': autocomplete.ModelSelect2Multiple(
                url='userprofile_autocomplete',
                attrs={'data-minimum-input-length': 1}
            ),
            'requests': autocomplete.ModelSelect2Multiple(
                url='userprofile_autocomplete',
                attrs={'data-minimum-input-length': 1}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.base_fields:
            if field in self.scrub_help_text_fields:
                self.fields[field].help_text = ''

    def clean(self, **kwargs):
        cleaned_data = super().clean(**kwargs)

        # We are going to check if the admin is moving members. But only if there are no other errors.
        if self.errors:
            return cleaned_data

        members = cleaned_data.get('members')
        teams = models.Team.objects.filter(at_event=cleaned_data.get('at_event'))
        if self.instance.pk:
            teams = teams.exclude(pk=self.instance.pk)

        moved_members = []
        moved_from = []
        for member in members:
            other_teams = teams.filter(members=member)
            if other_teams.exists():
                moved_members.append(member)
                moved_from.append(other_teams.first())

        if moved_members:
            # User has ticked confirmation checkbox, move those d00ds
            # TODO: executing the move in the clean() method is not "correct" but it works.
            # Probably the change should be happening in the model or signal handler instead of the ValidationError
            # and the form would just control the confirmation checkbox.
            if cleaned_data.get('move_user'):
                for user, team in zip(moved_members, moved_from):
                    team.members.remove(user)
                    if team.members.count() > 0:
                        team.save()
                    else:
                        team.delete()
                return cleaned_data

            self.fields['move_user'].widget = forms.CheckboxInput()
            if len(moved_members) > 1:
                self.fields['move_user'].label = "Yes, move users"
                this_user = "these users have"
            else:
                this_user = "this user has"
            member_string = ', '.join(['%s (already on %s)' % (user.user.username, team.name)
                                       for user, team in zip(moved_members, moved_from)])
            self.add_error('move_user',
                           'You are trying to add %s to this team. Are you sure you want'
                           ' to do this? Note! If %s already answered questions, this '
                           'will most likely alter the respective teams\' progress!' %
                           (member_string, this_user))
