import logging

from .base import *  # noqa


# Disable logging and traceback in unit tests for readability.
# https://docs.python.org/3/library/logging.html#logging.disable
logging.disable(logging.CRITICAL)

# `ManifestStaticFilesStorage` (used in base settings) requires `collectstatic` to be run.
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
COMPRESS_OFFLINE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
