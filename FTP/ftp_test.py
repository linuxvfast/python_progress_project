__author__ = 'progress'

import configparser

config = configparser.ConfigParser()
config.read('accot.cfg')
print(config['bitbucket.org']['User'])
config['bitbucket.org']['User'] = 'HG'
print(config['bitbucket.org']['User'])
config.set('bitbucket.org','User','HG')
config.write(open('accot.cfg','w'))
print(config['bitbucket.org']['User'])
