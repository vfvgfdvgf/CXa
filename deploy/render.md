# Render deployment for getsiaq.online

## GitHub

Create a clean Git repository from this project directory, not from `C:\Users\user`.

```bash
cd "C:\Users\user\Downloads\مجلد جديد\ZZZ-main"
git init
git add .
git commit -m "Prepare getsiaq.online for Render"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Render Blueprint

1. Open Render Dashboard.
2. Choose **New +** then **Blueprint**.
3. Connect the GitHub repository.
4. Render will read `render.yaml`.
5. Add the custom domains:
   - `getsiaq.online`
   - `www.getsiaq.online`
6. Put Render DNS records inside your domain provider.

## Important Render notes

- SQLite database is stored at `/var/data/db.sqlite3`.
- Uploaded media is stored at `/var/data/media`.
- The persistent disk in `render.yaml` keeps database and uploads between deploys.
- The start command runs migrations and seeds SEO content before starting Gunicorn.
- Keep `OPENAI_API_KEY` empty unless you want AI content generation.

## After deploy

Open:

- `https://getsiaq.online/`
- `https://getsiaq.online/robots.txt`
- `https://getsiaq.online/sitemap.xml`
- `https://getsiaq.online/sitemap-images.xml`
- `https://getsiaq.online/archive/`

Then submit `https://getsiaq.online/sitemap.xml` in Google Search Console.
