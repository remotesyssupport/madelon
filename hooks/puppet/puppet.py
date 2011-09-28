from fabric.api import *
import os, sys, socket, ConfigParser

# Function to place known_hosts on the remote host so that
# we can git clone a private repo via SSH successfully
def deploy_key(known_hosts):
  put(known_hosts, '/root/.ssh/known_hosts')
  # Until we can automate ssh-agent forwarding (through our dodgy hack in sshagent_run(),
  # or when paramiko and fabric are patched to support it (see http://code.fabfile.org/issues/show/72)
  # we are throwing up our private key onto the new server so that we can git clone, which is not great
  # @TODO remove hardcoding of path at least..
  put('/home/jenkins/.ssh/id_rsa', '/root/.ssh/id_rsa')

def install_dependencies(remote_host, fqdn):
  run('apt-get update', pty=True)
  run('apt-get install -y git-core puppet lsb-release debian-archive-keyring', pty=True)
  # Puppet doesn't like not having a valid FQDN and Linode API/Libcloud don't 
  # seem to do this properly for whatever reason.
  run('echo %s > /etc/hostname' % fqdn, pty=True)
  run('hostname -F /etc/hostname', pty=True)
  run('echo "%s	%s" >> /etc/hosts' % (remote_host, fqdn), pty=True)

# Clone down the puppet repo
def clone_repo(repo):
  local('git clone %s /tmp/puppet-%s' % (repo, os.getpid()))

# Create a new puppet node, and update the puppet manifest.
def create_puppet_node(fqdn, rolelist):
  # @TODO make this anything else but this ugly!
  readFile = open("/tmp/puppet-%s/puppet/nodes.pp" % os.getpid())
  lines = readFile.readlines()
  readFile.close()

  w = open("/tmp/puppet-%s/puppet/nodes.pp" % os.getpid(), "w")
  w.writelines([item for item in lines])

  configlines = []
  configlines.append('\n')
  configlines.append("node \"%s\" {\n" % fqdn)
  for role in rolelist:
    configlines.append("  include %s\n" % role)
  configlines.append("}\n")

  w.writelines(configlines)
  w.close()

# Commit the new file and push  
def commit_puppet_node(fqdn):
  print "===> Adding the new node into puppet"
  with cd('/tmp/puppet-%s' % os.getpid()):
    local('git add /tmp/puppet-%s/puppet/nodes.pp' % os.getpid())
    print "=== Committing and pushing the change"
    local('git commit -m "Added %s node into puppet"' % fqdn)
    local('git push origin master')

# Install the puppet manifests on the remote host
def deploy_puppet(repo):
  # We must use sshagent_run() here to get around the repo being private once we can automate it
  print "===> Pulling down the puppet manifests from %s onto the new machine" % repo
  run('git clone %s /opt/puppet' % repo, pty=True)

# Execute the puppet manifests on the remote host
def run_puppet(simulate='false'):
  if simulate == 'true':
    print "===> Simulating executing the puppet manifests..."
    run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules --noop', pty=True)
  else:
    print "===> Executing the puppet manifests..."
    run('puppet --verbose /opt/puppet/puppet/init.pp --modulepath=/opt/puppet/puppet/modules', pty=True)

# Clean up the temporary git repo
def remove_repo():
  print "===> Removing the git repo"
  local('rm -rf /tmp/puppet-%s' % os.getpid())

def main(remote_host, fqdn, hookconfigfile=""):
  # Install some dependencies
  install_dependencies(remote_host, fqdn)

  # Fetch some values from the config file
  config = ConfigParser.RawConfigParser()
  if hookconfigfile:
    config.read(hookconfigfile)
  else:
    config.read(os.path.expanduser(os.path.dirname(__file__) + "/puppet.ini"))

  if config.getboolean('Git', 'private'):
    # This is a private repo. We need to do some extra legwork to be able to clone it properly.
    # Send the private key.
    known_hosts = config.get('Puppet', 'known_hosts')
    print "===> Deploying the private keys..."
    deploy_key(known_hosts)

  # Define what roles this server will be, for puppet
  print "===> Setting puppet roles for this server..."
  availroles = config.options('Roles')
  rolelist = list()
  for availrole in availroles:
    if config.getint('Roles', availrole) == 1:
      rolelist.append(availrole)

  # Find the git repo for puppet
  repo = config.get('Git', 'repo')

  # Add our new node into puppet itself
  clone_repo(repo)
  create_puppet_node(fqdn, rolelist)
  commit_puppet_node(fqdn)
  remove_repo()

  # Clone down the puppet manifests on the remote host
  deploy_puppet(repo)
  # Execute the puppet manifests
  if config.getboolean('Puppet', 'simulate'):
    run_puppet(simulate='true')
  else:
    run_puppet()
