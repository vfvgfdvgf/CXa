import json
import os
import re
from urllib.parse import quote_plus

import requests
from django.core.management.base import BaseCommand, CommandError

from core.ai_content import (
    OPENAI_API_URL,
    _get_openai_api_key,
    _get_openai_model,
    _json_loads_maybe,
    save_bulk_generated_content,
)
from core.models import BlogPost, City, CityServicePage, SearchConsoleQuery, Service, SiteSettings


def _strip_tags(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()


def search_web(query, limit=3):
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    response.raise_for_status()
    snippets = []
    for match in re.finditer(r'<a rel="nofollow" class="result__a".*?>(.*?)</a>.*?<a class="result__snippet".*?>(.*?)</a>', response.text, re.S):
        title = _strip_tags(match.group(1))
        snippet = _strip_tags(match.group(2))
        if title or snippet:
            snippets.append({"title": title, "snippet": snippet})
        if len(snippets) >= limit:
            break
    return snippets


def build_site_snapshot():
    settings_obj = SiteSettings.load()
    return {
        "site_name": settings_obj.site_name,
        "services": list(Service.objects.filter(is_visible=True).values("title", "slug", "meta_title", "meta_description")[:30]),
        "cities": list(City.objects.filter(is_active=True).values("name", "slug", "region", "meta_title", "meta_description")[:50]),
        "local_pages": list(
            CityServicePage.objects.filter(is_active=True)
            .select_related("city", "service")
            .values("city__name", "city__slug", "service__title", "service__slug", "custom_slug", "meta_title", "meta_description")[:80]
        ),
        "recent_posts": list(BlogPost.objects.order_by("-created_at").values("title", "slug", "meta_title", "meta_description")[:20]),
        "search_console_queries": list(
            SearchConsoleQuery.objects.order_by("-impressions", "position").values(
                "query", "page", "clicks", "impressions", "ctr", "position", "date_from", "date_to"
            )[:80]
        ),
    }


def request_ai_seo_update(prompt, research, dry_run=False):
    api_key = _get_openai_api_key()
    if not api_key:
        raise CommandError("OPENAI_API_KEY is required for daily AI SEO.")

    body = {
        "model": _get_openai_model(),
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "أنت محرر SEO عربي لموقع خدمات لاندسكيب في السعودية. "
                            "حلل بيانات الموقع وملخصات البحث، ثم أخرج JSON فقط يحتوي مفاتيح: "
                            "cities, services, city_services, pages, blog_posts, site_settings. "
                            "لا تخترع أسعارًا أو وعودًا غير موجودة. لا تحذف محتوى، حسّن وأضف فقط."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(
                            {
                                "instruction": prompt,
                                "site_snapshot": build_site_snapshot(),
                                "web_research": research,
                            },
                            ensure_ascii=False,
                        ),
                    }
                ],
            },
        ],
        "max_output_tokens": 5000,
    }
    response = requests.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=body,
        timeout=180,
    )
    if response.status_code >= 400:
        raise CommandError(f"OpenAI request failed: {response.text}")
    result = response.json()
    raw_text = result.get("output_text") or ""
    if not raw_text:
        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    raw_text = content.get("text", "")
                    break
            if raw_text:
                break
    payload = _json_loads_maybe(raw_text)
    if dry_run:
        return payload
    return save_bulk_generated_content(payload, publish_now=True)


class Command(BaseCommand):
    help = "Research the web and ask AI to improve local SEO content. Intended for daily schedulers."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print the AI JSON instead of saving it.")
        parser.add_argument("--query", action="append", help="Extra research query. Can be passed multiple times.")

    def handle(self, *args, **options):
        if not options["dry_run"] and os.environ.get("AI_DAILY_SEO_ENABLED", "false").lower() not in {"1", "true", "yes", "on"}:
            raise CommandError("Set AI_DAILY_SEO_ENABLED=True to allow automatic SEO edits.")

        queries = options["query"] or [
            "تنسيق حدائق السعودية لاندسكيب",
            "تصميم حدائق فلل السعودية",
            "زراعة نخيل وأشجار حدائق السعودية",
            "أنظمة ري حدائق السعودية",
        ]
        research = []
        for query in queries:
            try:
                research.append({"query": query, "results": search_web(query)})
            except Exception as exc:
                research.append({"query": query, "error": str(exc), "results": []})

        prompt = (
            "حسّن SEO المحلي للموقع اليوم. اقترح تحديثات واقعية لعناوين ووصف صفحات المدن والخدمات، "
            "وأضف مقالة أو مقالتين إذا وجدت فجوة محتوى واضحة من ملخصات البحث."
        )
        result = request_ai_seo_update(prompt, research, dry_run=options["dry_run"])
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
