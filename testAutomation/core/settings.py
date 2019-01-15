import os
from ast import literal_eval

import dj_database_url
import django_cache_url


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONF_DIR = os.path.abspath(os.path.join(BASE_DIR, 'conf'))

SECRET_KEY = os.environ.get('SECRET_KEY', 'replace_me_please')

DEBUG = bool(os.environ.get('DEBUG', False))

AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'landing'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
INCUNA_AUTH_LOGIN_FORM = 'users.forms.SignInForm'
INCUNA_PASSWORD_RESET_FORM = 'users.forms.PasswordResetForm'
DUM_VALIDATE_EMAIL_SUBJECT = 'Welcome to the Global Grant Community'

CSRF_COOKIE_SECURE = bool(os.environ.get('CSRF_COOKIE_SECURE', not DEBUG))

ALLOWED_HOSTS = [host for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host]

DATABASES = {'default': dj_database_url.config(default='postgres:///gfgp')}
DATABASES['default']['ATOMIC_REQUESTS'] = True

CACHES = {'default': django_cache_url.config()}

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_FILE_PATH = os.environ.get('EMAIL_FILE_PATH', 'tmp')

COMPRESS_ENABLED = bool(os.environ.get('COMPRESS_ENABLED', not DEBUG))

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'admin@incuna.com')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
MANAGERS = ADMINS = (('Incuna error reporting', 'bugs+gfgp@incuna.com'),)
DEFAULT_SUBSCRIPTION_FROM_EMAIL = os.environ.get(
    'DEFAULT_SUBSCRIPTION_FROM_EMAIL',
    'gfgpcommunitybilling@aasciences.ac.ke'
)

EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
SESSION_COOKIE_SECURE = bool(os.environ.get('SESSION_COOKIE_SECURE', not DEBUG))

SITE_ID = 1

INSTALLED_APPS = (
    # Core project app
    'core',
    'surveys',
    'users',
    'documents',
    'subscriptions',

    # Third party
    'bleach',
    'captcha',
    'compressor',
    'countries',
    'crispy_forms',
    'django_extensions',
    'feincms',
    'feincms.module.medialibrary',
    'feincms.module.page',
    'feincms_extensions',
    'incuna_auth',
    'mptt',
    'raven.contrib.django.raven_compat',
    'orderable',
    'rest_framework',
    'rolepermissions',
    # 'rewrite_external_links',
    'tinymce',
    'user_management.ui',
    'django_celery_results',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # `debug_toolbar` expect to be loaded after `django.contrib.staticfiles`
    'debug_toolbar',
)

if os.environ.get('DISABLE_TOOLBAR'):
    INTERNAL_IPS = ['']
else:
    INTERNAL_IPS = ['127.0.0.1']

MIGRATION_MODULES = {
    'page': 'core.projectmigrations.page',
    'medialibrary': 'core.projectmigrations.medialibrary',
    'countries': 'core.projectmigrations.countries',
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'rewrite_external_links.middleware.RewriteExternalLinksMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',

)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

DEFAULT_AUTHENTICATION_CLASSES = os.environ.get(
    'DEFAULT_AUTHENTICATION_CLASSES',
    'rest_framework.authentication.SessionAuthentication',
).split(',')

DEFAULT_RENDERER_CLASSES = os.environ.get(
    'DEFAULT_RENDERER_CLASSES',
    'rest_framework.renderers.JSONRenderer',
).split(',')

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDERER_CLASSES,
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': DEFAULT_AUTHENTICATION_CLASSES,
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'logins': os.environ.get('LOGIN_RATE_LIMIT', '10/hour',),
        'passwords': os.environ.get('PASSWORD_RATE_LIMIT', '10/hour',),
    },
}
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += (
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'feincms.context_processors.add_page_if_missing',
            ],
            'debug': bool(os.environ.get('TEMPLATE_DEBUG', DEBUG)),
        },
    },
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

WSGI_APPLICATION = 'core.wsgi.application'

TIME_ZONE = 'UTC'
LANGUAGES = (('en-gb', 'English'),)
LANGUAGE_CODE = 'en-gb'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

AWS_SES_ACCESS_KEY_ID = os.environ.get('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = os.environ.get('AWS_SES_SECRET_ACCESS_KEY')

AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION_NAME')
AWS_SES_REGION_ENDPOINT = os.environ.get('AWS_SES_REGION_ENDPOINT')

# Static / client media settings for  for `django-storages` support
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_LOCATION = os.environ.get('AWS_LOCATION')
DEFAULT_FILE_STORAGE = os.environ.get(
    'DEFAULT_FILE_STORAGE',
    'django.core.files.storage.FileSystemStorage',
)
STATICFILES_STORAGE = os.environ.get(
    'STATICFILES_STORAGE',
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
)

STATIC_ROOT_DEFAULT = os.path.join(BASE_DIR, 'static_media')

STATIC_ROOT = os.environ.get('STATIC_ROOT', STATIC_ROOT_DEFAULT)

STATIC_URL = os.environ.get('STATIC_URL', '/static/')

MEDIA_ROOT_DEFAULT = os.path.join(BASE_DIR, 'client_media')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', MEDIA_ROOT_DEFAULT)
MEDIA_URL = os.environ.get('MEDIA_URL', '/client/')

TEST_RUNNER = 'core.runner.TestRunner'

# Used by frontend in development mode
FEATURE_STYLE_GUIDE = os.environ.get('FEATURE_STYLE_GUIDE', DEBUG)
FEATURE_MORE_INFORMATION = bool(os.environ.get('FEATURE_MORE_INFORMATION', False))

# Bleach
BLEACH_ALLOWED_TAGS = [
    'p', 'b', 'i', 'u', 'em', 'strike', 'strong', 'a', 'ul', 'li', 'ol', 'sup',
    'sub', 'div', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
]
BLEACH_STRIP_TAGS = True


TINYMCE_TOOLBAR = (
    'insertfile undo redo | styleselect | bold italic | ' +
    'alignleft aligncenter alignright alignjustify | ' +
    'bullist numlist outdent indent | link | media'
)
TINYMCE_JS_URL = '//cdn.tinymce.com/4/tinymce.min.js'
TINYMCE_DEFAULT_CONFIG = {
    'height': '300',
    'plugins': 'fullscreen paste link media',
    'paste_auto_cleanup_on_paste': True,
    'relative_urls': False,
    'invalid_elements': 'script',
    'statusbar': False,
    'menubar': False,
    'toolbar': TINYMCE_TOOLBAR,
}

RAVEN_CONFIG = {
    'dsn': os.environ.get('RAVEN_DSN'),
    'environment': os.environ.get('RAVEN_ENVIRONMENT', 'localhost'),
    'release': os.environ.get('DISTELLI_RELREVISION'),
}

CRISPY_TEMPLATE_PACK = 'bootstrap4'
ROLEPERMISSIONS_MODULE = 'core.roles'

RECAPTCHA_PUBLIC_KEY = os.environ.get(
    'RECAPTCHA_PUBLIC_KEY',
    '6LcxVlYUAAAAAOvNcWxxdABqps_N8u4OEj3nu91T',
)
RECAPTCHA_PRIVATE_KEY = os.environ.get(
    'RECAPTCHA_PRIVATE_KEY',
    '6LcxVlYUAAAAAP6KvQiaduPeSRpFIUubQWRlSmH0',
)
NOCAPTCHA = True
DISABLE_RECAPTCHA = bool(os.environ.get('DISABLE_RECAPTCHA', False))


# Celery settings
BROKER_URL = os.environ.get('BROKER_URL', 'amqp://guest:guest@localhost//')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', BROKER_URL)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

BROKER_TRANSPORT_OPTIONS = {
    # Specify region for AWS SQS
    'region': os.environ.get('AWS_SQS_REGION_NAME', 'eu-west-1')
}
SQS_QUEUE_NAME = os.environ.get('SQS_QUEUE_NAME')
if SQS_QUEUE_NAME:
    CELERY_DEFAULT_QUEUE = SQS_QUEUE_NAME

CELERY_ENABLE_REMOTE_CONTROL = bool(literal_eval(
    os.environ.get('CELERY_ENABLE_REMOTE_CONTROL', 'True')
))
CELERY_SEND_EVENTS = os.environ.get('CELERY_SEND_EVENTS', 'False')
CELERYD_SEND_EVENTS = bool(literal_eval(os.environ.get(
    'CELERYD_SEND_EVENTS',
    CELERY_SEND_EVENTS,
)))

CELERY_TASK_ALWAYS_EAGER = bool(os.environ.get('CELERY_TASK_ALWAYS_EAGER', DEBUG))
CELERY_TASK_EAGER_PROPAGATES = bool(os.environ.get(
    'CELERY_TASK_EAGER_PROPAGATES',
    DEBUG,
))

SITE_SUBSCRIPTION = {
    'price': 1500.00,
    'renewal_reminder_days': 30
}
