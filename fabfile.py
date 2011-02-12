from fabric.api import *
import ConfigParser
import os

# Fetch some values from the config file
config = ConfigParser.RawConfigParser()
config.read('config/madelon.ini')

# Function to place private key and known_hosts on the remote host
# so that we can git clone a private repo via SSH successfully
def deploy_key():
	put(os.path.expanduser('~/.ssh/id_rsa'), '/root/.ssh/id_rsa', mode=0400)
	put('known_hosts', '/root/.ssh/known_hosts')

# Install and run the puppet manifests on the remote host
def deploy_puppet():
        run('git clone %s /opt/puppet' % config.get('Git', 'repo'), pty=True)
	if config.getboolean('Puppet', 'simulate'):
		run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules --noop', pty=True)
	else:
	        run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules', pty=True)
