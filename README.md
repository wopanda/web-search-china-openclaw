# Web Search China

Hardened China-focused web search skill for OpenClaw-style agents.

## What this is

A lightweight search skill for **China-oriented search results**.
It is useful when:

- you want more **Chinese-localized** results
- you want to supplement normal web search with **Bing China / 360 / Baidu** coverage
- users explicitly ask for **国内搜索结果**

This repository is a **best-effort search helper**, not an official search API.

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

## Installation

### Option A: use as a standalone script

```bash
git clone https://github.com/wopanda/web-search-china-openclaw.git
cd web-search-china-openclaw
pip3 install -r requirements.txt
```

Then run:

```bash
python3 scripts/search.py "2026年中国两会"
python3 scripts/search.py "AI agent" --engine bing --count 3
python3 scripts/search.py "OpenClaw" --engine auto --count 5 --pretty
```

### Option B: use as an OpenClaw skill

If someone wants to use it inside an OpenClaw-style skills directory:

1. clone this repository
2. copy `web-search-china-openclaw/` into their skills folder, or keep it as its own skill directory
3. ensure `python3` is available
4. install dependencies from `requirements.txt`
5. call the script described in `SKILL.md`

Typical command pattern:

```bash
python3 {baseDir}/scripts/search.py "搜索关键词" --engine auto --count 5 --pretty
```

## How to use it

### Basic examples

```bash
# auto mode (recommended)
python3 scripts/search.py "AI agent 国内新闻" --engine auto --count 5 --pretty

# Bing only (currently the most stable)
python3 scripts/search.py "OpenClaw" --engine bing --count 5 --pretty

# 360 only
python3 scripts/search.py "OpenClaw" --engine 360 --count 5 --pretty

# Baidu only (less stable, lower quality)
python3 scripts/search.py "OpenClaw" --engine baidu --count 5 --pretty
```

### Output format

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

## Recommended usage guidance

### When to use this skill

Use **web-search-china** when:
- the user explicitly wants **国内搜索结果**
- you need better Chinese-localized coverage
- normal web search misses local/community/forum content

### When to use Tavily / normal web search instead

Use **Tavily** or standard web search when:
- you want cleaner general web results
- you need stronger English/global coverage
- you need AI-oriented relevance ranking
- you need more stable API-style behavior

## Difference vs Tavily

### This repository
- no API key needed
- uses public search surfaces
- China-localized coverage
- lower stability
- lower structure quality
- best for supplementary search

### Tavily
- requires API key
- official API product
- cleaner structured output
- generally more stable
- better for agent workflows and broad web research
- not specifically optimized for Chinese domestic engines

### Simple rule of thumb

- **Need 国内结果 / 中文本地化补充** → use `web-search-china`
- **Need stable agent search / global research** → use Tavily

## For people you share this repo with

If you give someone this GitHub link:

**https://github.com/wopanda/web-search-china-openclaw**

They can do this directly:

```bash
git clone https://github.com/wopanda/web-search-china-openclaw.git
cd web-search-china-openclaw
pip3 install -r requirements.txt
python3 scripts/search.py "你要搜索的问题" --engine auto --count 5 --pretty
```

That is the shortest working path.

## Known limitations

- This tool is **best-effort**, not a guaranteed API.
- Bing is currently the most stable source in this implementation.
- 360 works, but may include low-quality or promotional pages.
- Baidu may trigger verification or return ad-heavy results.
- Search engine HTML / behavior can change at any time.

## Files

- `scripts/search.py` — main search script
- `requirements.txt` — Python dependencies
- `SKILL.md` — skill-facing usage description
- `CHANGELOG.md` — release notes
- `LICENSE` — MIT license
