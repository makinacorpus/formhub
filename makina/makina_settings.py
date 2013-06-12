from settings import *
INSTALLED_APPS += ('makina',)
THERE = PROJECT_ROOT + '/makina'
TEMPLATE_DIRS = (THERE+'/templates',) + TEMPLATE_DIRS
ROOT_URLCONF = 'makina.makina_urls'
