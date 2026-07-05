# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Django settings for the GeoNode project.
import os
import sys
import ast
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "django,localhost").split(",")

LOCAL_ROOT = os.path.dirname(os.path.abspath(__file__))
print("🧭 LOCAL_ROOT:", LOCAL_ROOT)
print("📁 Template DIRS will include:", os.path.join(LOCAL_ROOT, "templates"))


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(BASE_DIR, 'my_geonode'))

# Python 3 imports only (remove Python 2 fallback)
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen, Request

# Always import base GeoNode settings first
from geonode.settings import *

# Load local settings which can override the base settings
try:
    from my_geonode.local_settings import *
except ImportError:
    pass  # It's okay if local_settings.py doesn't exist, use defaults

# Default languages
LANGUAGES = (
    ('en', 'English'),
)

#
# General Django development settings
#
PROJECT_NAME = "my_geonode"

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith("/"):
    SITEURL = f"{SITEURL}/"

SITENAME = os.getenv("SITENAME", "my_geonode")

# Defines the directory that contains the settings file as the LOCAL_ROOT
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

WSGI_APPLICATION = f"{PROJECT_NAME}.wsgi.application"

# Language code for this installation.
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en")

if PROJECT_NAME not in INSTALLED_APPS:
    INSTALLED_APPS += (PROJECT_NAME,)

INSTALLED_APPS += (
    'info_hub.apps.InfoHubConfig',
    'subscribers',
    'contact',
)

# Location of url mappings
ROOT_URLCONF = os.getenv("ROOT_URLCONF", f"{PROJECT_NAME}.urls")

# Additional directories which hold static files
_PROJECT_PACKAGE_ROOT = os.path.abspath(os.path.join(LOCAL_ROOT, os.pardir, os.pardir))
_PROJECT_STATIC_DIR = os.path.join(_PROJECT_PACKAGE_ROOT, "static")
_LOCAL_APP_STATIC_DIR = os.path.join(LOCAL_ROOT, "static")
STATICFILES_DIRS = [
    _PROJECT_STATIC_DIR,
    _LOCAL_APP_STATIC_DIR,
] + STATICFILES_DIRS

# Location of locale files
LOCALE_PATHS = (os.path.join(LOCAL_ROOT, "locale"),) + LOCALE_PATHS

TEMPLATES[0]["DIRS"].insert(0, os.path.join(LOCAL_ROOT, "templates"))
loaders = TEMPLATES[0]["OPTIONS"].get("loaders") or [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
TEMPLATES[0]["OPTIONS"]["loaders"] = loaders
TEMPLATES[0].pop("APP_DIRS", None)

TEMPLATES[0]["OPTIONS"]["context_processors"] = [
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.tz",
    "django.template.context_processors.request",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    "geonode.context_processors.resource_urls",
    "geonode.themes.context_processors.custom_theme",
    # Provides GEOSERVER_PUBLIC_LOCATION / GEOSERVER_BASE_URL to templates.
    # Required by the MapStore client config (_geonode_config.html); without it
    # geoServerPublicLocation is empty and the auth rule becomes urlPattern '.*',
    # which breaks MapStore plugin/resource loading (blank homepage & catalogue).
    "geonode.geoserver.context_processors.geoserver_urls",
]


# Add your custom middleware
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, 'corsheaders.middleware.CorsMiddleware')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d "
                      "%(thread)d %(message)s"
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "geonode": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "geoserver-restconfig.catalog": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "owslib": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "pycsw": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "celery": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "mapstore2_adapter.plugins.serializers": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "geonode_logstash.logstash": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

USER_ANALYTICS_ENABLED = ast.literal_eval(os.getenv("USER_ANALYTICS_ENABLED", "False"))

CENTRALIZED_DASHBOARD_ENABLED = ast.literal_eval(
    os.getenv("CENTRALIZED_DASHBOARD_ENABLED", "False")
)

if (
    CENTRALIZED_DASHBOARD_ENABLED
    and USER_ANALYTICS_ENABLED
    and "geonode_logstash" not in INSTALLED_APPS
):
    INSTALLED_APPS += ("geonode_logstash",)

    CELERY_BEAT_SCHEDULE["dispatch_metrics"] = {
        "task": "geonode_logstash.tasks.dispatch_metrics",
        "schedule": 3600.0,
    }

LDAP_ENABLED = ast.literal_eval(os.getenv("LDAP_ENABLED", "False"))
if LDAP_ENABLED and "geonode_ldap" not in INSTALLED_APPS:
    INSTALLED_APPS += ("geonode_ldap",)

# --- Your Custom App Settings ---
CORS_ALLOW_ALL_ORIGINS = True

# Email configuration
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", DEFAULT_FROM_EMAIL or EMAIL_HOST_USER)

# --------------------------------
BASE_URL = os.getenv("NGINX_BASE_URL", "http://localhost:3500")

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, 'media'))

# Language settings
# Django's bundled LANG_INFO doesn't include the Ethiopian language codes we use
# (am/om/ti). modeltranslation's admin calls get_language_bidi(), which raises
# KeyError for unknown codes, so register safe entries for them first.
try:
    from django.conf.locale import LANG_INFO as _DJANGO_LANG_INFO
    _DJANGO_LANG_INFO.setdefault("am", {"bidi": False, "code": "am", "name": "Amharic", "name_local": "አማርኛ"})
    _DJANGO_LANG_INFO.setdefault("om", {"bidi": False, "code": "om", "name": "Oromo", "name_local": "Afaan Oromoo"})
    _DJANGO_LANG_INFO.setdefault("ti", {"bidi": False, "code": "ti", "name": "Tigrinya", "name_local": "ትግርኛ"})
except Exception:
    pass

LANGUAGES = [
    ("en", "English"),
    ("am", "Amharic"),
    ("om", "Oromo"),
    ("ti", "Tigrinya"),
]

# modeltranslation: scoped to the info_hub app ONLY, so it never tries to add
# *_am/*_om/*_ti columns to GeoNode's core models (that is what broke earlier).
MODELTRANSLATION_LANGUAGES = ("en", "am", "om", "ti")
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_TRANSLATION_FILES = ("info_hub.translation",)
# NOTE: do NOT import modeltranslation here. Importing modeltranslation.* during
# settings load computes its AVAILABLE_LANGUAGES before MODELTRANSLATION_LANGUAGES
# is visible, caching the full ~100-language Django default. The LANG_INFO entries
# added above are what keep get_language_bidi() from raising on am/om/ti.
