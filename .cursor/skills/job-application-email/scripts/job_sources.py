#!/usr/bin/env python3
"""从公司官网/RSS/JSON/本地 fixture 采集招聘岗位。"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse


USER_AGENT = "job-application-email-skill/2.0 (+job-digest)"


@dataclass
class JobPosting:
    job_id: str
    company_id: str
    company_name: str
    title: str
    url: str
    source_type: str
    published: str = ""
    location: str = ""
    snippet: str = ""
    website: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_job_id(company_id: str, title: str, url: str) -> str:
    raw = f"{company_id}|{title.strip().lower()}|{url.strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def fetch_url(url: str, timeout: float = 25.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def parse_rss(xml_text: str, company_id: str, company_name: str) -> list[JobPosting]:
    root = ET.fromstring(xml_text)
    items: list[JobPosting] = []
    nodes = []
    for el in root.iter():
        if _local_name(el.tag).lower() in {"item", "entry"}:
            nodes.append(el)
    for node in nodes:
        title = ""
        link = ""
        published = ""
        summary = ""
        for child in list(node):
            name = _local_name(child.tag).lower()
            text = (child.text or "").strip()
            if name == "title":
                title = unescape(text)
            elif name == "link":
                href = child.attrib.get("href") or text
                link = href.strip()
            elif name in {"pubdate", "published", "updated"}:
                published = text
            elif name in {"description", "summary", "content"}:
                summary = re.sub(r"<[^>]+>", "", unescape(text))[:200]
        if not title:
            continue
        if not link:
            continue
        items.append(
            JobPosting(
                job_id=make_job_id(company_id, title, link),
                company_id=company_id,
                company_name=company_name,
                title=title,
                url=link,
                source_type="rss",
                published=published,
                snippet=summary,
            )
        )
    return items


def parse_html_regex(
    html: str,
    *,
    company_id: str,
    company_name: str,
    base_url: str,
    item_regex: str,
) -> list[JobPosting]:
    """item_regex 需包含命名组 title 与 url。"""
    pattern = re.compile(item_regex, re.I | re.S)
    jobs: list[JobPosting] = []
    seen: set[str] = set()
    for m in pattern.finditer(html):
        title = unescape(m.group("title")).strip()
        url = m.group("url").strip()
        if not title or not url:
            continue
        url = urljoin(base_url, url)
        jid = make_job_id(company_id, title, url)
        if jid in seen:
            continue
        seen.add(jid)
        jobs.append(
            JobPosting(
                job_id=jid,
                company_id=company_id,
                company_name=company_name,
                title=title,
                url=url,
                source_type="html_regex",
            )
        )
    return jobs


def parse_json_jobs(
    payload: Any,
    *,
    company_id: str,
    company_name: str,
    list_key: str | None,
    title_key: str,
    url_key: str,
    base_url: str = "",
) -> list[JobPosting]:
    if list_key:
        data = payload.get(list_key) if isinstance(payload, dict) else None
    else:
        data = payload
    if not isinstance(data, list):
        return []
    jobs: list[JobPosting] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        title = str(row.get(title_key) or "").strip()
        url = str(row.get(url_key) or "").strip()
        if not title or not url:
            continue
        if base_url and not urlparse(url).scheme:
            url = urljoin(base_url, url)
        jobs.append(
            JobPosting(
                job_id=make_job_id(company_id, title, url),
                company_id=company_id,
                company_name=company_name,
                title=title,
                url=url,
                source_type="json",
                location=str(row.get("location") or ""),
                published=str(row.get("published") or row.get("date") or ""),
                snippet=str(row.get("snippet") or row.get("description") or "")[:200],
            )
        )
    return jobs


def load_fixture(path: Path, company_id: str, company_name: str) -> list[JobPosting]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return parse_json_jobs(
        data,
        company_id=company_id,
        company_name=company_name,
        list_key="jobs" if isinstance(data, dict) and "jobs" in data else None,
        title_key="title",
        url_key="url",
    )


NAV_DENY = {
    "首页",
    "登录",
    "招聘动态",
    "了解我们",
    "社会招聘",
    "校招须知",
    "岗位投递",
    "立即投递",
    "一键投递",
    "更多",
    "返回",
    "注册",
}


def scrape_playwright(
    careers_url: str,
    *,
    company_id: str,
    company_name: str,
    timeout: float = 60.0,
    wait_ms: int = 6000,
) -> list[JobPosting]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("playwright not installed; pip install playwright && playwright install chromium") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": USER_AGENT})
        page.goto(careers_url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
        page.wait_for_timeout(wait_ms)
        for label in ("职位", "岗位列表", "全部职位", "校园招聘职位", "查看职位"):
            try:
                loc = page.get_by_text(label, exact=False).first
                if loc.is_visible(timeout=1500):
                    loc.click(timeout=2000)
                    page.wait_for_timeout(3500)
                    break
            except Exception:  # noqa: BLE001
                continue
        raw = page.evaluate(
            """() => {
              const out = [];
              const seen = new Set();
              document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href || '';
                if (!/^https?:/i.test(href)) return;
                const full = (a.innerText || '').trim().replace(/\\s+/g, ' ');
                if (!full) return;
                const title = full.split('\\n').map(s => s.trim()).filter(Boolean)[0] || full.slice(0, 80);
                if (title.length < 2 || title.length > 120) return;
                const key = href + '|' + title;
                if (seen.has(key)) return;
                seen.add(key);
                out.push({ title, url: href, snippet: full.slice(0, 400) });
              });
              return out;
            }"""
        )
        browser.close()

    jobs: list[JobPosting] = []
    for item in raw or []:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if not title or not url:
            continue
        if title in NAV_DENY:
            continue
        if any(d == title for d in NAV_DENY):
            continue
        jobs.append(
            JobPosting(
                job_id=make_job_id(company_id, title, url),
                company_id=company_id,
                company_name=company_name,
                title=title,
                url=url,
                source_type="playwright",
                snippet=str(item.get("snippet") or "")[:400],
            )
        )
    return jobs


def match_keywords(title: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    t = title.lower()
    return any(k.lower() in t for k in keywords if k.strip())


def collect_from_row(
    row: dict[str, str],
    *,
    skill_root: Path,
    timeout: float = 25.0,
    global_keywords: list[str] | None = None,
    playwright_wait_ms: int = 6000,
) -> tuple[list[JobPosting], str | None]:
    """返回 (jobs, error_message)。"""
    company_id = (row.get("company_id") or "").strip()
    company_name = (row.get("company_name") or "").strip() or company_id
    source_type = (row.get("source_type") or "rss").strip().lower()
    careers_url = (row.get("careers_url") or row.get("website") or "").strip()
    website = (row.get("website") or careers_url).strip()
    row_kw = [k.strip() for k in (row.get("keywords") or "").split("|") if k.strip()]
    keywords = row_kw or list(global_keywords or [])

    try:
        if source_type == "fixture":
            fixture_path = Path(careers_url)
            if not fixture_path.is_absolute():
                fixture_path = (skill_root / careers_url).resolve()
            jobs = load_fixture(fixture_path, company_id, company_name)
        elif source_type == "rss":
            if not careers_url:
                return [], "careers_url missing"
            xml_text = fetch_url(careers_url, timeout=timeout)
            jobs = parse_rss(xml_text, company_id, company_name)
        elif source_type == "html_regex":
            if not careers_url:
                return [], "careers_url missing"
            item_regex = (row.get("item_regex") or "").strip()
            if not item_regex:
                return [], "item_regex required for html_regex"
            html = fetch_url(careers_url, timeout=timeout)
            jobs = parse_html_regex(
                html,
                company_id=company_id,
                company_name=company_name,
                base_url=careers_url,
                item_regex=item_regex,
            )
        elif source_type == "json":
            if not careers_url:
                return [], "careers_url missing"
            raw = fetch_url(careers_url, timeout=timeout)
            payload = json.loads(raw)
            jobs = parse_json_jobs(
                payload,
                company_id=company_id,
                company_name=company_name,
                list_key=(row.get("json_list_key") or "").strip() or None,
                title_key=(row.get("json_title_key") or "title").strip(),
                url_key=(row.get("json_url_key") or "url").strip(),
                base_url=careers_url,
            )
        elif source_type == "playwright":
            if not careers_url:
                return [], "careers_url missing"
            jobs = scrape_playwright(
                careers_url,
                company_id=company_id,
                company_name=company_name,
                timeout=max(timeout, 60.0),
                wait_ms=playwright_wait_ms,
            )
        else:
            return [], f"unsupported source_type: {source_type}"
    except Exception as exc:  # noqa: BLE001
        return [], f"{type(exc).__name__}: {exc}"

    filtered: list[JobPosting] = []
    for j in jobs:
        if match_keywords(j.title, keywords):
            j.website = website
            filtered.append(j)
    return filtered, None
