from urlparse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def validate_settings():
    """
    Validate that if not in DEBUG mode, key settings have been changed.
    """
    if settings.DEBUG or settings.IN_TEST_SUITE:
        return

    # Things that values must not be.
    for key, value in [
            ('SECRET_KEY', 'please change this'),
            ('SESSION_COOKIE_SECURE', False),
            ('APP_PURCHASE_SECRET', 'please change this')]:
        if getattr(settings, key) == value:
            raise ImproperlyConfigured('{0} must be changed from default'
                                       .format(key))

    for key in ('CSP_IMG_SRC', 'CSP_MEDIA_SRC', 'CSP_SCRIPT_SRC'):
        for url in getattr(settings, key):
            # We will allow loading of resources from the current site.
            if url.startswith('http://') and url != settings.SITE_URL:
                raise ImproperlyConfigured('{0} has a http URL: {1}'
                                           .format(key, url))


def static_url(url):
    """
    Return the relevant URL from settings. Rather than rely on
    a complicated layer of settings to do their work, this just does
    it at runtime. This allows MEDIA_URL, STATIC_URL and VAMO_URL to be
    changed in a local settings file, without having to overidde all the
    URLs.

    If the URL starts with https:// or http://, then no changes are made.
    """
    prefix = {
        'ADDON_ICONS_DEFAULT_URL': settings.MEDIA_URL,
        'ADDON_ICON_URL': settings.STATIC_URL,
        'PREVIEW_THUMBNAIL_URL': settings.STATIC_URL,
        'PREVIEW_FULL_URL': settings.STATIC_URL,
        'PRODUCT_ICON_URL': settings.MEDIA_URL,
        'WEBAPPS_RECEIPT_URL': settings.SITE_URL
    }

    value = getattr(settings, url)
    if value.startswith(('https://', 'http://')):
        return value
    if settings.DEBUG and settings.SERVE_TMP_PATH:
        value = '/' + value if not value.startswith('/') else value
        return urljoin(prefix[url], '/tmp' + value)
    return urljoin(prefix[url], value)


def update_csp():
    """
    After settings, including DEBUG has loaded, see if we need to update CSP.
    """
    for key in ('CSP_IMG_SRC', 'CSP_MEDIA_SRC', 'CSP_SCRIPT_SRC'):
        values = getattr(settings, key)
        new = set()
        for value in values:
            # If we are in debug mode, mirror any HTTPS resources as a
            # HTTP url.
            if value.startswith('https://') and settings.DEBUG:
                res = value.replace('https://', 'http://')
                for v in value, res:
                    new.add(v)
                continue
            # If there's a HTTP url in there and we are not in debug mode
            # don't add it in.
            elif value.startswith('http://') and not settings.DEBUG:
                continue
            # Add in anything like 'self'.
            else:
                new.add(value)

        setattr(settings, key, tuple(new))
