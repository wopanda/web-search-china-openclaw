#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from dataclasses import asdict
from typing import Any, Dict, List, Sequence

import requests

from search import WebSearchChina

DEFAULT_TIMEOUT = 15
MAX_RESULTS = 10
TAVILY_ENDPOINT = "https://api.tavily.com/search"
CHINA_HINT_KEYWORDS = (
    "国内",
    "中国",
    "大陆",
    "知乎",
    "飞书",
    "微信",
    "微信公众号",
    "公众号",
    "小红书",
    "百度",
    "360",
    "B站",
    "哔哩哔哩",
    "政策",
    "备案",
    "中文社区",
    "方案",
    "教程",
    "部署",
    "自动化",
)


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def looks_china_oriented(query: str) -> bool:
    q = (query or "").strip()
    if not q:
        return False
    if any(k.lower() in q.lower() for k in CHINA_HINT_KEYWORDS):
        return True
    if has_chinese(q):
        return True
    return False


class TavilySearch:
    def __init__(self) -> None:
        self.api_key = (os.getenv("TAVILY_API_KEY") or "").strip()

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, count: int = 5) -> List[dict]:
        if not self.api_key:
            raise RuntimeError("missing TAVILY_API_KEY")

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "max_results": max(1, min(count, 20)),
            "include_answer": False,
            "include_raw_content": False,
        }
        resp = requests.post(
            TAVILY_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for idx, item in enumerate((data.get("results") or [])[:count], start=1):
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            snippet = str(item.get("content") or "").strip()
            if not title or not url:
                continue
            results.append(
                {
                    "rank": idx,
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "engine": "tavily",
                }
            )
        return results


class SearchRouter:
    def __init__(self) -> None:
        self.china = WebSearchChina()
        self.tavily = TavilySearch()

    def resolve_route(self, query: str, route: str) -> Sequence[str]:
        if route == "china-first":
            return ["china", "tavily"]
        if route == "global-first":
            return ["tavily", "china"]
        if looks_china_oriented(query):
            return ["china", "tavily"]
        return ["tavily", "china"]

    def search(self, query: str, count: int = 5, route: str = "auto") -> Dict[str, Any]:
        query = (query or "").strip()
        if not query:
            raise ValueError("query is required")

        count = max(1, min(int(count), MAX_RESULTS))
        plan = list(self.resolve_route(query, route))
        attempts: List[Dict[str, Any]] = []

        for provider in plan:
            try:
                if provider == "tavily":
                    results = self.tavily.search(query, count=count)
                else:
                    results = [asdict(r) for r in self.china.search(query, engine="auto", count=count)]

                if results:
                    attempts.append({"provider": provider, "ok": True, "result_count": len(results)})
                    return {
                        "query": query,
                        "route": route,
                        "resolved_route": plan,
                        "used_provider": provider,
                        "attempts": attempts,
                        "results": results,
                    }

                attempts.append({"provider": provider, "ok": False, "reason": "empty_results"})
            except Exception as exc:
                attempts.append({"provider": provider, "ok": False, "reason": str(exc)})

        return {
            "query": query,
            "route": route,
            "resolved_route": plan,
            "used_provider": None,
            "attempts": attempts,
            "results": [],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search router: Tavily + China search fallback")
    parser.add_argument("query", help="search query")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument(
        "--route",
        choices=["auto", "china-first", "global-first"],
        default="auto",
        help="routing policy",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        router = SearchRouter()
        payload = router.search(args.query, count=args.count, route=args.route)
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
