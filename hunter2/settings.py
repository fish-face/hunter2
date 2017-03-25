from .local import *

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Application definition
ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = (
    'social_core.backends.steam.SteamOpenId',
    'django.contrib.auth.backends.ModelBackend',
    'rules.permissions.ObjectPermissionBackend',
)

DEBUG_TOOLBAR_PATCH_SETTINGS = False

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'nested_admin',
    'rules.apps.AutodiscoverRulesConfig',
    'social_django',
    'sortedm2m',
    'subdomains',
    'events',
    'teams',
    'hunts',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'django.db': {
        },
    },
}

LOGIN_URL = '/login/'

MEDIA_ROOT = '/storage/media/'

MEDIA_URL = '/media/'

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'subdomains.middleware.SubdomainURLRoutingMiddleware',
    'django.middleware.common.CommonMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'events.middleware.EventMiddleware',
    'teams.middleware.TeamMiddleware',
)

ROOT_URLCONF = 'hunter2.urls'

STATIC_ROOT = '/storage/static/'

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    'hunter2/static',
)

TEMPLATES = [
    {
        'APP_DIRS': True,
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'hunter2/templates',
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'teams.context_processors.event_team',
            ],
        },
    },
]

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SITE_ID = 1

SUBDOMAIN_URLCONFS = {
    'admin': 'hunter2.urls.admin',
    'www': 'hunter2.urls.www',
}

USE_I18N = True

USE_L10N = True

USE_TZ = True

WSGI_APPLICATION = 'hunter2.wsgi.application'

X_FRAME_OPTIONS = 'DENY'
