# موقع لاندسكيب سعودي

مشروع Django عربي لإدارة موقع خدمات لاندسكيب وتنسيق حدائق داخل السعودية. يدعم الصفحات المحلية للمدن، صفحات خدمة داخل مدينة، المدونة، المشاريع، العملاء المحتملين، لوحة تحكم عربية، ومولد محتوى بالذكاء الاصطناعي.

## التشغيل المحلي

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py generate_local_pages
python manage.py runserver
```

افتح الموقع على:

```text
http://127.0.0.1:8000/
```

## قاعدة البيانات

المشروع مضبوط على SQLite افتراضيًا.

- الملف الافتراضي: `db.sqlite3`
- يمكن تغيير المسار عبر `SQLITE_NAME`

## أهم أوامر الإدارة

```bash
python manage.py generate_local_pages
```

ينشئ المدن والخدمات الافتراضية، ثم يولد صفحات SEO مثل:

- `/riyadh/landscaping/`
- `/jeddah/palm-trees/`
- `/abha/irrigation-maintenance/`

```bash
python manage.py daily_ai_seo --dry-run
```

يجرب مهمة تحسين SEO اليومية بدون حفظ. للحفظ التلقائي يجب تفعيل:

```text
AI_DAILY_SEO_ENABLED=True
OPENAI_API_KEY=...
```

```bash
python manage.py run_seo_automation --skip-ai
python manage.py run_seo_automation --dry-run-ai
python manage.py run_seo_automation --apply-ai
```

`run_seo_automation` هو أمر التشغيل اليومي الشامل. يقوم بالتالي:

- جلب كلمات Google Search Console إذا تم ضبط بيانات الربط.
- توليد صفحات المدن والخدمات الناقصة.
- مزامنة تحويلات الروابط القديمة.
- تشغيل تقرير SEO اليومي وتخزينه في لوحة التحكم.
- تشغيل الذكاء الاصطناعي لتحسين المحتوى عند استخدام `--apply-ai` أو عند تفعيل `ai_seo_auto_apply` من إعدادات الموقع.

لجعله يعمل يوميًا على Windows Task Scheduler استخدم الأمر:

```powershell
python "C:\Users\user\Downloads\مجلد جديد\ZZZ-main\manage.py" run_seo_automation --apply-ai
```

على الاستضافة يمكن تشغيل نفس الأمر كـ Cron Job يومي.

## متغيرات البيئة

انسخ `.env.example` إلى `.env` ثم عدل القيم:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `SITE_DOMAIN`
- `SITE_URL`
- `SQLITE_NAME`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `AI_DAILY_SEO_ENABLED`
- `USE_CLOUDINARY_MEDIA`

## الذكاء الاصطناعي

لوحة التحكم تحتوي مولد محتوى يستطيع:

- إنشاء أو تحديث مقال.
- إنشاء أو تحديث خدمة.
- إنشاء أو تحديث مدينة.
- إنشاء أو تحديث صفحة.
- إنشاء أو تحديث صفحة خدمة داخل مدينة.
- تنفيذ أمر شامل لإضافة عدة مدن وخدمات وصفحات ومقالات من طلب واحد.

## الاختبار

```bash
python manage.py check
python manage.py check --deploy
python manage.py test
python manage.py collectstatic --noinput
```

## Render

The project includes `render.yaml` for deploying `getsiaq.online` from GitHub.

- Render build command installs dependencies and runs `collectstatic`.
- Render start command runs migrations, seeds SEO content, and starts Gunicorn.
- SQLite is configured for `/var/data/db.sqlite3` on a persistent Render disk.
- Uploaded media is configured for `/var/data/media` on the same disk.

See `deploy/render.md` for the GitHub and Render steps.
