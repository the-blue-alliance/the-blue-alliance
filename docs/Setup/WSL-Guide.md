### Initial setup

This doc was written on `Windows 10 Version 2004 (OS Build 19041.388)` using WSL 2 running Ubuntu 20.04. This was not tested on WSL1 and we highly recommend using WSL2.

Powershell:

```
PS C:\Users\justin> wsl --list --verbose
  NAME                   STATE           VERSION
* Ubuntu-20.04           Running         2
  docker-desktop         Running         2
  docker-desktop-data    Running         2
```

We highly recommend cloning your TBA fork onto the WSL filesystem. Upon an initial WSL setup, doing `cd ~` in your WSL shell will bring you to the FS in your terminal. To see the files in Windows Explorer, you can navigate to `\\wsl$` and then open your corresponding OS installation.

If you do not clone to the WSL FS, you will experience slower file read/write times and *hot reloading will not work* (such as `vagrant rsync-auto`). There may be an option to swap these hot reloading tools to poll the FS, but these will be much slower, especially in a large project like TBA. (Source: https://github.com/microsoft/WSL/issues/4417)

### Install Docker on windows

Make sure you set it up with WSL.

https://docs.docker.com/docker-for-windows/

https://docs.docker.com/docker-for-windows/wsl/

After its running (on Windows), it should be added to your WSL path.

### Install Vagrant on WSL

You probably need to install Virtualbox too, as it says in the article.

https://linuxize.com/post/how-to-install-vagrant-on-ubuntu-20-04/

### Edit `~/.bashrc`

(Or the equivalent for whatever shell you are using)

Please follow the Vagrant setup for WSL here: https://www.vagrantup.com/docs/other/wsl

Please make note to add the following to your `~/.bashrc` (or equivalent):

```
export VAGRANT_WSL_ENABLE_WINDOWS_ACCESS="1"
```

##### Additionally...

WSL may not be able to find your powershell executable (for some reason); you'll need to add the following symlink:

```
sudo ln -s /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe /usr/local/bin/powershell
```

Source: https://github.com/hashicorp/vagrant/issues/11085

For whatever reason, the usual way of exporting the powershell executable onto the `PATH` variable doesn't work here.


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

You may have to chmod 600 to the private key, but proobably not:

```
$ chmod 600 -f .vagrant/machines/default/docker/private_key
```

### Run `vagrant up`

Try running `vagrant up`. If you see an error regarding unable to find the directory `/tba`, try running `vagrant destroy && vagrant up`.