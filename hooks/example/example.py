# An example hook for madelon.
# Remember, this is only executed if the hook is set
# to '1' in [Hooks] section of config/madelon.ini

import fabric.api as fabric
import ConfigParser

def main(remote_host, fqdn):
	# If you wanted to fetch settable/gettable options from ConfigParser, you
        # could set a hook-specific config ini file.
	config = ConfigParser.RawConfigParser()
	config.read(os.path.expanduser(os.path.dirname(__file__) + "/example.ini"))
	foo = config.get('Example', 'foo')
	print "%s\n" % foo
	
	# The main madelon file sends two arguments to the hook's main function that might be useful.
	# These are remote_host (the IP of the new machine), and fqdn (the name of the server that was 
	# sent as an argument to madelon). Not always necessary, but is for things like the Aegir hook
	print "The server's IP is %s\n" % remote_host
	
	# Use fabric to set the FQDN on the remote host
	fabric.run("echo %s > /etc/hostname" % fqdn, pty=True)
	fabric.run("hostname -F /etc/hostname", pty=True)

# Initialise the main loop
if __name__ == "__main__":
        main()
