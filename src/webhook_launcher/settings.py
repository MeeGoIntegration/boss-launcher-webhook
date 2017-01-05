# Copyright (C) 2013 Jolla Ltd.
# Contact: Islam Amer <islam.amer@jollamobile.com>
# All rights reserved.
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from os.path import abspath, dirname, join
import struct,socket
PROJECT_DIR = dirname(__file__)

WEBHOOKCONF="/etc/skynet/webhook.conf"

import ConfigParser
config = ConfigParser.ConfigParser()
try:
    config.readfp(open(WEBHOOKCONF))
except Exception:
    try:
        # during docs build
        config.readfp(open("src/webhook_launcher/webhook.conf"))
    except IOError:
        # when developing it is in cwd
        config.readfp(open("webhook.conf"))

URL_PREFIX = config.get('web', 'url_prefix')
static_media_collect = config.get('web', 'static_media_collect')

DEFAULT_PROJECT = ""
if config.has_option('web', 'default_project'):
    DEFAULT_PROJECT = config.get('web', 'default_project')

USE_REMOTE_AUTH = config.getboolean('web', 'use_http_remote_user')

PUBLIC_LANDING_PAGE = False
if config.has_option('web', 'public_landing_page'):
    PUBLIC_LANDING_PAGE = config.getboolean('web', 'public_landing_page')

SERVICE_WHITELIST = False
if config.has_option('web', 'service_whitelist'):
    SERVICE_WHITELISTt = [ service.strip() for service in config.get('web', 'service_whitelist').split(",") ]

# IP filtering for POST
POST_IP_FILTER = False
POST_IP_FILTER_HAS_REV_PROXY = False
NETMASKS=[]
if config.has_option('web', 'post_ip_filter'):
    POST_IP_FILTER = True
    if config.has_option('web', 'post_ip_filter_has_rev_proxy'):
        POST_IP_FILTER_HAS_REV_PROXY = True
    # http://stackoverflow.com/questions/819355/how-can-i-check-if-an-ip-is-in-a-network-in-python
    # settings.post_ip_filter should be a list of IPs or CIDR (eg
    # 10.0.0.0/24)
    for ip in config.get('web', 'post_ip_filter').split(","):
        ip = ip.strip()
        if "/" in ip :
            ip,bits = ip.split('/')
            bits=int(bits)
        else:
            bits=32
        print "Allow POST from %s / %d" % (ip, bits)
        NETMASKS.append(struct.unpack('<L',socket.inet_aton(ip))[0] & ((2L<<bits-1) - 1))

OUTGOING_PROXY = None
if config.has_option('web', 'outgoing_proxy'):
    OUTGOING_PROXY = config.get('web', 'outgoing_proxy')
    OUTGOING_PROXY_PORT = int(config.get('web', 'outgoing_proxy_port'))

BOSS_HOST = config.get('boss', 'boss_host')
BOSS_USER = config.get('boss', 'boss_user')
BOSS_PASS = config.get('boss', 'boss_pass')
BOSS_VHOST = config.get('boss', 'boss_vhost')

db_engine = config.get('db', 'db_engine')
db_name = config.get('db', 'db_name')
db_user = config.get('db', 'db_user')
db_pass = config.get('db', 'db_pass')
db_host = config.get('db', 'db_host')

VCSCOMMIT_QUEUE = config.get('processes', 'vcscommit_queue')
VCSCOMMIT_NOTIFY = config.get('processes', 'vcscommit_notify')
VCSCOMMIT_BUILD = config.get('processes', 'vcscommit_build')


USE_LDAP = config.getboolean('ldap', 'use_ldap')
USE_SEARCH = config.getboolean('ldap', 'use_search')
if USE_LDAP:

  import ldap
  from django_auth_ldap.config import LDAPSearch
  import logging

  LDAP_SERVER = config.get('ldap', 'ldap_server')
  ldap_verify_cert = config.getboolean('ldap', 'verify_certificate')

  if USE_SEARCH:
    AUTH_LDAP_USER_SEARCH = LDAPSearch( config.get('ldap', 'ldap_base_dn', raw=True),
                                        ldap.SCOPE_SUBTREE,
                                        config.get('ldap', 'ldap_filter', raw=True))
  else:
    AUTH_LDAP_USER_DN_TEMPLATE = config.get('ldap', 'ldap_dn_template', raw=True)

  mail_attr = config.get('ldap', 'ldap_mail_attr', raw=True)
  fname_attr = config.get('ldap', 'ldap_fname_attr', raw=True)
  lname_attr = config.get('ldap', 'ldap_lname_attr', raw=True)
  AUTH_LDAP_USER_ATTR_MAP = {"first_name" : fname_attr, "last_name" : lname_attr, "email":mail_attr}
elif USE_REMOTE_AUTH:
    AUTHENTICATION_BACKENDS = (
        'webhook_launcher.app.models.RemoteStaffBackend',
    )

SECRET_KEY = config.get('web', 'secret_key')

STRICT_MAPPINGS = False
if config.has_option('web', 'strict_mappings'):
    STRICT_MAPPINGS = config.getboolean('web', 'strict_mappings')

DEBUG = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS
DATABASES = {
            'default': {
                'ENGINE' : 'django.db.backends.' + db_engine,
                'NAME' : db_name,
                'USER' : db_user,
                'PASSWORD' : db_pass,
                'HOST' : db_host,
                'PORT' : '',
                }
            }

DATABASE_OPTIONS = {
            "autocommit": True,
            }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

STATIC_ROOT = static_media_collect

#STATIC_ROOT = join(PROJECT_DIR, "site_media")

STATIC_URL = '/' + URL_PREFIX + '/site_media/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
#        'APP_DIRS': True,
        'DIRS': [
                # Put strings here, like "/home/html/django_templates"
                # or "C:/www/django/templates".  Always use forward
                # slashes, even on Windows.  Don't forget to use
                # absolute paths, not relative paths.
                ],
        'OPTIONS': {
             'context_processors': [
                 'django.template.context_processors.debug',
                 'django.template.context_processors.request',
                 "django.contrib.auth.context_processors.auth",
                 "django.template.context_processors.i18n",
                 "django.template.context_processors.media",
                 "django.template.context_processors.static",
                 'django.contrib.auth.context_processors.auth',
                 'django.contrib.messages.context_processors.messages',
             ],
             # List of callables that know how to import templates
             # from various sources.
             'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                #'django.template.loaders.eggs.Loader',
             ],
            'debug': True,
         },
    }
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'webhook_launcher.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'webhook_launcher.app',
    'django.contrib.admin',
    'django_extensions',
    'rest_framework',
)

FORCE_SCRIPT_NAME = ''

LOGIN_URL='/' + URL_PREFIX + "/admin/login/"
LOGIN_REDIRECT_URL='/' + URL_PREFIX + "/landing/"

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_filters.backends.DjangoFilterBackend',
    )
}

if USE_LDAP:

  logger = logging.getLogger('django_auth_ldap')
  logger.addHandler(logging.StreamHandler())
  logger.setLevel(logging.DEBUG)

  AUTH_LDAP_SERVER_URI = LDAP_SERVER
  if not ldap_verify_cert :
      AUTH_LDAP_GLOBAL_OPTIONS = {
      ldap.OPT_X_TLS_REQUIRE_CERT : ldap.OPT_X_TLS_NEVER
      }

  AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
  )
elif USE_REMOTE_AUTH:
  MIDDLEWARE_CLASSES += ( 'django.contrib.auth.middleware.RemoteUserMiddleware',)
  REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] =  ('webhook_launcher.app.auth.RemoteAuthentication',)
