---
name: web-search-china
description: China-focused web search helper for Baidu, Bing China, and 360 Search. Best-effort parsing with Bing RSS as primary strategy.
homepage: https://github.com/wopanda/web-search-china-openclaw
metadata: {"clawdbot":{"emoji":"🇨🇳","requires":{"bins":["python3"],"python":true}}}
---

# Web Search China

用于补充国内搜索结果的轻量搜索技能。

## 当前策略

- **bing**：主引擎，优先走 RSS，稳定性最好
- **360**：HTML 抓取兜底
- **baidu**：可选兜底，但稳定性和结果质量较弱

默认 `auto` 顺序：

1. `bing`
2. `360`
3. `baidu`

## 适用场景

- 用户明确要找 **中国国内搜索结果**
- 用户要查 **百度/Bing 中国版/360** 更容易覆盖的信息
- 现有通用搜索结果不够本地化时

## 调用方式

```bash
python3 {baseDir}/scripts/search.py "搜索关键词"
python3 {baseDir}/scripts/search.py "搜索关键词" --engine bing --count 5
python3 {baseDir}/scripts/search.py "搜索关键词" --engine auto --count 8 --pretty
```

## 参数

- `query`：搜索词
- `--engine`：`auto` / `baidu` / `bing` / `360`，默认 `auto`
- `--count`：结果条数，默认 5，最大 10
- `--pretty`：格式化 JSON 输出

## 怎么理解它和 Tavily 的区别

### web-search-china
- 不需要 API key
- 适合补充 **国内搜索结果**
- 更偏本地化中文结果
- 稳定性一般，属于 best-effort

### Tavily
- 需要 API key
- 更适合 AI / agent 标准搜索工作流
- 结构更干净，整体更稳
- 更偏全网通用搜索，不是专为国内搜索设计

## 简单建议

- 要 **国内结果补充**：优先用 `web-search-china`
- 要 **稳定、通用、全网研究**：优先用 Tavily

## 说明

- 这是 **best-effort** 工具，不保证每次都稳定
- 不是官方 API
- `auto` 会按顺序尝试多个引擎，提高可用性
- 若搜索引擎页面结构变化，可能需要更新解析规则
