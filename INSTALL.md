# Project setup instructions

Follow the instructions below to setup the project into an "empty" platform, which is assumed to be
Ubuntu 16.04 (Xenial) 64-bit. If you use Vagrant, note that there is bug in the official box
"ubuntu/xenial64" in Windows. You cannot login with ``vagrant:vagrant`` like normal. The username is
``ubuntu`` and the password is a random string visible in
``~\Users\<Name>\.vagrant.d\...\Vagrantfile``. The unofficial recommendation is to use the box
called ``v0rtex\xenial64``

# Preparation

As is customary, you should not do things as ``root``, so let's create our user account. In Vagrant
these steps are not needed.

1. Either as ``root`` or via ``sudo``, create the account: ``adduser vortech`` and give it a password
1. Then add ``sudo`` rights for the account. Run: ``visudo``
1. Find the row that says ``root    ALL=(ALL:ALL) ALL``
1. Under it, add our new user: ``vortech ALL=(ALL:ALL) ALL``
1. Save and close
1. SSH to the platform using this new account.

# Programs

These are the mandatory programs needed to get started.

## The basic tools

1. Vagrant specialty: At least for me, there was a lock file in ``/var/lib/dpkg/lock`` that had to
be deleted
1. Then install the first pieces:
``sudo apt install virtualenv python3 uwsgi uwsgi-emperor uwsgi-plugin-python3 nginx-full git``

## Setup the app

1. Create the dir where the app will be: ``sudo mkdir -p /srv/vortech-backend``
1. Enter the dir: ``cd /srv/vortech-backend``
1. And add a virtualenv there: ``sudo virtualenv -p /usr/bin/python3 venv``
1. Then clone the project there:
``sudo git clone https://github.com/Torniojaws/vortech-backend.git html/``
