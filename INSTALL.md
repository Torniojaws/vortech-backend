# Project setup instructions

Follow the instructions below to setup the project into an "empty" platform, which is assumed to be
Ubuntu 18.04 64-bit. Tested on a Virtualbox running Ubuntu 16.04, also.

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
1. Apache seems to run by default in Ubuntu 16.04, so stop it: ``sudo systemctl stop apache2.service``
1. Update apt: ``sudo apt-get update``
1. Then install the first pieces:
``sudo apt install virtualenv python3 uwsgi uwsgi-emperor uwsgi-plugin-python3 nginx-full git zip``
1. And the database of course: ``sudo apt install mariadb-server``
    1. Note that the install process is different in Ubuntu 16.04 than in previous versions. The
    installer will not prompt for root password. Instead, you access it using ``sudo mysql -u root``
1. For caching, we use Redis. Install it with: ``sudo apt install redis-server``

## Setup the app

1. Create the dir where the app will be: ``sudo mkdir -p /srv/vortech-backend``
1. Enter the dir: ``cd /srv/vortech-backend``
1. And add a virtualenv there: ``sudo virtualenv -p /usr/bin/python3 venv``
1. Then clone the project there:
``sudo git clone https://github.com/Torniojaws/vortech-backend.git html/``
1. Then we will install the project requirements, but first you need to install the essential tools:
``sudo apt-get install build-essential python3-dev``
1. Activate the virtualenv: ``source /srv/vortech-backend/venv/bin/activate``
1. Change to the project dir: ``cd /srv/vortech-backend/html``
1. And then install the requirements:
``sudo /srv/vortech-backend/venv/bin/pip install -r requirements/prod.txt``
1. Create the logs dir that is *required* by nginx: ``sudo mkdir /srv/vortech-backend/logs``
1. And finally, change the owner of the app dir:
``sudo chown -R www-data:www-data /srv/vortech-backend``

## Configure uWSGI

1. Let's create the config: ``sudo vim /etc/uwsgi-emperor/vassals/vortech-backend.ini``
1. Make the contents as follows:
    ```
    [uwsgi]
    project = vortech-backend
    socket = /srv/%(project)/uwsgi.sock
    chmod-socket = 666

    chdir = /srv/%(project)/html
    master = true
    virtualenv = /srv/%(project)/venv
    binary-path = %(virtualenv)/bin/uwsgi

    module = wsgi:application
    uid = www-data
    gid = www-data

    processes = 10
    cheaper = 2
    cheaper-initial = 5
    cheaper-step = 1
    cheaper-algo = spare
    cheaper-overload = 5

    plugins = python3, logfile
    logger = file:/srv/%(project)/uwsgi.log
    vacuum = true
    ```

## Setup Nginx

1. Let's create our config: ``sudo vim /etc/nginx/sites-enabled/vortech-backend.conf``
1. Make the contents of the file as follows:
    ```
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;

        # These are commented out until we have run the certbot for the first time. Otherwise it will
        # fail with a Nginx config error. It comes because these two *.pem files do not exist until
        # we have run certbot :)
        # ssl_certificate /etc/letsencrypt/live/vortechmusic.com/fullchain.pem;
        # ssl_certificate_key /etc/letsencrypt/live/vortechmusic.com/privkey.pem;
        ssl_session_cache shared:SSL:20m;
        ssl_session_timeout 180m;
        ssl_session_tickets off;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_prefer_server_ciphers on;
        ssl_ciphers ECDH+AESGCM:ECDH+AES256:ECDH+AES128:DHE+AES128:!ADH:!AECDH:!MD5;
        ssl_dhparam /etc/nginx/cert/dhparam.pem;

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";

        # Deters click-jacking
        add_header X-Frame-Options SAMEORIGIN;

        # Deters MIME-type confusion attacks
        add_header X-Content-Type-Options nosniff;

        # OCSP stapling
        ssl_stapling on;
        ssl_stapling_verify on;
        # This is also commented out until we run certbot for the first time
        # ssl_trusted_certificate /etc/letsencrypt/live/vortechmusic.com/fullchain.pem;
        resolver 8.8.8.8 8.8.4.4;

        # Root location
        root /srv/vortech-backend/html;
        index index.html index.htm;

        access_log /srv/vortech-backend/logs/access.log;
        error_log /srv/vortech-backend/logs/error.log;

        location / {
            include uwsgi_params;
            uwsgi_pass unix:/srv/vortech-backend/uwsgi.sock;
        }

        # Prevent serving files beginning with a “.”
        # Do not log attempt
        location ~ /\. {
            access_log off;
            log_not_found off;
            deny all;
        }

        # Prevent serving files beginning with a “$”
        # Do not log attempt
        location ~ ~$ {
            access_log off;
            log_not_found off;
            deny all;
        }

        # Prevent logging whenever favicon & robots.txt files are accessed
        location = /robots.txt {
            log_not_found off;
        }

        location = /favicon.ico {
            access_log off;
            log_not_found off;
        }
    }

    # Redirect all HTTP traffic to HTTPS
    # Always redirect to www.<domain_name>, not bare-domain (without "www") according to SEO best-practices
    # If you are in Vagrant, comment this out if you use "localhost". Otherwise there's an infinite loop
    server {
        listen 80;
        listen [::]:80;

        return 301 https://www.vortechmusic.com$request_uri;
    }

    # Redirect bare-domain HTTPS to https://www.vortechmusic.com
    # If you are in Vagrant, comment this out if you use "localhost". Otherwise there's an infinite loop
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;

        server_name vortechmusic.com www.vortechmusic.com;
        return 301 https://www.vortechmusic.com$request_uri;
    }
    ```
1. There are a lot of special files in /etc/nginx/cert/ and some other things. So, let's do them.
1. First, create a DH parameters file. Before it starts, we need to create the dir and file with:
    ```
    sudo mkdir -p /etc/nginx/cert
    sudo touch /etc/nginx/cert/dhparam.pem
    ```
1. Then create the file contents: ``sudo openssl dhparam 2048 -out /etc/nginx/cert/dhparam.pem``
It will take about 2 minutes to finish.
1. Then, for the below steps we will need Certbot from Let's Encrypt.
1. Install add-apt-repository: ``sudo apt-get install software-properties-common``
1. Setup the repository: ``sudo add-apt-repository ppa:certbot/certbot``
1. Update: ``sudo apt-get update``
1. Install: ``sudo apt-get install python-certbot-nginx``
1. When you run Certbot for the first time, we need to do some special steps (as follows).
1. Create a new config: ``sudo vim /etc/nginx/sites-enabled/vortechmusic.conf``
1. Make the contents of that file like this:
    ```
    server {
        listen 8080;
        server_name vortechmusic.com www.vortechmusic.com;
        location / {
            try_files $uri $uri/ =404;
        }
    }
    ```
1. Save and close.
1. Verify that nginx config is OK: ``sudo nginx -t``
1. Then generate the certs: ``sudo certbot --nginx -d vortechmusic.com -d www.vortechmusic.com``
    1. In Vagrant, the easiest way is to run:
    ``sudo certbot run -a manual -i nginx -d vortechmusic.com -d www.vortechmusic.com``
    1. Note that it will require you to create files manually in the real host. After you run the
    command, it will tell you how to do it. Basically a random string in
    ``../public_html/.well-known/acme-challenge/<some_string>`` with a second random string as its
    contents
1. There will be two files generated, which you should use as follows. Make sure the path is the
same that the actual file. It has sometimes appeared in
**/etc/letsencrypt/live/vortechmusic.com-0001/privkey.pem** instead of the below. In that case, use
the -0001 one.
    ```
    ssl_certificate /etc/letsencrypt/live/vortechmusic.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vortechmusic.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/vortechmusic.com/fullchain.pem;
    ```
1. So let's uncomment those rows from the config:
``sudo vim /etc/nginx/sites-enabled/vortech-backend.conf``
1. Find the above three rows and uncomment them. Then save and close.
1. Remove the unneeded config: ``sudo rm /etc/nginx/sites-enabled/vortechmusic.conf``
1. At this point, you might make sure the Nginx config is OK: ``sudo nginx -t``
1. Let's also setup the automatic renewal of the certificates: ``sudo crontab -e``
1. Add this line to it: ``0 8 1 */2 * /usr/bin/certbot renew --quiet``. It will renew the
certificates on Day 1 of every second month at 08:00, eg. 1 September at 08:00, 1 November at 08:00

## uWSGI Emperor setup

Emperor is used to manage multiple sites, but it also has some nice features that a single site
server benefits from. For example automatic restarting of hung sites.

1. Let's create by destroying. We want to use systemd instead of LSB:
    ```
    sudo systemctl stop uwsgi-emperor
    sudo systemctl disable uwsgi-emperor
    ```
1. Then create the new config: ``sudo vim /etc/systemd/system/emperor.uwsgi.service`` and make the
contents of the file as follows:
    ```
    [Unit]
    Description=uWSGI Emperor
    After=syslog.target

    [Service]
    ExecStart=/usr/bin/uwsgi --ini /etc/uwsgi-emperor/emperor.ini
    # Requires systemd version 211 or newer
    RuntimeDirectory=uwsgi
    Restart=always
    KillSignal=SIGQUIT
    Type=notify
    StandardError=syslog
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target
    ```
1. Save and close.
1. Then start the brand new emperor:
    ```
    sudo systemctl daemon-reload
    sudo systemctl enable nginx emperor.uwsgi
    sudo systemctl reload nginx
    sudo systemctl start emperor.uwsgi
    ```
1. Check that it is running: ``sudo systemctl status emperor.uwsgi``

## Configure the database

As mentioned in the beginning, you will now access the root user with ``sudo mysql -u root``. Run
that now and let's create our database user and an empty database. The database structure will be
built by Flask Migrate.

1. Create the database: ``CREATE DATABASE vortech;``
1. Create the user: ``CREATE USER vortech@'localhost' IDENTIFIED BY 'somepassword';``
1. And give it grants: ``GRANT ALL ON vortech.* TO vortech@'localhost';``
1. And then we will build the structure with Flask Migrate. First, let's create the config file:
1. Run ``cd /srv/vortech-backend/html`` and then ``sudo cp settings/secret.sample settings/secret.cfg``
1. And then edit the ``secret.cfg`` to the settings you defined for the database
1. Then activate the virtualenv, if it's not active: ``source /srv/vortech-backend/venv/bin/activate``
1. Now we can build the database structure.
1. In production, run ``flask db upgrade`` to make the database up-to-date with the code.
1. In Vagrant, if you start from scratch, you need to temporarily
``sudo chown vagrant:vagrant html/``.
1. Then in Vagrant, run:
    ```
    # This reads the registered DB models and initializes the migration
    flask db init

    # This builds the migration files, which will be added to the repo.
    # They are used to build the DB structure in other computers where the repo is cloned to
    flask db migrate -m "Creating all tables"

    # This builds the database tables based on the migration files
    flask db upgrade
    ```

## Setup local DB for development

1. Create a new User through the register page http://localhost:5000/register
1. To make the user an admin, run this into the DB:
  ``INSERT INTO UsersAccessMapping(UserID, UsersAccessLevelID) VALUES(1, 4);``
   Replace the ``1`` with the actual Users.UserID you have locally. Should usually be ``1``.

## Final words for production

Whenever you make changes to the app, you might need to "refresh" uWSGI to update the page that it
serves. Otherwise you will see the old page.
Run ``sudo touch --no-dereference /etc/uwsgi-emperor/vassals/vortech-backend.ini``
