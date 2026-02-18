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

# Ensure Django knows about additional language codes we use for translations.
# Some Django distributions may not include smaller language codes (eg. 'am',
# 'ti', 'om') in LANG_INFO. Add safe entries and ensure they appear in
# `LANGUAGES` so modeltranslation/admin won't raise KeyError.
try:
    from django.conf.locale import LANG_INFO as _DJANGO_LANG_INFO
    _DJANGO_LANG_INFO.update(
        {
            "am": {"bidi": False, "code": "am", "name": "Amharic", "name_local": "\u12a0\u121b\u122d\u129b\u1295"},
            "ti": {"bidi": False, "code": "ti", "name": "Tigrinya", "name_local": "\u1275\u1303\u1309\u122a\u1229\u1295"},
            "om": {"bidi": False, "code": "om", "name": "Oromo", "name_local": "Afaan Oromo"},
        }
    )
except Exception:
    # If LANG_INFO is unavailable for some reason, continue without failing.
    pass

# Ensure these languages are present in the `LANGUAGES` setting so admin
# and modeltranslation present them in forms.
_extra_langs = [("am", "Amharic"), ("ti", "Tigrinya"), ("om", "Oromo")]
try:
    LANGUAGES = list(LANGUAGES)
except Exception:
    LANGUAGES = []
for _code, _name in _extra_langs:
    if not any(_code == c for c, _ in LANGUAGES):
        LANGUAGES.append((_code, _name))

#
# General Django development settings
#
PROJECT_NAME = "my_geonode"

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith("/"):
    SITEURL = f"{SITEURL}/"

SITENAME = os.getenv("SITENAME", "my_geonode")

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

WSGI_APPLICATION = f"{PROJECT_NAME}.wsgi.application"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
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
# - Ensure project static dir (/usr/src/my_geonode/static) is included so CRA build is found
# Project package root (e.g., /usr/src/my_geonode)
# LOCAL_ROOT points to /usr/src/my_geonode/src/my_geonode — go up two levels to reach /usr/src/my_geonode
_PROJECT_PACKAGE_ROOT = os.path.abspath(os.path.join(LOCAL_ROOT, os.pardir, os.pardir))
_PROJECT_STATIC_DIR = os.path.join(_PROJECT_PACKAGE_ROOT, "static")  # /usr/src/my_geonode/static
_LOCAL_APP_STATIC_DIR = os.path.join(LOCAL_ROOT, "static")  # /usr/src/my_geonode/my_geonode/static
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
    "django.template.context_processors.request",  # Add this line
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    "geonode.context_processors.resource_urls",
    "geonode.themes.context_processors.custom_theme",
]


# Add your custom middleware
MIDDLEWARE = list(MIDDLEWARE)  # Convert the tuple to a list
MIDDLEWARE.insert(1, 'corsheaders.middleware.CorsMiddleware')  # Insert after SecurityMiddleware

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

# Add your specific LDAP configuration after this comment:
# https://docs.geonode.org/en/master/advanced/contrib/#configuration

# --- Your Custom App Settings ---
# CORS Settings for your React Frontend
CORS_ALLOW_ALL_ORIGINS = True

# Email configuration for sending advisories (pulled from environment variables)
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
#! Change
# Use BASE_URL from the environment, defaulting if not present
BASE_URL = os.getenv("NGINX_BASE_URL", "http://localhost:3500")

# Use MEDIA_URL and MEDIA_ROOT from the environment, if available
# This avoids hardcoding paths and respects the Docker volumes
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, 'media'))

LANGUAGES = [
    ("en", "English"),
    ("am", "Amharic"),
    ("ti", "Tigrinya"),
    ("om", "Oromo"),
]

MODELTRANSLATION_LANGUAGES = ("en", "am", "ti", "om")
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
# Restrict modeltranslation loading to project app translations only.
# This prevents GeoNode core models (e.g. layers_dataset) from requiring
# *_am/*_ti/*_om DB columns that are not present in this deployment.
MODELTRANSLATION_TRANSLATION_FILES = ("info_hub.translation",)

# Defensive monkey-patch: some deployments/Django builds may not include
# complete entries for smaller language codes in Django's LANG_INFO map.
# modeltranslation calls `get_language_bidi()` which currently bubbles a
# KeyError for unknown codes (eg. 'am'). Patch `modeltranslation.utils`
# early so admin form construction won't raise when an unexpected code is
# encountered. This is safe and reversible; it treats unknown languages as
# non-bidi by default.
try:
    import modeltranslation.utils as _mt_utils

    _mt_original_get_language_bidi = getattr(_mt_utils, "get_language_bidi", None)

    if _mt_original_get_language_bidi:
        def _mt_safe_get_language_bidi(lang: str) -> bool:
            try:
                return _mt_original_get_language_bidi(lang)
            except KeyError:
                return False

        _mt_utils.get_language_bidi = _mt_safe_get_language_bidi
except Exception:
    # Do not fail settings import if modeltranslation isn't available yet
    pass

