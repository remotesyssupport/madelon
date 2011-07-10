from fabric.api import *
import os, sys, socket, ConfigParser

# Function to place known_hosts on the remote host so that
# we can git clone a private repo via SSH successfully
def deploy_key(known_hosts):
	put(known_hosts, '/root/.ssh/known_hosts')

def install_dependencies(remote_host, fqdn):
        run('apt-get update', pty=True)
        run('apt-get install -y git-core puppet lsb-release debian-archive-keyring', pty=True)
	# Puppet doesn't like not having a valid FQDN and Linode API/Libcloud don't 
	# seem to do this properly for whatever reason.
	run('echo %s > /etc/hostname' % fqdn, pty=True)
	run('hostname -F /etc/hostname', pty=True)
	run('echo "%s	%s" >> /etc/hosts' % (remote_host, fqdn), pty=True)

# Install and run the puppet manifests on the remote host
def deploy_puppet(repo):
        run('git clone %s /opt/puppet' % repo, pty=True)

def run_puppet(simulate='false'):
        if simulate == 'true':
                run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules --noop', pty=True)
        else:
                run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules', pty=True)

def select_roles(config):
        # Fetch some values from the config file
        # @TODO fix this so that fabfile doesn't depend on ConfigParser at all
        config = ConfigParser.RawConfigParser()
        config.read(config)

        availroles = config.options('Roles')
        rolelist = list()
        for availrole in availroles:
                if config.getint('Roles', availrole) == 1:
                        rolelist.append(availrole)

        for role in rolelist:
                run('sed -i -r -e "s/# include %s/include %s"/  /opt/puppet/puppet/nodes.pp' % (role, role), pty=True)


def main(remote_host, fqdn):
        # Fetch some values from the config file
        config = ConfigParser.RawConfigParser()
        config.read(os.path.expanduser(os.path.dirname(__file__) + "/puppet.ini"))

        if config.getboolean('Git', 'private'):
                # This is a private repo. We need to do some extra legwork to be able to clone it properly.
                # Send the private key.
	        known_hosts = config.get('Puppet', 'known_hosts')
                print "Deploying the private key..."
                deploy_key(known_hosts)

        # Now fetch and run puppet on the remote host
	repo = config.getboolean('Git', 'repo')
        print "Fetching the puppet git repo %s" % repo
	deploy_puppet(repo)

        # Define what roles this server will be, for puppet
        if config.has_section('Roles'):
                print "Setting puppet roles for this server..."
		select_roles(config)

        if config.getboolean('Puppet', 'simulate'):
                print "Simulating executing the puppet manifests..."
                run_puppet(simulate='true')
        else:
                print "Executing the puppet manifests..."
                run_puppet()

