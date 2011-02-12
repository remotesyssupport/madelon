from fabric.api import *
import os


# Function to place private key and known_hosts on the remote host
# so that we can git clone a private repo via SSH successfully
def deploy_key():
	put(os.path.expanduser('~/.ssh/id_rsa'), '/root/.ssh/id_rsa', mode=0400)
	put('known_hosts', '/root/.ssh/known_hosts')

# Install and run the puppet manifests on the remote host
def deploy_puppet(repo, simulate='false'):
        run('git clone %s /opt/puppet' % repo, pty=True)
	if simulate == 'true':
		run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules --noop', pty=True)
	else:
	        run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules', pty=True)
