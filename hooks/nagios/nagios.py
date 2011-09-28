from fabric.api import *
import os, sys, socket, ConfigParser

# Clone down the puppet repo
def clone_repo(repo):
  local('git clone %s /tmp/puppet-%s' % (repo, os.getpid()))

# Create a new nagios config file for this node, and update the puppet manifest.
def create_nagios_node(remote_host, fqdn, rolelist):
  # @TODO make this anything else but this ugly!
  readFile = open("/tmp/puppet-%s/puppet/modules/nagios/manifests/init.pp" % os.getpid())
  lines = readFile.readlines()
  readFile.close()

  w = open("/tmp/puppet-%s/puppet/modules/nagios/manifests/init.pp" % os.getpid(), "w")
  w.writelines([item for item in lines[:-1]])

  configlines = []
  configlines.append('\n')
  configlines.append("  nagios::host { '%s':\n" % fqdn)
  configlines.append("    address => '%s',\n" % remote_host)
  configlines.append("    hostgroups => 'linux-servers, ssh-servers, smtp-servers, " + ', '.join(rolelist) + "',\n")
  configlines.append("  }\n")
  configlines.append("}\n")

  w.writelines(configlines)
  w.close()

# Commit the new file and push  
def commit_nagios_node(fqdn):
  print "===> Adding the new node nagios config into git"
  with cd('/tmp/puppet-%s/' % os.getpid()):
    local('git add /tmp/puppet-%s/puppet/modules/nagios/manifests/init.pp' % os.getpid())
    print "=== Committing and pushing the change"
    local('git commit -m "Added %s into nagios monitoring"' % fqdn)
    local('git push origin master')

# Clean up the temporary git repo
def remove_repo():
  print "===> Removing the git repo"
  local('rm -rf /tmp/puppet-%s' % os.getpid())

def main(remote_host, fqdn, hookconfigfile=""):
  # Fetch some values from the config file
  config = ConfigParser.RawConfigParser()
  if hookconfigfile:
    config.read(hookconfigfile)
  else:
    config.read(os.path.expanduser(os.path.dirname(__file__) + "/nagios.ini"))

  # Find the git repo for puppet
  repo = config.get('Git', 'repo')

  # Define what roles this server will be, for nagios hostgroups
  availroles = config.options('Roles')
  rolelist = list()
  for availrole in availroles:
    # Currently ignoring the 'debian' and 'proxyserver' roles. Latter should probably have its backend checked
    if config.getint('Roles', availrole) == 1 and availrole not in ['debian', 'proxyserver']:
      rolelist.append(availrole)

  clone_repo(repo)
  create_nagios_node(remote_host, fqdn, rolelist)
  commit_nagios_node(fqdn)
  remove_repo()
