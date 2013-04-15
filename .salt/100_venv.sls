{% set cfg = opts.ms_project %}
{% set data = cfg.data %}
{% set scfg = salt['mc_utils.json_dump'](cfg) %}

{{cfg.name}}-venv:
  virtualenv.managed:
    - requirements: salt://makina-projects/{{cfg.name}}/requirements.txt
    - name: {{cfg.project_root}}
    - download_cache: {{cfg.data_root}}/cache
    - user: {{cfg.user}}
    - runas: {{cfg.user}}
    - use_vt: true

