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


from accounts.models import UserProfile
from .models import Team


class TeamMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.team = None

        if not request.user.is_authenticated:
            return

        (user, _) = UserProfile.objects.get_or_create(user=request.user)

        if request.tenant is not None:
            try:
                request.team = user.teams.get(at_event=request.tenant)
            except Team.DoesNotExist:
                request.team = None
                # TODO: User has no team for this event. Redirect to team creation?
                pass
            return
