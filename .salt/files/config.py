#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
{% set cfg = salt['mc_utils.json_load'](cfg) %}
{% set data = cfg.data %}
{% set settings = cfg.data.settings %}
{% macro renderbool(opt)%}
{{opt}} = {%if data.get(opt, False)%}True{%else%}False{%endif%}
{% endmacro %}
import json
from django.utils.translation import gettext_lazy as _
from pymongo import Connection
SITE_ID={{data.SITE_ID}}
SERVER_EMAIL = '{{data.server_email}}'
DEFAULT_FROM_EMAIL = '{{data.default_from_email}}'
DATABASES = {
    'default': json.loads("""
{{salt['mc_utils.json_dump'](data.db)}}
""".strip()),
}
{% set admint = None %}
ADMINS = (
    {% for dadmins in data.admins %}
    {% for admin, data in dadmins.items() %}
    {% if data %}{% set admint = (admin, data) %}{%endif %}
    ('{{admin}}', '{{data.mail}}'),
    {% endfor %}
    {% endfor %}
)
{{renderbool('DEBUG') }}
{% for i in data.server_aliases %}
{% if i not in data.ALLOWED_HOSTS %}
{% do data.ALLOWED_HOSTS.append(i) %}
{% endif %}
{% endfor %}
CORS_ORIGIN_ALLOW_ALL = {{data.CORS_ORIGIN_ALLOW_ALL}}
ALLOWED_HOSTS = {{data.ALLOWED_HOSTS}}
MEDIA_ROOT = '{{data.media}}'
STATIC_ROOT = '{{data.static}}'
SECRET_KEY = '{{data.SECRET_KEY}}'
USE_X_FORWARDED_HOST={{data.USE_X_FORWARDED_HOST}}
# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/
DATE_FORMAT = '{{data.DATE_FORMAT}}'
TIME_ZONE = '{{data.timezone}}'
LANGUAGE_CODE = '{{data.LANGUAGE_CODE}}'
LANGUAGES = (
    ('fr', _('Français')),
    ('it', _('Italia')),
    ('en', _('English'))
)

WEBISTE_URL = 'http://{{data.domain}}'
TOUCHFORMS_URL = 'http://localhost:9000/'
DEBUG = '{{data.DEBUG}}'.lower().strip() == 'true'
MEDIA_URL = WEBISTE_URL+'/media/'
ENKETO_URL = '{{data.enketo_url}}/'
BROKER_URL = 'amqp://{{data.rabbitmq_user}}:{{data.rabbitmq_password}}@{{data.rabbitmq_host}}:{{data.rabbitmq_port}}/{{data.rabbitmq_vhost}}'
GOOGLE_STEP2_URI = WEBISTE_URL + '/gwelcome'
GOOGLE_CLIENT_ID = '{{data.google_client_id}}'
GOOGLE_CLIENT_SECRET = '{{data.google_client_secret}}'
MONGO_DATABASE = {
    'HOST': '{{data.mongodb_host}}',
    'PORT': int('{{data.mongodb_port}}'),
    'NAME': '{{data.mongodb_db}}',
    'USER': '{{data.mongodb_user}}',
    'PASSWORD': '{{data.mongodb_password}}'}
ENKETO_API_TOKEN = '{{data.enketo_token}}'
{% if data.get('ADDITIONAL_TEMPLATE_DIRS', None) %}
ADDITIONAL_TEMPLATE_DIRS = tuple({{data.ADDITIONAL_TEMPLATE_DIRS}})
{% endif %}
# vim:set et sts=4 ts=4 tw=80:
