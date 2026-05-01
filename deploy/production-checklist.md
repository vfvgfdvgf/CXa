# getsiaq.online launch checklist

## Server

- Create `/var/www/getsiaq`.
- Copy project files to `/var/www/getsiaq`.
- Copy `.env.production.example` to `.env` and set a real `DJANGO_SECRET_KEY`.
- Keep `DJANGO_DEBUG=False` and `DJANGO_PRODUCTION=True`.
- Keep `SITE_URL=https://getsiaq.online`.

## Django

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

## Service

```bash
sudo cp deploy/getsiaq.service /etc/systemd/system/getsiaq.service
sudo systemctl daemon-reload
sudo systemctl enable --now getsiaq
sudo systemctl status getsiaq
```

## Nginx and SSL

```bash
sudo cp deploy/nginx.getsiaq.online.conf /etc/nginx/sites-available/getsiaq.online
sudo ln -s /etc/nginx/sites-available/getsiaq.online /etc/nginx/sites-enabled/getsiaq.online
sudo nginx -t
sudo certbot --nginx -d getsiaq.online -d www.getsiaq.online
sudo systemctl reload nginx
```

## SEO smoke test

- `https://getsiaq.online/robots.txt`
- `https://getsiaq.online/sitemap.xml`
- `https://getsiaq.online/sitemap-images.xml`
- `https://getsiaq.online/archive/`
- `https://getsiaq.online/cost-calculator/`
