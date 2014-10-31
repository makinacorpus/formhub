*FORMHUB INSTALL*
------------------

# Requirements & prerequisites
* Ubuntu >= 14.04
* 4gb ram
* 10gb free drive space
* Full internet access
* For enqueto, a wildcard DNS on the hostname '\*.enketo.local'

# Important notes
##  salt['mc_utils.generate_stored_password']
This function stores a local password on the host where salt executes and the given hash key.
In this case, we are installing on the same host and that is why we can reference it on other projets and the function just return everywhere the same password.

In other words, that obviously mean that you need to get the password out of the registry on a multi-hosts formhub install.
EG, in formhub deployment pillar, you will need the raw mysql password string got with `salt-call --local mc_utils.generate_stored_password corpus_mysql_formhub` on the mysql host.

Replace formhub.local with your formhub FQDN.
Replace enketo.local with your enelto FQDN.

# DNS Setup exemple
* \*.enketo.local / enketo.local -> enketo host
* formhub.local -> formhub host
* rabbitmq.formhub.local -> formhub host
* mysql.forhub.local -> formhub host

Here all services are hosted on the same host.

# Install makina-states

    git clone https://github.com/makinacorpus/makina-states.git /srv/salt/makina-states
    mkdir -p /srv/salt
    /srv/salt//makina-states/_scripts/boot-salt.sh  -b stable

# initialize deployment containers

     for i in mysql mongodb rabbitmq formhub enketo;do salt-call --local mc_project.deploy ${i};done

# initialize project remote repositories counter parts

    for i in mysql rabbitmq mongodb;do pushd /srv/projects/$i/project;git remote rm g;git remote add g https://github.com/makinacorpus/corpus-${i}.git;git fetch --all;git reset --hard g/master;popd;done
    pushd /srv/projects/formhub/project;git remote rm g;git remote add g https://github.com/makinacorpus/formhub.git;git fetch --all;git reset --hard g/master;popd
    for i in mysql rabbitmq mongodb;do pushd /srv/projects/$i/project;git remote rm g;git remote add g https://github.com/makinacorpus/corpus-${i}.git;git fetch --all

# configure mysql

/srv/projects/mysql/pillar/init.sls:

    makina-states.services.db.mysql.available_mem: 1500
    makina-projects.mysql:
      api_version: '2'
      data:
        domain: mysql.formhub.local
        http_users:
          - root: "{{salt['mc_utils.generate_stored_password']('corpus_root_mysql')}}"
        sysctls:
          # 1.5GB optim, mongodb is the most used db
          - kernel.shmall: 393216
          - kernel.shmmax: 1572864
        databases:
          - enketo:
              password: {{salt['mc_utils.generate_stored_password']('corpus_mysql_enketo')}}
              user: enketo
          - formhub:
              password: {{salt['mc_utils.generate_stored_password']('corpus_mysql_formhub')}}
              user: formhub

# configure mongodb

/srv/projects/mondodb/pillar/init.sls:

    makina-projects.mongodb:
      api_version: '2'
      data:
        domain: mongodb.formhub.local
        databases:
          - formhub:
              password: {{salt['mc_utils.generate_stored_password']('corpus_mongodb_formhub')}}
              user: formhub

# configure rabbitmq

/srv/projects/rabbitmq/pillar/init.sls:

    makina-projects.rabbitmq:
      api_version: '2'
      data:
        domain: rabbitmq.formhub.local
        vhosts:
          - formhub:
              password: {{salt['mc_utils.generate_stored_password']('corpus_rabbitmq_formhub')}}
              user: formhub

# configure formhub
/srv/projects/formhub/pillar/init.sls:

    makina-projects.formhub:
      api_version: '2'
      data:
        domain: formhub.local
        rabbitmq_vhost: formhub
        rabbitmq_host:  127.0.0.1
        rabbitmq_user: formhub
        rabbitmq_password: "{{salt['mc_utils.generate_stored_password']('corpus_rabbitmq_formhub')}}"
        mongodb_host: 127.0.0.1
        mongodb_user: formhub
        mongodb_password: "{{salt['mc_utils.generate_stored_password']('corpus_mongodb_formhub')}}"
        adminmail: sysadmin+formhub@makina-corpus.com
        google_client_id: '104603543414.apps.googleusercontent.com'
        google_client_secret: 'YjBPBFlPxPBQ3JGN0FyHKqsK'
        google_map_key: 'AIzaSyBEYSyNMJPuzxLQik4ajsW2hqT47u6qUSA'
        enketo_token: "{{salt['mc_utils.generate_stored_password']('corpus_enketo_password_formhub')}}"
        enketo_key: "{{salt['mc_utils.generate_stored_password']('corpus_enketo_key')}}"
        enketo_url: http://enketo.local
        db:
          ENGINE: django.db.backends.mysql
          HOST: 127.0.0.1
          NAME: formhub
          USER: formhub
          PASSWORD: "{{salt['mc_utils.generate_stored_password']('corpus_mysql_formhub')}}"
        # if you want to reskin some templates
        #ADDITIONAL_TEMPLATE_DIRS:
        #  - '{project_root}/overrides'

# configure enketo

     makina-projects.enketo:
      api_version: '2'
      data:
        server_aliases: [enketo.local]
        domain: "*.enketo.local"
        db_name: enketo
        db_host: 127.0.0.1
        db_user: enketo
        db_password: "{{salt['mc_utils.generate_stored_password']('corpus_mysql_enketo')}}"
        enketo_key: "{{salt['mc_utils.generate_stored_password']('corpus_enketo_key')}}"
        google_map_key: 'AIzaSyBEYSyNMJPuzxLQik4ajsW2hqT47u6qUSA'
        integration_with_url: 'http://formub.local'
        formhub_hosts:
            - host: "formhub.local"
              token: {{salt['mc_utils.generate_stored_password']('corpus_enketo_password_formhub')}}

# Commit & refresh pillar & project remotes counterpart

     for i in mysql mongodb rabbitmq formhub enketo;do for j in project pillar;do cd /srv/projects/$i/$j && git commit -am up && git push --force;done;done

# Install projects
## mysql

    salt-call --local -lall mc_project.deploy mysql only=install,fixperms
    # 2 times are neccessary because mysql saltstack modules at first are not avalaible as mysql is not installed
    salt-call --local -lall mc_project.deploy mysql only=install,fixperms

## rabbitmq

    salt-call --local -lall mc_project.deploy rabbitmq only=install,fixperms

## mongodb

    salt-call --local -lall mc_project.deploy mongodb only=install,fixperms
    # 2 times, again
    salt-call --local -lall mc_project.deploy mongodb only=install,fixperms

## Install enketo

    salt-call --local -lall mc_project.deploy enketo only=install,fixperms

## Install formhub

    salt-call --local -lall mc_project.deploy formhub only=install,fixperms

<!-- vim: set tw=0 ft=markdown -->
