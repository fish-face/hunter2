from .utils import load_or_create_secret_key
import environ
import logging

# Load the current environment profile
root = environ.Path(__file__) - 2
env = environ.Env()

# Default settings which should be overridden by environment variables
DEBUG              = env.bool      ('H2_DEBUG',         default=False)
DEFAULT_URL_SCHEME = env.str       ('H2_SCHEME',        default='http')
LOG_LEVEL          = env.str       ('H2_LOG_LEVEL',     default='WARNING')
LANGUAGE_CODE      = env.str       ('H2_LANGUAGE_CODE', default='en-gb')
PIWIK_DOMAIN_PATH  = env.str       ('H2_PIWIK_HOST',    default=None)
PIWIK_SITE_ID      = env.str       ('H2_PIWIK_SITE',    default='1')
TIME_ZONE          = env.str       ('H2_TIME_ZONE',     default='Europe/London')
ALLOWED_HOSTS      = env.list      ('H2_ALLOWED_HOSTS', default=['*'])
INTERNAL_IPS       = env.list      ('H2_INTERNAL_IPS',  default=['127.0.0.1'])
EMAIL_CONFIG       = env.email_url ('H2_EMAIL_URL',     default='smtp://localhost:25')
EMAIL_DOMAIN       = env.str       ('H2_EMAIL_DOMAIN',  default='hunter2.local')
ADMINS             = env.list      ('H2_ADMINS',        default=[])
RAVEN_DSN          = env.str       ('H2_SENTRY_DSN',    default=None)
SENDFILE_BACKEND   = env.str       ('H2_SENDFILE',      default='sendfile.backends.development')

DATABASES = {
    'default': env.db('H2_DATABASE_URL', default="postgres://postgres:postgres@db:5432/postgres")
}
CACHES = {
    'default': env.cache_url('H2_CACHE_URL', default="dummycache://" )
}
USE_SILK = DEBUG and env.bool('H2_SILK', default=False)

if USE_SILK:  # nocover
    try:
        import silk  # noqa: F401
    except ImportError:
        logging.error("Silk profiling enabled but not available. Check REQUIREMENTS_VERSION is set to development at build time.")
        USE_SILK = False

# Generate a secret key and store it the first time it is accessed
SECRET_KEY = load_or_create_secret_key("/config/secrets.ini")

# Load the email configuration
vars().update(EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = f'webmaster@{EMAIL_DOMAIN}'

SERVER_EMAIL = f'root@{EMAIL_DOMAIN}'

# Application definition
BASE_DIR = root()

ACCOUNT_ACTIVATION_DAYS = 7

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_EMAIL_VERIFICATION = 'none'

ACCOUNT_SIGNUP_FORM_CLASS = 'accounts.forms.UserProfileForm'

AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
    'rules.permissions.ObjectPermissionBackend',
)

DATABASES['default']['ATOMIC_REQUESTS'] = True

DEBUG_TOOLBAR_PATCH_SETTINGS = False

FULLCLEAN_WHITELIST = [
    'events',
    'hunts',
    'teams',
]

INSTALLED_APPS = (
    # Our apps first to allow us to override third party templates
    # These are in dependency order
    'accounts',
    'events',
    'teams',
    'hunts',
    'hunter2',
    # Third party apps
    # These are in alphabetical order
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.openid',
    'analytical',
    'dal',
    'dal_select2',
    'debug_toolbar',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_fullclean',
    'nested_admin',
    'raven.contrib.django.raven_compat',
    'rules.apps.AutodiscoverRulesConfig',
    'solo',
    'sortedm2m',
    'subdomains',
    'url_tools',
)
if USE_SILK:  # nocover
    INSTALLED_APPS = INSTALLED_APPS + ('silk',)

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
            'level': LOG_LEVEL,
        },
        'django.db': {
        },
    },
}

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/accounts/login/'

MEDIA_ROOT = '/uploads/'

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
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'subdomains.middleware.SubdomainMiddleware',
    'events.middleware.EventMiddleware',
    'teams.middleware.TeamMiddleware',
)
if USE_SILK:  # nocover
    MIDDLEWARE = ('silk.middleware.SilkyMiddleware',) + MIDDLEWARE

if RAVEN_DSN:  # nocover
    RAVEN_CONFIG = {
        'dsn': RAVEN_DSN
    }

ROOT_URLCONF = 'hunter2.urls'

SOCIALACCOUNT_AUTO_SIGNUP = False

SOCIALACCOUNT_PROVIDERS = {
    'openid': {
        'SERVERS': [{
            'id': 'steam',
            'name': 'Steam',
            'openid_url': 'https://steamcommunity.com/openid',
            'stateless': True,
        }]
    }
}

STATIC_ROOT = '/static/'

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    'hunter2/static',
    'hunts/static',
)

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SENDFILE_ROOT = '/uploads'

SENDFILE_URL = '/media'

SITE_ID = 1

SUBDOMAIN_URLCONFS = {
    'admin': 'hunter2.urls.admin',
    'www': 'hunter2.urls.www',
}

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
                'teams.context_processors.event_team',
                'hunts.context_processors.announcements',
            ],
        },
    },
]

TEST_RUNNER = 'hunter2.tests.TestRunner'

USE_I18N = True

USE_L10N = True

USE_TZ = True

WSGI_APPLICATION = 'hunter2.wsgi.application'

X_FRAME_OPTIONS = 'DENY'

if USE_SILK:  # nocover
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    # Well, the following path is rubbish but I cba doing it properly for now
    SILKY_PYTHON_PROFILER_RESULT_PATH = '/uploads/events/'
