Deployment notes for `getsiaq.online`

The project reads production settings from environment variables. Do not commit real secrets.

1. Prepare environment

Copy the production example and fill the real secret values:

```bash
cp .env.production.example .env
```

Required values:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS=getsiaq.online,www.getsiaq.online`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://getsiaq.online,https://www.getsiaq.online`
- `SITE_DOMAIN=getsiaq.online`
- `WWW_SITE_DOMAIN=www.getsiaq.online`
- `SITE_URL=https://getsiaq.online`
- `DATABASE_URL=postgresql://...` for PostgreSQL on Render. Use Render's internal URL only when the web service and database can reach each other on Render's private network; otherwise use the external URL.
- `SQLITE_NAME=db.sqlite3` or an absolute persistent path
- `OPENAI_API_KEY` only if AI generation is enabled

2. Install dependencies

```bash
python --version
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Use Python 3.12 on managed hosts that read `runtime.txt`.

3. Run production preparation

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

4. Gunicorn

Example command:

```bash
gunicorn project.wsgi:application --workers 3 --bind 0.0.0.0:8000 --log-file -
```

Example `systemd` service:

```ini
[Unit]
Description=gunicorn daemon for getsiaq.online
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/project
EnvironmentFile=/path/to/project/.env
ExecStart=/path/to/project/.venv/bin/gunicorn project.wsgi:application --workers 3 --bind unix:/run/getsiaq.sock --log-file -

[Install]
WantedBy=multi-user.target
```

5. Nginx

```nginx
server {
    server_name getsiaq.online www.getsiaq.online;

    location /static/ {
        alias /path/to/project/staticfiles_build/;
    }

    location /media/ {
        alias /path/to/project/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/getsiaq.sock;
    }
}
```

6. Final checks after DNS and SSL

- Open `https://getsiaq.online/`
- Open `https://getsiaq.online/robots.txt`
- Open `https://getsiaq.online/sitemap.xml`
- Open `https://getsiaq.online/sitemap-images.xml`
- Test WhatsApp and call buttons
- Test admin login over HTTPS only

7. DNS notes

- Point `getsiaq.online` to the hosting server.
- Point `www.getsiaq.online` to the same server, usually with a CNAME.
- Install SSL before enabling strict redirects in production.
