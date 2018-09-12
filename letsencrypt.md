# Let's Encrypt setup

Setting up Let's Encrypt with Ansible turned out problematic, so here are the manual steps for it.

## First time install (new server)

1. Create the file `sudo vim /etc/nginx/sites-enabled/vortechmusic.conf` and make its contents:
```
server {
    listen 8080;
    server_name vortechmusic.com www.vortechmusic.com;
    location / {
        try_files $uri $uri/ =404;
    }
}
```
1. Check the Nginx config: `sudo nginx -t`
1. Generate the certs: `sudo certbot --nginx -d vortechmusic.com -d www.vortechmusic.com`
   1. This will ask for some manual steps. Do them as needed.
   1. You can also do it fully manually:
      1. Run: `sudo certbot run -a manual -i nginx -d vortechmusic.com -d www.vortechmusic.com`
      1. Then connect to the server via SSH and place the asked ACME files to:
         `/srv/vortech-backend/html/.well-known/acme-challenge/<some_string>`
1. Two files are generated under `/etc/letsencrypt/live/vortechmusic.com/`
   1. NB: They were once generated under `/etc/letsencrypt/live/vortechmusic.com-0001/`
1. Modify the Nginx config: `sudo vim /etc/nginx/sites-enabled/vortech-backend.conf`
1. Uncomment these three rows there:
```
ssl_certificate /etc/letsencrypt/live/vortechmusic.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/vortechmusic.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/vortechmusic.com/fullchain.pem;
```
1. Remove the temporary config: `sudo rm /etc/nginx/sites-enabled/vortechmusic.conf`
1. Make sure the Nginx config is ok: `sudo nginx -t`
1. Then add the renewal to crontab: `sudo crontab -e`
1. Add this to the crontab: `0 8 1 */2 * /usr/bin/certbot renew --quiet`

## Moving of server

When the server is moved to another provider, it might be enough just to move the existing (valid)
certificates as-is to the new server and place them in the `/etc/letsencrypt/live/vortechmusic.com/`
directory. Remember to setup the crontab.
