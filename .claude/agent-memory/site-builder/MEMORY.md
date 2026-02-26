## 起動時の最初のアクション
**まず `.claude/agents/site-builder.md` をReadツールで読め。** 詳細な技術スタック・コーディング規約・品質チェックリストが書いてある。次に `docs/design-rules.md` を読め。読んでから作業を始めること。

---

# Site Builder ナレッジ

## Site Structure
- `site/index.html` - LP (landing page), created 2026-02-15
- Tailwind CSS v4 via CDN (`@tailwindcss/browser@4`)
- No JS file yet (not needed)
- No CSS file yet (theme defined inline per design-rules.md)

## Design Rules Key Points (updated 2026-02-26: DARK theme)
- design-rules.md is the single source of truth
- Dark theme: bg-base (#0f172a) body, text-gray-300 body, blue accent (#2563eb)
- Font: Noto Sans JP via Google Fonts. font-mono is BANNED
- NO arbitrary values [#xxx] — use tokens only
- Breakpoints: only `md:` and `lg:`
- Transitions: `transition-colors` and `transition-shadow` only
- Shadows: NOT used on dark theme. Border used instead: `hover:border-brand/50`
- Container: `max-w-5xl mx-auto px-6`
- Section spacing: `py-24`; alternate bg-base / bg-surface-alt
- Card: `bg-surface border border-edge rounded-lg p-6 hover:border-brand/50 transition-colors`
- Headings (h1/h2/h3): `text-white` only
- Body text: `text-gray-300 leading-relaxed`
- Lead text: `text-lg text-gray-400 leading-relaxed`
- Supplementary text: `text-sm text-gray-400`
- Badges: `text-xs font-medium text-brand bg-brand-light px-2.5 py-0.5 rounded`
- Section labels (`// Foo`) are BANNED — use h2 only
- font-extrabold is BANNED — use font-bold
- Disabled button: `bg-surface text-gray-500 font-medium rounded-lg px-6 py-3 cursor-not-allowed`
- Nav: `bg-base/90 backdrop-blur-md border-b border-edge`, h-16, hover:text-brand
- Secondary button: `border border-edge hover:bg-surface text-gray-300 font-medium rounded-lg px-6 py-3 transition-colors`

## デプロイフロー（2026-02-26〜）

ホスティング: Cloudflare Pages（Direct Upload方式）
ドメイン: ai-unmanned.com

### サイト修正後の手順
1. **CEOからの指示を受けて site/ 内を修正**
2. **プレビューデプロイ（develop）**
   ```
   cd site && npx wrangler pages deploy . --project-name=ai-unmanned --branch=develop --commit-dirty=true --commit-message="preview: 変更内容"
   ```
   → https://develop.ai-unmanned.pages.dev で株主が確認
3. **株主OK → 本番デプロイ（main）**
   ```
   cd site && npx wrangler pages deploy . --project-name=ai-unmanned --branch=main --commit-dirty=true --commit-message="deploy: 変更内容"
   ```
   → https://ai-unmanned.com に反映

### 注意
- commit-messageは英語（日本語だとWranglerがUTF-8エラーを出す）
- `--commit-dirty=true` は必須（git未コミットでもデプロイ可能にする）
- デプロイはCEOの指示で実行。勝手にデプロイしない
- site/ ディレクトリの中身だけがアップロードされる（docs/等は含まれない）

---

## Patterns Used
- FAQ uses `<details>/<summary>` for accordion (no JS needed)
- summary hover: `hover:bg-surface-alt` (not surface-hover — that token is gone)
- Org chart uses flexbox + grid layout with connector lines (`w-px h-8 bg-edge`)
- text-white is for all headings AND primary button (bg-brand background)
- Character icons: `<img src="assets/icons/{name}.svg" width="40" height="40" alt="{キャラ名}" loading="lazy">`
- CEO card uses `border-2 border-brand` to stand out (only exception to border-edge rule)
- Org list items: `flex items-start gap-4`, icon has `shrink-0 mt-1` to align with text top
