## 起動時の最初のアクション
**まず `.claude/agents/site-builder.md` をReadツールで読め。** 詳細な技術スタック・コーディング規約・品質チェックリストが書いてある。次に `docs/design-rules.md` を読め。読んでから作業を始めること。

---

# Site Builder ナレッジ

## Site Structure
- `site/index.html` - LP (landing page), created 2026-02-15
- Tailwind CSS v4 via CDN (`@tailwindcss/browser@4`)
- No JS file yet (not needed)
- No CSS file yet (theme defined inline per design-rules.md)

## Design Rules Key Points
- design-rules.md is the single source of truth
- Only allowed arbitrary value: `bg-[#0a0a0f]` for page background
- Breakpoints: only `md:` and `lg:`
- Transitions: only `transition-colors` and `transition-opacity`
- No shadows, transforms, animations
- Container: `max-w-5xl mx-auto px-6`
- Section spacing: `py-24`
- Card padding: `p-6`

## Patterns Used
- FAQ uses `<details>/<summary>` for accordion (no JS needed)
- Org chart uses flexbox + grid layout with connector lines (`w-px h-8 bg-edge`)
- Disabled buttons use `cursor-not-allowed` + `text-gray-500` + `border-edge`
