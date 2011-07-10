import ConfigParser, sys, os, random, string
import fabric.api as fabric

# Install dependencies for Aegir
def fab_install_dependencies(newpass):
        fabric.run("apt-get update", pty=True)
        fabric.run("echo 'postfix postfix/main_mailer_type select Internet Site' | debconf-set-selections", pty=True)
        fabric.run("echo 'postfix postfix/mailname string $HOSTNAME' | debconf-set-selections", pty=True)
        fabric.run("echo 'postfix postfix/destinations string localhost.localdomain, localhost' | debconf-set-selections", pty=True)
        fabric.run("echo mysql-server mysql-server/root_password select %s | debconf-set-selections" % newpass, pty=True)
        fabric.run("echo mysql-server mysql-server/root_password_again select %s | debconf-set-selections" % newpass, pty=True)
        fabric.run("apt-get -y install apache2 php5 php5-cli php5-gd php5-mysql postfix mysql-server sudo rsync git-core unzip", pty=True)

# Prepare a basic firewall
def fab_prepare_firewall(trusted_ip):
        print "===> Setting a little firewall"
        fabric.run("iptables -I INPUT -s %s -p tcp --dport 22 -j ACCEPT; iptables -I INPUT -s %s -p tcp --dport 80 -j ACCEPT; iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT; iptables --policy INPUT DROP" % (trusted_ip, trusted_ip), pty=True)

# Fabric command to set some Apache requirements
def fab_prepare_apache():
        print "===> Preparing Apache"
        fabric.run("a2enmod rewrite", pty=True)
        fabric.run("ln -s /var/aegir/config/apache.conf /etc/apache2/conf.d/aegir.conf", pty=True)

# Fabric command to raise PHP CLI memory limit (for Drupal 7 / OpenAtrium)
def fab_prepare_php():
        print "===> Preparing PHP"
        fabric.run("sed -i s/'memory_limit = 32M'/'memory_limit = 256M'/ /etc/php5/cli/php.ini", pty=True)

# Fabric command to add the aegir user and to sudoers also
def fab_prepare_user():
        print "===> Preparing the Aegir user"
        fabric.run("useradd -r -U -d /var/aegir -m -G www-data aegir", pty=True)
        fabric.run("echo 'aegir ALL=NOPASSWD: /usr/sbin/apache2ctl' >> /etc/sudoers", pty=True)

# Fabric command to fetch Drush
def fab_fetch_drush():
        print "===> Fetching Drush"
        fabric.run("su - -s /bin/sh aegir -c 'wget http://ftp.drupal.org/files/projects/drush-7.x-4.4.tar.gz'", pty=True)
        fabric.run("su - -s /bin/sh aegir -c' gunzip -c drush-7.x-4.4.tar.gz | tar -xf - '", pty=True)
        fabric.run("su - -s /bin/sh aegir -c 'rm /var/aegir/drush-7.x-4.4.tar.gz'", pty=True)

# Fabric command to fetch Provision
def fab_fetch_provision():
        print "===> Fetching Provision"
        fabric.run("su - -s /bin/sh aegir -c 'php /var/aegir/drush/drush.php dl -y --destination=/var/aegir/.drush provision-6.x-1.1'", pty=True)

# Fabric command to run the install.sh aegir script
def fab_hostmaster_install(domain, email, newpass):
        print "===> Running hostmaster-install"
        fabric.run("su - -s /bin/sh aegir -c 'php /var/aegir/drush/drush.php hostmaster-install %s --client_email=%s --aegir_db_pass=%s --yes'" % (domain, email, newpass), pty=True)
        fabric.run("su - -s /bin/sh aegir -c 'php /var/aegir/drush/drush.php -y @hostmaster vset hosting_queue_tasks_frequency 1'", pty=True)
        fab_run_dispatch()

# Force the dispatcher
def fab_run_dispatch():
        fabric.run("su - -s /bin/sh aegir -c 'php /var/aegir/drush/drush.php @hostmaster hosting-dispatch'", pty=True)

# Helper script to generate a random password
def gen_passwd():
        N=8
        return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(N))

def main(remote_host, fqdn):
	# Fetch some values from the config file
	config = ConfigParser.RawConfigParser()
	config.read(os.path.expanduser(os.path.dirname(__file__) + "/aegir.ini"))

	# E-mail address of the main Aegir admin user
	email = config.get('Aegir', 'email')
	# A trusted IP to grant access to in the firewall
	trusted_ip = config.get('Aegir', 'trusted_ip')

	# Set a random password, which will be used for the MySQL 'root' user.
	newpass = gen_passwd()

	# Run through our sub fab functions to install Aegir.
        fab_prepare_firewall(trusted_ip)
        fab_install_dependencies(newpass)
        fab_prepare_apache()
        fab_prepare_php()
        fab_prepare_user()
        fab_fetch_drush()
        fab_fetch_provision()
        fab_hostmaster_install(fqdn, email, newpass)

# Initialise the main loop
if __name__ == "__main__":
        main()
