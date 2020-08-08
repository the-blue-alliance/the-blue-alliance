This doc was written on `Windows 10 Version 2004 (OS Build 19041.388)` using WSL 2 running Ubuntu 20.04.

Powershell:

```
PS C:\Users\justin> wsl --list --verbose
  NAME                   STATE           VERSION
* Ubuntu-20.04           Running         2
  docker-desktop         Running         2
  docker-desktop-data    Running         2
```

### Install Docker on windows

Make sure you set it up with WSL.

https://docs.docker.com/docker-for-windows/

https://docs.docker.com/docker-for-windows/wsl/

After its running (on Windows), it should be added to your WSL path.

### Install Vagrant on WSL

You probably need to install Virtualbox too, as it says in the article.

https://linuxize.com/post/how-to-install-vagrant-on-ubuntu-20-04/


### Edit `/etc/wsl.conf`

Create `/etc/wsl.conf` (you'll need `sudo`) and add this:

```
[automount]
enabled = true
options = "metadata"
mountFsTab = false
```

Restart WSL after this. You may be able to get away with just restarting your shells, but it didn't work for me until I restarted Windows entirely.

Source: https://github.com/microsoft/WSL/issues/81#issuecomment-400597679

### Maybe `chmod` the ssh key

You may have to chmod 600 to the private key:

```
$ chmod 600 -f .vagrant/machines/default/docker/private_key
```

### Run `vagrant up`

Try running `vagrant up`. If you see an error regarding unable to find the directory `/tba`, try running `vagrant destroy && vagrant up`.