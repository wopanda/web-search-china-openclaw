# Web Search China

Hardened China-focused web search skill for OpenClaw-style agents.

## Current engine strategy

- **Bing**: primary, using **RSS** first for better stability
- **360 Search**: HTML parsing fallback
- **Baidu**: optional fallback, but less stable and often noisy

Default `auto` order:

1. `bing`
2. `360`
3. `baidu`

## What it does

- Searches **Baidu**, **Bing China**, and **360 Search**
- Supports `--engine auto` fallback mode
- Returns structured **JSON** results
- Uses safe defaults: timeout, retry, URL validation, result dedupe
- Reads only public search pages and writes nothing except stdout

## Install

```bash
pip3 install -r requirements.txt
```

Then use directly:

```bash
python3 scripts/search.py "2026年中国两会"
python3 scripts/search.py "AI agent" --engine bing --count 3
python3 scripts/search.py "OpenClaw" --engine auto --count 5 --pretty
```

## Output

Default output is JSON:

```json
[
  {
    "rank": 1,
    "title": "示例标题",
    "url": "https://example.com",
    "snippet": "示例摘要",
    "engine": "bing"
  }
]
```

## Notes

- This tool is **best-effort**, not a guaranteed API.
- Bing is currently the most stable source in this implementation.
- 360 works, but may include low-quality or promotional pages.
- Baidu may trigger verification or return ad-heavy results.
