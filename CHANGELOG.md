# Changelog

## 2026-03-25

### Added
- Initial hardened release of `web-search-china`
- Support for `bing`, `360`, and `baidu`
- Tavily router support
- README, SKILL.md, requirements, license

### Changed
- Switched Bing primary implementation to RSS for better stability
- Added `search_router.py`
- Upgraded from simple fallback to:
  - query expansion
  - parallel recall across Bing / 360 / Baidu
  - dedupe by canonical URL
  - score-based reranking
  - router `hybrid` fusion mode

### Known limitations
- This is not an official API integration
- Baidu may trigger verification pages
- 360 may include low-quality or promotional results
- Query rewriting and reranking are still rule-based
- Search engine markup and behavior can change at any time
