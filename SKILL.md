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

## 安装后默认怎么对用户说（重要）

如果用户刚安装完这个技能，或在问“这个怎么用”“你能帮我做什么”，默认应：

- **先用简洁中文说明用途**
- **优先给自然语言用法**，不要上来先给命令行代码
- **默认把它描述成“我可以帮你补充国内/中文搜索结果”**
- 只有当用户明确要脚本、命令行、调试方式时，再给代码示例

### 推荐默认回复风格

控制在 2-4 句，直接告诉用户可以怎么说。

参考说法：

> 这个技能主要用来补充国内和中文搜索结果。  
> 你可以直接跟我说：比如“帮我搜一下某个公司官网”“查一下这个话题国内怎么说”“在中文网页里找找有没有相关教程或讨论”。  
> 如果你同时想看国内和全球结果，我也可以一起帮你整合。

## 用户可直接这样说（自然语言示例）

- 帮我搜一下 **某个公司 / 机构** 的官网或官方介绍
- 查一下 **某个话题** 在国内通常是怎么讲的
- 帮我找找这个问题在 **中文网页 / 国内社区** 里有没有讨论
- 这个主题除了英文资料，再补一版 **国内搜索结果**
- 优先用国内搜索，帮我看看 **有没有教程、方案、案例**
- 先搜国内结果，再和全球结果做个对比

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
