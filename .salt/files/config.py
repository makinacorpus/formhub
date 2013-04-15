#!/usr/bin/env python
# WARNING
# GENERATED AND OVERWRITTEN BY SALT
#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
{% set cfg = salt['mc_utils.json_load'](data) %}
{% set data = cfg.data %}
{% set settings = cfg.data.settings %}
from pymongo import Connection
SERVER_EMAIL = DEFAULT_FROM_EMAIL = 'root@{{cfg.fqdn}}'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'db': '{{settings.mysql_db}}',
            'host': '{{data.hosts.mysql}}',
            'port': int('{{data.ports.mysql}}'),
            'user': '{{data.users.mysql}}',
            'passwd': '{{data.passwords.mysql}}',
        }
    }
}
WEBISTE_URL = 'http://{{settings.host}}'
TOUCHFORMS_URL = 'http://localhost:9000/'
DEBUG = '{{settings.debug}}'.lower().strip() == 'true'
TIME_ZONE = 'Europe/Paris'
LANGUAGE_CODE = 'fr-fr'
MEDIA_URL = WEBISTE_URL+'/media/'
ENKETO_URL = '{{settings.enketo_url}}/'
ADMINS = (
    ('admin', '{{settings.adminmail}}'),
)

BROKER_URL = 'amqp://{{data.users.rabbitmq}}:{{data.passwords.rabbitmq}}@{{data.hosts.rabbitmq}}:{{data.ports.rabbitmq}}/{{settings.rabbitmq_vhost}}'
DEFAULT_FROM_EMAIL = '{{settings.adminmail}}'
GOOGLE_STEP2_URI = WEBISTE_URL + '/gwelcome'
GOOGLE_CLIENT_ID = '{{settings.google_client_id}}'
GOOGLE_CLIENT_SECRET = '{{settings.google_client_secret}}'
MONGO_DATABASE = {
    'HOST': '{{data.hosts.mongodb}}',
    'PORT': int('{{data.ports.mongodb}}'),
    'NAME': 'formhub',
    'USER': '{{data.users.mongo}}',
    'PASSWORD': '{{data.passwords.mongo}}'}
ENKETO_API_TOKEN = '{{settings.enketo_token}}'
ALLOWED_HOSTS = ['{{settings.host}}',
                 '{{settings.host}}',
                 '{{settings.host}}:443',
                 '{{settings.host}}:80']
MEDIA_ROOT = '{{settings.media_root}}'
STATIC_ROOT = '{{data.static}}'
# vim:set et sts=4 ts=4 tw=80:
