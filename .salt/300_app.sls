{% set cfg = opts.ms_project %}
{% set data = cfg.data %}
{% set scfg = salt['mc_utils.json_dump'](cfg) %}


{% macro set_env() %}
    - env:
      - DJANGO_SETTINGS_MODULE: "{{data.DJANGO_SETTINGS_MODULE}}"
{% endmacro %}

{{cfg.name}}-up-sub:
  cmd.run:
    - user: {{cfg.user}}
    - use_vt: true
    - name: |
            set -e
            cd {{data.app_root}}
            git submodule init
            git submodule update

{{cfg.name}}-config:
  file.managed:
    - name: {{data.app_root}}/local_settings.py
    - source: salt://makina-projects/{{cfg.name}}/files/config.py
    - template: jinja
    - user: {{cfg.user}}
    - data: |
            {{scfg}}
    - group: {{cfg.group}}
    - makedirs: true
    - require:
      - cmd: {{cfg.name}}-up-sub

static-{{cfg.name}}:
  cmd.run:
    - name: {{data.app_root}}/bin/python manage.py collectstatic --noinput
    {{set_env()}}
    - cwd: {{data.app_root}}
    - user: {{cfg.user}}
    - watch:
      - file: {{cfg.name}}-config

syncdb-{{cfg.name}}:
  cmd.run:
    - name: {{data.app_root}}/bin/python manage.py syncdb --noinput
    {{set_env()}}
    - cwd: {{data.app_root}}
    - user: {{cfg.user}}
    - use_vt: true
    - output_loglevel: info
    - watch:
      - file: {{cfg.name}}-config

media-{{cfg.name}}:
  cmd.run:
    - name: rsync -av {{data.media_source}}/ {{data.media}}/
    - onlyif: test -e {{data.media_source}}
    - cwd: {{cfg.project_root}}
    - user: {{cfg.user}}
    - use_vt: true
    - output_loglevel: info
    - watch:
      - file: {{cfg.name}}-config

{% for dadmins in data.admins %}
{% for admin, udata in dadmins.items() %}
user-{{cfg.name}}-{{admin}}:
  cmd.run:
    - name: {{data.app_root}}/bin/python manage.py reatesuperuser --username="{{admin}}" --email="{{udata.mail}}" --noinput
    - unless: {{data.app_root}}/bin/python -c "from django.contrib.auth.models import User;User.objects.filter(username='{{admin}}')[0]"
    {{set_env()}}
    - cwd: {{data.app_root}}
    - user: {{cfg.user}}
    - watch:
      - file: {{cfg.name}}-config
      - cmd: syncdb-{{cfg.name}}

superuser-{{cfg.name}}-{{admin}}:
  file.managed:
    - contents: |
                from django.contrib.auth.models import User
                user=User.objects.filter(username='{{admin}}').all()[0]
                user.set_password('{{udata.password}}')
                user.save()
    - mode: 600
    - user: {{cfg.user}}
    - group: {{cfg.group}}
    - source: ""
    - name: "{{data.app_root}}/salt_{{admin}}_password.py"
    - watch:
      - file: {{cfg.name}}-config
      - cmd: syncdb-{{cfg.name}}
  cmd.run:
    {{set_env()}}
    - name: {{data.app_root}}/bin/python "{{data.app_root}}/salt_{{admin}}_password.py"
    - cwd: {{data.app_root}}
    - user: {{cfg.user}}
    - watch:
      - cmd: user-{{cfg.name}}-{{admin}}
      - file: superuser-{{cfg.name}}-{{admin}}
{%endfor %}
{%endfor %}
