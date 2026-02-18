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

"""
WSGI config for my_geonode project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_geonode.settings")

# Ensure Django's LANG_INFO contains smaller language codes we need
try:
	from django.conf import locale as _dj_locale

	_dj_lang_info = getattr(_dj_locale, "LANG_INFO", None)
	if _dj_lang_info is not None:
		_dj_lang_info.update(
			{
				"am": {
					"bidi": False,
					"code": "am",
					"name": "Amharic",
					"name_local": "\u12a0\u121b\u122d\u129b\u1295",
				},
				"ti": {
					"bidi": False,
					"code": "ti",
					"name": "Tigrinya",
					"name_local": "\u1275\u1303\u1309\u122a\u1229\u1295",
				},
				"om": {
					"bidi": False,
					"code": "om",
					"name": "Oromo",
					"name_local": "Afaan Oromo",
				},
			}
		)
except Exception:
	pass
# Defensive monkey-patch for modeltranslation language bidi lookup.
# Some Django distributions may not include entries for smaller language
# codes (e.g. 'am'). Patch `modeltranslation.utils.get_language_bidi` here
# at WSGI startup so it is in effect before Django/ModelTranslation build
# ModelAdmin forms which call it.
try:
	import modeltranslation.utils as _mt_utils

	_mt_orig = getattr(_mt_utils, "get_language_bidi", None)

	if _mt_orig:
		def _mt_safe_get_language_bidi(lang: str) -> bool:
			try:
				return _mt_orig(lang)
			except KeyError:
				return False

		_mt_utils.get_language_bidi = _mt_safe_get_language_bidi
		# Also patch modeltranslation.admin where the function may have been
		# imported directly (``from modeltranslation.utils import get_language_bidi``)
		try:
			import modeltranslation.admin as _mt_admin

			if hasattr(_mt_admin, "get_language_bidi"):
				_mt_admin.get_language_bidi = _mt_safe_get_language_bidi
		except Exception:
			pass
except Exception:
	# If modeltranslation isn't installed yet or import fails, continue.
	pass

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
