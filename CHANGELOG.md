# Changelog

## 2026-03-25

### Added
- Initial hardened release of `web-search-china`
- Support for `bing`, `360`, and `baidu`
- `auto` mode with fallback ordering
- Safer URL validation and result dedupe
- README, SKILL.md, requirements, license

### Changed
- Switched **Bing** primary implementation to **RSS** for better stability
- Kept **360** as HTML fallback
- Kept **Baidu** as optional lower-priority fallback

### Known limitations
- This is not an official API integration
- Baidu may trigger verification pages
- 360 may include low-quality or promotional results
- Search engine markup and behavior can change at any time
