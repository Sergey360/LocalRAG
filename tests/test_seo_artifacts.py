import json
import re
import xml.etree.ElementTree as ET

import main
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def extract_json_ld(html_text: str) -> dict:
    match = re.search(
        r'<script type="application/ld\+json">(?P<payload>.*?)</script>',
        html_text,
        flags=re.DOTALL,
    )
    assert match, "JSON-LD script tag is missing"
    return json.loads(match.group("payload"))


def test_index_page_renders_localized_seo_metadata_and_schema():
    resp = client.get("/", cookies={"lang": "ru"})

    assert resp.status_code == 200
    assert resp.headers["X-Robots-Tag"] == "noindex,follow"
    assert '<html lang="ru" dir="ltr">' in resp.text
    assert "<title>Локальный ИИ-поиск по документам - LocalRAG</title>" in resp.text
    assert '<meta name="robots" content="noindex,follow">' in resp.text
    assert '<link rel="canonical" href="https://localrag.dev/">' in resp.text
    assert '<meta property="og:locale" content="ru_RU">' in resp.text
    assert "Проверяйте ответы по найденным фрагментам источников" in resp.text

    schema = extract_json_ld(resp.text)
    assert schema["@type"] == "SoftwareApplication"
    assert schema["name"] == "LocalRAG"
    assert schema["url"] == "https://localrag.dev/"
    assert schema["softwareVersion"] == main.APP_VERSION
    assert schema["inLanguage"] == "ru"
    assert "aggregateRating" not in schema
    assert "offers" not in schema
    assert any("FAISS retrieval" in item for item in schema["featureList"])


def test_index_page_sets_hebrew_lang_and_direction():
    resp = client.get("/", cookies={"lang": "he"})

    assert resp.status_code == 200
    assert '<html lang="he" dir="rtl">' in resp.text
    assert '<meta property="og:locale" content="he_IL">' in resp.text


def test_robots_and_sitemap_default_to_non_indexed_app_surface():
    robots = client.get("/robots.txt")
    sitemap = client.get("/sitemap.xml")

    assert robots.status_code == 200
    assert robots.headers["content-type"].startswith("text/plain")
    assert "User-agent: *" in robots.text
    assert "Disallow: /" in robots.text
    assert "Sitemap:" not in robots.text

    assert sitemap.status_code == 200
    root = ET.fromstring(sitemap.text)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    assert root.findall("sm:url", namespace) == []


def test_indexed_seo_mode_exposes_root_in_robots_and_sitemap(monkeypatch):
    monkeypatch.setattr(main, "SEO_INDEX_APP", True)

    index = client.get("/")
    robots = client.get("/robots.txt")
    sitemap = client.get("/sitemap.xml")

    assert '<meta name="robots" content="index,follow">' in index.text
    assert index.headers["X-Robots-Tag"] == "index,follow"
    assert "Allow: /" in robots.text
    assert "Disallow: /api/" in robots.text
    assert "Disallow: /docs" in robots.text
    assert "Sitemap: https://localrag.dev/sitemap.xml" in robots.text

    root = ET.fromstring(sitemap.text)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = root.findall("sm:url", namespace)
    assert len(urls) == 1
    assert urls[0].find("sm:loc", namespace).text == "https://localrag.dev/"
