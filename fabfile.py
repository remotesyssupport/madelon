from fabric.api import *
import os, ConfigParser

# Function to place private key and known_hosts on the remote host
# so that we can git clone a private repo via SSH successfully
def deploy_key():
	put(os.path.expanduser('~/.ssh/id_rsa'), '/root/.ssh/id_rsa', mode=0400)
	put('known_hosts', '/root/.ssh/known_hosts')

# Install and run the puppet manifests on the remote host
def deploy_puppet(repo):
        run('git clone %s /opt/puppet' % repo, pty=True)

def run_puppet(simulate='false'):
	if simulate == 'true':
		run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules --noop', pty=True)
	else:
	        run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules', pty=True)

def select_roles():
	# Fetch some values from the config file
	# @TODO fix this so that fabfile doesn't depend on ConfigParser at all
	config = ConfigParser.RawConfigParser()
	config.read('config/madelon.ini')

	availroles = config.options('Roles')
        rolelist = list()
        for availrole in availroles:
        	if config.getint('Roles', availrole) == 1:
                	rolelist.append(availrole)

	for role in rolelist:
		run('sed -i -r -e "s/# include %s/include %s"/  /opt/puppet/puppet/nodes.pp' % (role, role))

