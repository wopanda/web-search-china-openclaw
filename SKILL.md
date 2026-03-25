---
name: web-search-china
description: China-focused web search helper and search router with Tavily fallback support.
homepage: https://github.com/wopanda/web-search-china-openclaw
metadata: {"clawdbot":{"emoji":"🇨🇳","requires":{"bins":["python3"],"python":true}}}
---

# Web Search China

用于补充国内搜索结果的轻量搜索技能。

现在包含两层：

1. `search.py`：国内搜索补充
2. `search_router.py`：**Tavily + 国内搜索 fallback 路由器**

## 当前策略

### 国内搜索层
- **bing**：主引擎，优先走 RSS，稳定性最好
- **360**：HTML 抓取兜底
- **baidu**：可选兜底，但稳定性和结果质量较弱

默认 `auto` 顺序：
1. `bing`
2. `360`
3. `baidu`

### 路由层
- `auto`：自动判断是先走 Tavily 还是先走国内搜索
- `china-first`：先走国内搜索
- `global-first`：先走 Tavily

## 推荐调用

### 最简单推荐
```bash
python3 {baseDir}/scripts/search_router.py "搜索关键词" --route auto --count 5 --pretty
```

### 只用国内搜索
```bash
python3 {baseDir}/scripts/search.py "搜索关键词" --engine auto --count 5 --pretty
```

### 强制先走 Tavily
```bash
python3 {baseDir}/scripts/search_router.py "搜索关键词" --route global-first --count 5 --pretty
```

## Tavily 和它的关系

- 要 **全网/稳定/标准 agent 搜索**：优先 Tavily
- 要 **国内中文结果补充**：优先国内搜索
- 在中国服务器上，Tavily 失效时，可自动切到国内搜索

## 说明

- 这是 **best-effort** 工具，不保证每次都稳定
- 不是官方 API
- 路由器可以减少 Tavily 在中国环境失效时的影响
