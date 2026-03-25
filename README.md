# Web Search China

Hardened China-focused web search skill for OpenClaw-style agents.

## What this is

A lightweight research/search layer for **China-oriented search results**.
It is useful when:

- you want more **Chinese-localized** results
- you want to supplement normal web search with **Bing / 360 / Baidu** coverage
- users explicitly ask for **国内搜索结果**
- you want a controllable fallback when Tavily or general web search is unstable

This repository now contains **two layers**:

1. **`search.py`** — China multi-engine search with query expansion, parallel recall, dedupe and rerank
2. **`search_router.py`** — unified router for **Tavily + China hybrid fusion**

## New architecture

### China search layer

The China layer no longer relies only on simple fallback order.
It now supports:

- **query expansion**
- **parallel recall** across Bing / 360 / Baidu
- **dedupe** by canonical URL
- **score-based reranking**
- optional sequential mode for debugging

### Router layer

The router now supports two modes:

- `hybrid` (recommended): merge results from multiple providers and rerank
- `fallback`: keep the old first-success behavior

## Installation

```bash
git clone https://github.com/wopanda/web-search-china-openclaw.git
cd web-search-china-openclaw
pip3 install -r requirements.txt
```

### Optional: Tavily support

If you want hybrid routing with Tavily, set:

```bash
export TAVILY_API_KEY=your_key_here
```

Without `TAVILY_API_KEY`, the router still works and will use the China layer only.

## Usage

### A. China search directly

Recommended:

```bash
python3 scripts/search.py "福建OPC联盟" --engine auto --mode parallel --count 8 --pretty
```

Debug old behavior:

```bash
python3 scripts/search.py "福建OPC联盟" --engine auto --mode sequential --count 8 --pretty
```

### B. Router mode

Recommended hybrid fusion:

```bash
python3 scripts/search_router.py "福建OPC联盟" --route auto --mode hybrid --count 8 --pretty
python3 scripts/search_router.py "latest ai agent framework" --route global-first --mode hybrid --count 6 --pretty
```

Old fallback behavior:

```bash
python3 scripts/search_router.py "你的问题" --route auto --mode fallback --count 5 --pretty
```

## How it works now

### China search (`search.py`)
For `--engine auto --mode parallel`:

1. expand the query into several variants
2. run Bing / 360 / Baidu in parallel
3. merge all candidates
4. dedupe by canonical URL
5. rerank using relevance + domain quality rules

### Router (`search_router.py`)
For `--mode hybrid`:

1. resolve route order (`auto` / `china-first` / `global-first`)
2. query both providers in the resolved plan
3. merge results
4. dedupe + rerank
5. return a single fused result list

## Recommended usage guidance

### If your server is in China
Recommended:

- Chinese / domestic queries → `--route auto --mode hybrid`
- official / org / local info lookup → `search.py --engine auto --mode parallel`
- global / English research → `--route global-first --mode hybrid`

## Difference vs Tavily

### This repository
- can work without API key
- better for Chinese-localized / domestic search supplementation
- highly controllable
- supports custom reranking rules
- useful as a local-first research orchestration layer

### Tavily
- requires API key
- cleaner structured output
- generally more stable for global/general research
- stronger as a ready-made search provider

### Practical rule

- **Need 国内结果 / 中文本地化补充** → use China search or router `hybrid`
- **Need stable global agent search** → use Tavily or router `global-first --mode hybrid`

## Files

- `scripts/search.py` — China parallel recall + rerank layer
- `scripts/search_router.py` — Tavily + China fusion router
- `requirements.txt` — Python dependencies
- `SKILL.md` — skill-facing usage description
- `CHANGELOG.md` — release notes
- `LICENSE` — MIT license

## Known limitations

- This tool is still **best-effort**, not a guaranteed API.
- Baidu may still trigger verification pages.
- 360 may still return low-quality or promotional pages.
- Query rewriting and reranking are rule-based, not ML-trained.
- Search engine behavior may change over time.
