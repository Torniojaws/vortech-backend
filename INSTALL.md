# Project setup instructions

Follow the instructions below to setup the project into an "empty" platform, which is assumed to be
Ubuntu 14.04 64-bit.

# Preparation

As is customary, you should not do things as ``root``, so let's create our user account.

1. Either as ``root`` or via ``sudo``, create the account: ``adduser vortech`` and give it a password
1. Then add ``sudo`` rights for the account. Run: ``visudo``
1. Find the row that says ``root    ALL=(ALL:ALL) ALL``
1. Under it, add our new user: ``vortech ALL=(ALL:ALL) ALL``
1. Save and close
1. SSH to the platform using this new account.

# Programs

These are the mandatory programs needed to get started.

## Webserver - Nginx

1. Let's update apt first: ``sudo apt-get update``
1. Webserver: ``sudo apt-get install nginx`` - this will install an old version 1.4.6
1. Let's update the nginx to a newer version:
1. Update the repositories: ``sudo add-apt-repository ppa:nginx/stable``
1. Then update apt: ``sudo apt-get update``
1. And now install the updated nginx: ``sudo apt-get install nginx`` - as of now, it is 1.12.1

## Database - MariaDB

1. If you just do ``sudo apt-get install mariadb-server``, you will get version 5.5 of MariaDB
1. Let's install MariaDB 10.2 instead.
1. Update the repositories:
```
sudo apt-get install software-properties-common
sudo apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xF1656F24C74CD1D8
sudo add-apt-repository 'deb [arch=amd64,i386,ppc64el] http://mirror.jmu.edu/pub/mariadb/repo/10.2/ubuntu trusty main'
```
1. Then run: ``sudo apt-get update``
1. And finally, install MariaDB server: ``sudo apt-get install mariadb-server``
1. The output of ``mysql -V`` should have ``Distrib 10.2.7-MariaDB``

## Other Programs

1. Python is pre-installed in Ubuntu, so no need to install it
1. Git: ``sudo apt-get install git``

# Prepare the project

1. If you use Vagrant, then add this rule to the Vagrantfile:
``config.vm.synced_folder "./", "/var/www", owner: "vagrant", group: "vagrant"``
1. The website will be served from ``/var/www/vortech-backend/html``, so create the dir first:
``mkdir -p /var/www/vortech-backend/html``
1. And then we can clone this codebase to that directory:
```
cd /var/www/vortech-backend
git clone https://github.com/Torniojaws/vortech-backend.git html/
```
Now the app will be available in the directory, but before it actually does anything, we must setup
both Nginx and uWSGI.

## Setup Nginx

1. Create a new config for the API. It will run in port 8000.
1. Run: ``sudo vim /etc/nginx/conf.d/vortech-backend.conf``
1. Then make the contents of the file as follows:
```
server {
    listen 8000;
    server_name localhost;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:///var/www/vortech-backend/vortech-backend.sock;
    }
}
```
1. And restart Nginx for the config to take effect: ``sudo service nginx restart``
1. You can now test the new config by opening eg. http://127.0.0.1:8000
1. You should get a ``502 Bad Gateway`` which means the config is OK. It is an error code 502 because
we have not yet setup uWSGI to handle the request, but it means the request did get handled by nginx

## Install Python dependencies

We are now ready to setup all the things related to the actual Python app, so let's install all
dependencies and related tools.

1. Install pip for Python 3: ``sudo apt-get install python3-pip``
1. Then virtualenv: ``sudo apt-get install python-virtualenv``
1. Setup the virtualenv. First, ``cd /var/www/vortech-backend``
1. Then create the virtualenv: ``virtualenv venv``, or if in Vagrant+Windows, use:
``virtualenv venv --always-copy``
1. And activate it: ``source venv/bin/activate``
1. Then go to the subdir for the app: ``cd /var/www/vortech-backend/html``
1. Now, install all the project dependencies (TODO: should not use sudo, but there's Permission
Denied and virtualenv cannot be installed without sudo): ``sudo pip3 install -r requirements/prod.txt``

## Setup uWSGI

uWSGI is installed along with the other Python dependencies above, so we are ready to configure it.

1. First, install the Python 3 plugin: ``sudo apt-get install uwsgi-plugin-python3``
1. Create the config file to our server:
```
cd /var/www/vortech-backend
sudo vim vortech-backend.ini
```
1. Make the contents of that file as follows:
```
[uwsgi]
project = vortech-backend
base = /var/www
chdir = %(base)/%(project)

plugins = python34

home = %(base)/%(project)/venv
module = wsgi:application
master = true
processes = 10

cheaper = 2
cheaper-initial = 5
cheaper-step = 1
cheaper-algo = spare
cheaper-overload = 5

socket = %(base)/%(project)/%(project).sock
chmod-socket = 666
vacuum = true
```
1. Save and close.
1. Then run uwsgi again, using the config file we just made: ``uwsgi --ini vortech-backend.ini``
1. Now, open again the URL from earlier that gave a 502. It should work now: http://127.0.0.1:8000
