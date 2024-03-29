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

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django_tenants.middleware import TenantMainMiddleware

from accounts.models import UserInfo, UserProfile


class EventMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.tenant is not None:
            UserProfile.objects.get_or_create(user=request.user)
            (user, _) = UserInfo.objects.get_or_create(user=request.user)
            user.attendance_set.get_or_create(
                user_info=request.user.info,
                event=request.tenant,
            )
        return


class TenantMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        try:
            super().process_request(request)
        except self.TENANT_NOT_FOUND_EXCEPTION:
            connection.set_schema_to_public()
            request.tenant = None
            if hasattr(settings, 'PUBLIC_SCHEMA_URLCONF'):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF

            # This path bypasses the cache clear in the superclass
            ContentType.objects.clear_cache()
