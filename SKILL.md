---
name: web-search-china
description: China-focused search helper and research router with Tavily fusion support.
homepage: https://github.com/wopanda/web-search-china-openclaw
metadata: {"clawdbot":{"emoji":"🇨🇳","requires":{"bins":["python3"],"python":true}}}
---

# Web Search China

用于补充国内搜索结果的轻量研究/搜索技能。

现在包含两层：

1. `search.py`：国内多引擎搜索层（查询改写 + 并联召回 + 去重重排）
2. `search_router.py`：**Tavily + 国内搜索融合路由器**

## 当前推荐模式

### 国内搜索层
推荐：
```bash
python3 {baseDir}/scripts/search.py "搜索关键词" --engine auto --mode parallel --count 8 --pretty
```

### 路由层
推荐：
```bash
python3 {baseDir}/scripts/search_router.py "搜索关键词" --route auto --mode hybrid --count 8 --pretty
```

## 两种模式

### `hybrid`
- 多源一起召回
- 统一去重和重排
- 推荐作为默认模式

### `fallback`
- 先试一个源
- 不行再切另一个
- 兼容旧逻辑

## 适用理解

- 要 **国内中文结果补充**：优先 `search.py`
- 要 **中国环境下的研究路由**：优先 `search_router.py --mode hybrid`
- 要 **稳定全球搜索**：可接 Tavily，走 `global-first`

## 说明

- 这是 **best-effort** 工具，不保证每次都稳定
- 不是官方 API
- 当前版本已经从纯串联 fallback 升级到并联召回 + 融合重排
