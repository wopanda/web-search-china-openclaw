#!/usr/bin/env python3
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
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

LOW_QUALITY_HOST_KEYWORDS = (
    "mydown.com",
    "gamesteamplay.cn",
    "cr173.com",
    "down",
    "download",
    "soft",
)

HIGH_QUALITY_HOST_KEYWORDS = (
    ".gov.cn",
    ".org.cn",
    ".edu.cn",
    "github.com",
    "openclaw.ai",
)

OFFICIAL_INTENT_KEYWORDS = (
    "官网",
    "官方",
    "协会",
    "联盟",
    "研究院",
    "公司",
    "学院",
    "大学",
    "实验室",
)


@dataclass
class SearchResult:
    rank: int
    title: str
    url: str
    snippet: str
    engine: str
    score: float = 0.0


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

    def expand_queries(self, query: str) -> List[str]:
        q = (query or "").strip()
        if not q:
            return []
        variants = [q]
        if re.search(r"[A-Za-z]{2,}", q) and re.search(r"[\u4e00-\u9fff]", q):
            spaced = re.sub(r"([A-Za-z]+)", r" \1 ", q)
            spaced = re.sub(r"\s+", " ", spaced).strip()
            if spaced != q:
                variants.append(spaced)
        if any(k in q for k in OFFICIAL_INTENT_KEYWORDS) is False and len(q) <= 16:
            variants.append(f"{q} 官网")
        deduped: List[str] = []
        seen = set()
        for item in variants:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped[:3]

    def search_engine(self, query: str, engine: str, count: int = 5) -> List[SearchResult]:
        if engine not in self.engines:
            raise ValueError(f"unsupported engine: {engine}")
        raw_results = self.engines[engine](query, count)
        out: List[SearchResult] = []
        for item in raw_results:
            normalized = self._normalize_result(item, engine, query)
            if normalized:
                out.append(normalized)
        return out

    def search(self, query: str, engine: str = "auto", count: int = 5, mode: str = "parallel") -> List[SearchResult]:
        query = (query or "").strip()
        if not query:
            raise ValueError("query is required")

        count = max(1, min(int(count), MAX_RESULTS))
        if engine != "auto":
            items = self.search_engine(query, engine, count)
            return self._rerank(self._dedupe_and_sort(items, count))

        variants = self.expand_queries(query)
        plans: List[tuple[str, str]] = [(eng, qv) for qv in variants for eng in ["bing", "360", "baidu"]]
        collected: List[SearchResult] = []

        if mode == "parallel":
            with ThreadPoolExecutor(max_workers=min(6, len(plans) or 1)) as pool:
                futures = {pool.submit(self._safe_search_engine, qv, eng, count): (eng, qv) for eng, qv in plans}
                for future in as_completed(futures):
                    collected.extend(future.result())
        else:
            for eng, qv in plans:
                collected.extend(self._safe_search_engine(qv, eng, count))

        return self._rerank(self._dedupe_and_sort(collected, count))

    def _safe_search_engine(self, query: str, engine: str, count: int) -> List[SearchResult]:
        try:
            return self.search_engine(query, engine, count)
        except Exception:
            return []

    def _dedupe_and_sort(self, items: List[SearchResult], count: int) -> List[SearchResult]:
        by_url: Dict[str, SearchResult] = {}
        for item in items:
            key = self._canonicalize_url(item.url)
            prev = by_url.get(key)
            if prev is None or item.score > prev.score:
                by_url[key] = item
        ranked = sorted(by_url.values(), key=lambda x: x.score, reverse=True)
        return ranked[:count]

    def _canonicalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        return base.lower()

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

    def _normalize_result(self, item: dict, engine: str, query: str) -> Optional[SearchResult]:
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

        score = self._score_result(query, title, url, snippet, engine)
        return SearchResult(rank=0, title=title, url=url, snippet=snippet, engine=engine, score=score)

    def _score_result(self, query: str, title: str, url: str, snippet: str, engine: str) -> float:
        q = (query or "").lower()
        title_l = title.lower()
        snippet_l = snippet.lower()
        host = (urlparse(url).netloc or "").lower()
        score = 0.0

        if q in title_l:
            score += 8.0
        if q in snippet_l:
            score += 4.0

        query_tokens = [t for t in re.split(r"\s+", re.sub(r"([A-Za-z]+)", r" \1 ", query)) if t]
        for token in query_tokens:
            tok = token.lower()
            if len(tok) <= 1:
                continue
            if tok in title_l:
                score += 2.5
            if tok in snippet_l:
                score += 1.0
            if tok in host:
                score += 1.5

        if any(k in host for k in HIGH_QUALITY_HOST_KEYWORDS):
            score += 3.0
        if host.endswith(".gov.cn") or host.endswith(".org.cn") or host.endswith(".edu.cn"):
            score += 3.5
        if any(k in host for k in LOW_QUALITY_HOST_KEYWORDS):
            score -= 6.0
        if any(k in title for k in ("下载", "正式版", "极速下载")):
            score -= 5.0
        if any(k in query for k in OFFICIAL_INTENT_KEYWORDS) and ("官网" in title or host.endswith(".org.cn") or host.endswith(".gov.cn")):
            score += 4.0

        engine_bias = {"bing": 1.5, "360": 0.5, "baidu": 0.0}
        score += engine_bias.get(engine, 0.0)
        return score

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
                    break

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
                    break

        if not results:
            return self._extract_links_generic(resp.text, count)
        return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="China-focused web search")
    parser.add_argument("query", help="search query")
    parser.add_argument("--engine", choices=["auto", "baidu", "bing", "360"], default="auto")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--mode", choices=["parallel", "sequential"], default="parallel")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        searcher = WebSearchChina()
        results = searcher.search(args.query, engine=args.engine, count=args.count, mode=args.mode)
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
