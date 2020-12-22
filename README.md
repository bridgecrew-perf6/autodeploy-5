# Gitdeploy
Service to sync from a gitea webhook to a server as securely as possible

There are two components to this, one receiver that takes the output of the
webhook POST-ed by Gitea and checks the signature and validity of the branch
and repository against the repo and key in a config file, and another that
acts on the local filesystem by checking out the changes from the pushed webhook into a cloned repo.

There are two kinds of the first component here, one meant to run as a CGI
script from an existing webserver, and another that runs as a daemon with
a standalone webserver (for nodes without a suitable apache)

## Design
Why have two components? The first component can run as CGI therefore can be
run as the apache or nginx user, and the part that reads the json and checks
the signature can operate in a lower security domain. The repo-syncing daemon
component can run as root or another privileged user to do the actual git pull without sudo rules or having to run a setuid operation from a CGI script.

The config file is shared by both components and has some universal settings then a section per-repo you want configured. See `conf.sample` provided in this repo. The default location is `/etc/autodeploy.cfg` but it is overridable with the `AUTODEPLOYCFG` enviornment variable.

The messages passed from the receiver component to the git daemon component are
signed with a message key

## Deploying
First figure out how you want to deploy the receiver-component -- via CGI or
standalone daemon. This will determine how to set the permissions on the config file as well.

### Security Concerns for Config File
Since the config file has secrets that need to be read by both components, it
needs to be readable by both but not by everyone.

For example, if you run the CGI script under apache and the daemon runs as root, the config file should look like:
```
[user@host]$ ls -l /etc/autodeploy.cfg
-rw-r-----. 1 root apache 3302 Sep 14 15:35 /etc/autodeploy.cfg
```

The daemon does the git operations so the files will end up owned by that user unless the postscript changes the owner (if root).

### Daemon socket
The daemon listens on a unix domain socket configured in the config file main section, this socket needs to be writable by the receiver-component and the daemon.



