#!/usr/bin/env python3
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional, Sequence
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 15
MAX_RESULTS = 10
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

BLOCKLIST_HOST_KEYWORDS = (
    "go.microsoft.com",
)

BLOCKLIST_TITLE_KEYWORDS = (
    "隐私",
    "法律声明",
    "广告",
    "Cookie",
    "许可证",
    "公安",
    "ICP",
)


@dataclass
class SearchResult:
    rank: int
    title: str
    url: str
    snippet: str
    engine: str


class WebSearchChina:
    def __init__(self) -> None:
        self.session = requests.Session()
        retry = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
                "Connection": "keep-alive",
            }
        )
        self.engines: Dict[str, Callable[[str, int], List[dict]]] = {
            "baidu": self._search_baidu,
            "bing": self._search_bing,
            "360": self._search_360,
        }

    def search(self, query: str, engine: str = "auto", count: int = 5) -> List[SearchResult]:
        query = (query or "").strip()
        if not query:
            raise ValueError("query is required")

        count = max(1, min(int(count), MAX_RESULTS))
        plan: Sequence[str] = [engine] if engine in self.engines else ["baidu"]
        if engine == "auto":
            plan = ["bing", "360", "baidu"]

        seen = set()
        merged: List[SearchResult] = []

        for eng in plan:
            try:
                raw_results = self.engines[eng](query, count)
            except Exception:
                continue
            for item in raw_results:
                normalized = self._normalize_result(item, eng)
                if not normalized:
                    continue
                if normalized.url in seen:
                    continue
                seen.add(normalized.url)
                merged.append(normalized)
                if len(merged) >= count:
                    return self._rerank(merged)

        return self._rerank(merged)

    def _rerank(self, items: List[SearchResult]) -> List[SearchResult]:
        out = []
        for idx, item in enumerate(items, start=1):
            item.rank = idx
            out.append(item)
        return out

    def _get(self, url: str, *, headers: Optional[dict] = None) -> requests.Response:
        resp = self.session.get(url, timeout=DEFAULT_TIMEOUT, allow_redirects=True, headers=headers)
        resp.raise_for_status()
        return resp

    def _normalize_result(self, item: dict, engine: str) -> Optional[SearchResult]:
        title = self._clean_text(item.get("title", ""))
        url = (item.get("url") or "").strip()
        snippet = self._clean_text(item.get("snippet", ""))

        if not title or len(title) < 4:
            return None
        if not self._is_valid_public_url(url):
            return None
        if any(k.lower() in title.lower() for k in BLOCKLIST_TITLE_KEYWORDS):
            return None
        if any(k in url.lower() for k in BLOCKLIST_HOST_KEYWORDS):
            return None

        return SearchResult(rank=0, title=title, url=url, snippet=snippet, engine=engine)

    def _is_valid_public_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        host = parsed.netloc.lower()
        if host.startswith("localhost") or host.startswith("127.") or host.startswith("0."):
            return False
        if host.endswith(".local"):
            return False
        return True

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip())

    def _extract_links_generic(self, html: str, count: int) -> List[dict]:
        matches = re.findall(r'<a[^>]+href="(https?://[^"#]+)"[^>]*>(.*?)</a>', html, flags=re.I | re.S)
        out = []
        seen = set()
        for href, title_html in matches:
            title = self._clean_text(BeautifulSoup(title_html, "html.parser").get_text(" ", strip=True))
            if not href or not title or href in seen:
                continue
            seen.add(href)
            out.append({"title": title, "url": href, "snippet": ""})
            if len(out) >= count:
                break
        return out

    def _search_baidu(self, query: str, count: int) -> List[dict]:
        self._get("https://www.baidu.com", headers={"User-Agent": USER_AGENT})
        url = f"https://www.baidu.com/s?wd={quote_plus(query)}&rn={count}"
        resp = self._get(url, headers={"User-Agent": USER_AGENT})
        if "百度安全验证" in resp.text or "网络不给力，请稍后重试" in resp.text:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        seen = set()

        for item in soup.select(".result, .c-container, .result-op"):
            title_elem = item.select_one("h3 a, a")
            if not title_elem:
                continue
            title = title_elem.get_text(" ", strip=True)
            href = (title_elem.get("href") or "").strip()
            snippet_elem = item.select_one(".c-abstract, .c-color-text, .content-right, .abstract")
            snippet = snippet_elem.get_text(" ", strip=True) if snippet_elem else item.get_text(" ", strip=True)[:160]
            if href and title and href not in seen:
                seen.add(href)
                results.append({"title": title, "url": href, "snippet": snippet})
                if len(results) >= count:
                    return results

        if not results:
            return self._extract_links_generic(resp.text, count)
        return results

    def _search_bing(self, query: str, count: int) -> List[dict]:
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9"}
        rss_url = f"https://www.bing.com/search?format=rss&q={quote_plus(query)}&count={count}&cc=cn"
        resp = requests.get(rss_url, timeout=DEFAULT_TIMEOUT, allow_redirects=True, headers=headers)
        resp.raise_for_status()

        results = []
        seen = set()
        try:
            root = ET.fromstring(resp.text)
            for item in root.findall("./channel/item"):
                title = self._clean_text(item.findtext("title") or "")
                href = (item.findtext("link") or "").strip()
                snippet = self._clean_text(item.findtext("description") or "")
                if href and title and href not in seen:
                    seen.add(href)
                    results.append({"title": title, "url": href, "snippet": snippet})
                    if len(results) >= count:
                        return results
        except ET.ParseError:
            pass

        html_url = f"https://cn.bing.com/search?q={quote_plus(query)}&count={count}&cc=cn"
        html_resp = requests.get(html_url, timeout=DEFAULT_TIMEOUT, allow_redirects=True, headers=headers)
        html_resp.raise_for_status()
        soup = BeautifulSoup(html_resp.text, "html.parser")

        for item in soup.select(".b_algo, li[data-bm], .b_ans"):
            title_elem = item.select_one("h2 a, .b_title a")
            if not title_elem:
                continue
            title = title_elem.get_text(" ", strip=True)
            href = (title_elem.get("href") or "").strip()
            snippet_elem = item.select_one(".b_caption p, .b_snippet, p")
            snippet = snippet_elem.get_text(" ", strip=True) if snippet_elem else item.get_text(" ", strip=True)[:160]
            if href and title and href not in seen:
                seen.add(href)
                results.append({"title": title, "url": href, "snippet": snippet})
                if len(results) >= count:
                    break

        return results

    def _search_360(self, query: str, count: int) -> List[dict]:
        self._get("https://www.so.com", headers={"User-Agent": USER_AGENT})
        url = f"https://www.so.com/s?q={quote_plus(query)}&pn=1"
        resp = self._get(url, headers={"User-Agent": USER_AGENT})
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        seen = set()

        for item in soup.select("li.res-list"):
            title_elem = item.select_one("h3.res-title a, h3.g-title a, .res-title a, .t a, h3 a")
            if not title_elem:
                continue
            title = title_elem.get_text(" ", strip=True)
            href = (title_elem.get("data-mdurl") or title_elem.get("href") or "").strip()
            snippet_elem = item.select_one(".res-desc, .c-abstract, p")
            snippet = snippet_elem.get_text(" ", strip=True) if snippet_elem else item.get_text(" ", strip=True)[:160]
            if href and title and href not in seen:
                seen.add(href)
                results.append({"title": title, "url": href, "snippet": snippet})
                if len(results) >= count:
                    return results

        if not results:
            return self._extract_links_generic(resp.text, count)
        return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="China-focused web search")
    parser.add_argument("query", help="search query")
    parser.add_argument("--engine", choices=["auto", "baidu", "bing", "360"], default="auto")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        searcher = WebSearchChina()
        results = searcher.search(args.query, engine=args.engine, count=args.count)
        payload = [asdict(r) for r in results]
        if args.pretty:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(payload, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
