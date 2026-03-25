# Web Search China

Hardened China-focused web search skill for OpenClaw-style agents.

## What this is

A lightweight search skill for **China-oriented search results**.
It is useful when:

- you want more **Chinese-localized** results
- you want to supplement normal web search with **Bing China / 360 / Baidu** coverage
- users explicitly ask for **国内搜索结果**

This repository now contains **two layers**:

1. **`search.py`** — China web search helper
2. **`search_router.py`** — unified router for **Tavily + China search fallback**

## Router behavior

The router lets you do this:

- try **Tavily** first when global/general search is preferred
- automatically fall back to **web-search-china** when Tavily fails or returns nothing
- prefer **China search first** when the query looks Chinese / domestic-oriented

### Route policies

- `auto` — smart route selection based on the query
- `china-first` — always try China search first
- `global-first` — always try Tavily first

## Current engine strategy

Inside China search:

- **Bing**: primary, using **RSS** first for better stability
- **360 Search**: HTML parsing fallback
- **Baidu**: optional fallback, but less stable and often noisy

Default China search `auto` order:

1. `bing`
2. `360`
3. `baidu`

## Installation

```bash
git clone https://github.com/wopanda/web-search-china-openclaw.git
cd web-search-china-openclaw
pip3 install -r requirements.txt
```

### Optional: Tavily support

If you want router-level global search + fallback, set:

```bash
export TAVILY_API_KEY=your_key_here
```

Without `TAVILY_API_KEY`, the router can still work, but it will naturally fall back to China search.

## Usage

### A. Use China search directly

```bash
python3 scripts/search.py "OpenClaw" --engine auto --count 5 --pretty
python3 scripts/search.py "飞书 自动化" --engine bing --count 5 --pretty
```

### B. Use the router

```bash
python3 scripts/search_router.py "OpenClaw 是什么" --route auto --count 5 --pretty
python3 scripts/search_router.py "latest ai agent framework" --route global-first --count 5 --pretty
python3 scripts/search_router.py "飞书 自动化 国内方案" --route china-first --count 5 --pretty
```

## What the router returns

Router output includes:

- `used_provider` — which provider actually served the result
- `attempts` — which providers were tried and whether they failed
- `results` — final search results

Example:

```json
{
  "used_provider": "china",
  "attempts": [
    {"provider": "tavily", "ok": false, "reason": "timeout"},
    {"provider": "china", "ok": true, "result_count": 5}
  ],
  "results": []
}
```

## Recommended usage guidance

### If your server is in China
Recommended logic:

- Chinese / domestic queries → `--route auto` or `--route china-first`
- Global / English research → `--route global-first`
- If Tavily is unstable, the router will degrade to China search

### If you just want the shortest working path

```bash
python3 scripts/search_router.py "你的问题" --route auto --count 5 --pretty
```

## Difference vs Tavily

### This repository
- can work without API key
- better for Chinese-localized / domestic search supplementation
- lower stability than a real API
- useful as fallback or local-first supplement

### Tavily
- requires API key
- cleaner structured output
- more stable for agent workflows
- better for global/general research

### Practical rule

- **Need 国内结果 / 中文本地化补充** → use China search or router `auto`
- **Need stable global agent search** → use Tavily or router `global-first`

## For people you share this repo with

Send them this repo:

**https://github.com/wopanda/web-search-china-openclaw**

Then they can do:

```bash
git clone https://github.com/wopanda/web-search-china-openclaw.git
cd web-search-china-openclaw
pip3 install -r requirements.txt
python3 scripts/search_router.py "要搜索的问题" --route auto --count 5 --pretty
```

## Files

- `scripts/search.py` — China search engine helper
- `scripts/search_router.py` — Tavily + China fallback router
- `requirements.txt` — Python dependencies
- `SKILL.md` — skill-facing usage description
- `CHANGELOG.md` — release notes
- `LICENSE` — MIT license

## Known limitations

- This tool is **best-effort**, not a guaranteed API.
- Bing is currently the most stable source in China search mode.
- 360 may include low-quality or promotional pages.
- Baidu may trigger verification or return ad-heavy results.
- Search engine behavior may change over time.
