# Web Search China

面向中国场景强化过的 OpenClaw 风格 Web 搜索技能。

## 这是什么

这是一个轻量的**中文 / 国内搜索补充层**，适合在下面这些场景使用：

- 你想获得更偏**中文本地化**的搜索结果
- 你希望在常规 Web 搜索之外，补充 **Bing / 360 / 百度** 的覆盖
- 用户明确要求看 **国内搜索结果**
- Tavily 或通用搜索不稳定时，你需要一个更可控的补位方案

当前仓库包含两层能力：

1. **`search.py`**：国内多引擎搜索，支持查询扩展、并联召回、去重与重排
2. **`search_router.py`**：统一路由层，支持 **Tavily + 国内搜索混合融合**

## 新架构

### 国内搜索层

国内搜索层不再只是简单的顺序 fallback。
现在支持：

- **query expansion（查询扩展）**
- **parallel recall（Bing / 360 / 百度并联召回）**
- **dedupe（基于 canonical URL 去重）**
- **score-based reranking（按分数重排）**
- 可选串行模式，便于调试

### 路由层

路由层支持两种模式：

- `hybrid`（推荐）：多源合并后统一重排
- `fallback`：保留旧的“哪个先成功就用哪个”的行为

## 安装

```bash
git clone https://github.com/wopanda/web-search-china-openclaw.git
cd web-search-china-openclaw
pip3 install -r requirements.txt
```

### 可选：启用 Tavily

如果你想使用带 Tavily 的混合路由模式，请设置：

```bash
export TAVILY_API_KEY=your_key_here
```

如果没有设置 `TAVILY_API_KEY`，路由器仍然可以正常工作，只是只会使用国内搜索层。

## 用法

### A. 直接使用国内搜索

推荐：

```bash
python3 scripts/search.py "福建OPC联盟" --engine auto --mode parallel --count 8 --pretty
```

调试旧行为：

```bash
python3 scripts/search.py "福建OPC联盟" --engine auto --mode sequential --count 8 --pretty
```

### B. 路由模式

推荐的混合融合模式：

```bash
python3 scripts/search_router.py "福建OPC联盟" --route auto --mode hybrid --count 8 --pretty
python3 scripts/search_router.py "latest ai agent framework" --route global-first --mode hybrid --count 6 --pretty
```

旧的 fallback 行为：

```bash
python3 scripts/search_router.py "你的问题" --route auto --mode fallback --count 5 --pretty
```

## 现在它是怎么工作的

### 国内搜索（`search.py`）

对于 `--engine auto --mode parallel`：

1. 先把原始查询扩展成几个变体
2. 并行请求 Bing / 360 / 百度
3. 合并所有候选结果
4. 按 canonical URL 去重
5. 根据相关性和域名质量规则重排

### 路由器（`search_router.py`）

对于 `--mode hybrid`：

1. 先解析路由顺序（`auto` / `china-first` / `global-first`）
2. 按规划请求两个提供方
3. 合并结果
4. 去重并重排
5. 返回一份统一融合后的结果列表

## 推荐使用建议

### 如果你的服务器在中国

推荐这样用：

- 中文 / 国内查询 → `--route auto --mode hybrid`
- 官方站点 / 机构 / 本地信息查询 → `search.py --engine auto --mode parallel`
- 全球 / 英文研究 → `--route global-first --mode hybrid`

## 和 Tavily 的区别

### 这个仓库

- 不依赖 API Key 也能工作
- 更适合做中文本地化 / 国内搜索补充
- 可控性更强
- 支持自定义重排规则
- 适合作为本地优先的研究编排层

### Tavily

- 需要 API Key
- 输出结构更干净
- 更适合全球 / 通用研究场景
- 作为现成搜索提供方更省心

### 实用规则

- **需要国内结果 / 中文本地化补充** → 用国内搜索层，或用路由器 `hybrid`
- **需要稳定的全球 Agent 搜索** → 用 Tavily，或用路由器 `global-first --mode hybrid`

## 文件说明

- `scripts/search.py` —— 国内并联召回 + 重排层
- `scripts/search_router.py` —— Tavily + 国内搜索融合路由器
- `requirements.txt` —— Python 依赖
- `SKILL.md` —— 面向技能接入的说明
- `CHANGELOG.md` —— 发布说明
- `LICENSE` —— MIT 许可证

## 已知限制

- 这是一个 **best-effort** 工具，不是稳定 SLA 的官方 API
- 百度仍然可能触发验证页
- 360 仍然可能返回低质量或带推广性质的页面
- 查询改写和重排目前是规则驱动，不是训练出来的模型
- 搜索引擎的页面结构和行为可能随时间变化
