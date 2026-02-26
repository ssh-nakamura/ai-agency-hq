# デザインルール & コーディング規約

> site-builder エージェントのための唯一のルールブック。
> ここに書いてないことはやらない。迷ったらCEOに確認。

---

## 1. デザイン方針

**「神話と技術が交差する、知的で怪しい組織」の佇まい。**
ダークトーンを基調に、神話・宗教・民俗の「目」モチーフを纏う。
安っぽいサイバー感ではなく、秘密結社のような品と重みを出す。

---

## 2. セットアップ

全HTMLの `<head>` に以下を含める：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">

<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
<style type="text/tailwindcss">
  @theme {
    --color-base: #0f172a;
    --color-brand: #2563eb;
    --color-brand-dim: #1d4ed8;
    --color-brand-light: rgba(37, 99, 235, 0.15);
    --color-surface: #1e293b;
    --color-surface-alt: #111827;
    --color-edge: #334155;
    --color-success: #16a34a;
    --color-danger: #dc2626;
    --font-sans: "Noto Sans JP", sans-serif;
  }
</style>
```

※ 本番化時は CDN → Tailwind CLI に切り替える。

---

## 3. カラー

| 用途 | クラス | 補足 |
|------|--------|------|
| ページ背景 | `bg-base` | 濃紺 #0f172a |
| セクション背景（交互） | `bg-surface-alt` | やや明るい暗色 #111827 |
| カード背景 | `bg-surface` | #1e293b |
| ホバー背景 | `hover:bg-surface-alt` | カード・行のホバー |
| ボーダー | `border-edge` | #334155 |
| 本文テキスト | `text-gray-300` | メインのテキスト |
| 補助テキスト | `text-gray-400` | 日付、注釈など |
| 見出しテキスト | `text-white` | h1, h2, h3 |
| アクセント | `text-brand` / `bg-brand` | 要所だけ。多用禁止 |
| アクセント背景（薄） | `bg-brand-light` | バッジ背景（半透明青） |
| 成功 | `text-success` | ステータス表示 |
| エラー | `text-danger` | エラー表示 |

### カラールール
- `text-white` は見出し（h1, h2, h3）のみ
- `text-brand` はラベル、バッジ、リンク、CTAに限定
- 背景の交互: 濃紺(`bg-base`) → 暗色(`bg-surface-alt`) → 濃紺 → ...
- **任意値 `[#xxx]` は原則禁止。すべてトークンを使う**

---

## 4. タイポグラフィ

| 要素 | クラス |
|------|--------|
| Hero見出し (h1) | `text-4xl md:text-5xl font-bold tracking-tight text-white` |
| セクション見出し (h2) | `text-2xl font-bold text-white` |
| 小見出し (h3) | `text-lg font-semibold text-white` |
| 本文 | `text-base text-gray-300 leading-relaxed` |
| リード文 | `text-lg text-gray-400 leading-relaxed` |
| 補助テキスト | `text-sm text-gray-400` |

### タイポルール
- フォントは `Noto Sans JP` 1本。`font-sans` で適用
- フォントウェイトは 400(regular), 500(medium), 700(bold) の3種のみ
- `font-mono` は使わない
- `font-extrabold` は使わない。`font-bold` で統一

---

## 5. スペーシング

### 使っていい値（これ以外は使わない）

| 値 | Tailwindクラス | 用途 |
|----|---------------|------|
| 4px | `p-1` / `m-1` | バッジ内の微調整 |
| 8px | `p-2` / `m-2` / `gap-2` | アイコンとテキストの間 |
| 12px | `p-3` / `m-3` / `gap-3` | ラベルとコンテンツの間 |
| 16px | `p-4` / `m-4` / `gap-4` | カード内の要素間 |
| 24px | `p-6` / `m-6` / `gap-6` | カード内パディング、カード間 |
| 32px | `p-8` / `gap-8` | セクション内のブロック間 |
| 48px | `py-12` | 小セクションの上下 |
| 96px | `py-24` | メインセクションの上下 |

### スペーシングルール
- `p-5`, `p-7`, `p-9`, `p-10` 等の中途半端な値は使わない
- セクション間は必ず `py-24`
- カード内パディングは必ず `p-6`
- 要素間のgapは `gap-4` か `gap-6`

---

## 6. レイアウト

### コンテナ
```html
<div class="max-w-5xl mx-auto px-6">
  <!-- 全セクションのコンテンツはこの中 -->
</div>
```
- コンテナ幅は `max-w-5xl` で統一。他のmax-w値は使わない
- 左右パディングは `px-6` で統一

### Flex vs Grid
- **1次元（横並び）**: `flex` を使う
- **2次元（グリッド）**: `grid` を使う
- カード一覧: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- 2カラム: `grid grid-cols-1 md:grid-cols-2 gap-6`
- ナビ: `flex items-center justify-between`
- 縦積み: `flex flex-col gap-4`

### Z-index
| レイヤー | 値 |
|---------|-----|
| ナビゲーション | `z-50` |
| モーダル（将来用） | `z-40` |
| デフォルト | なし（指定しない） |

---

## 7. コンポーネント

### ナビゲーション
```html
<nav class="fixed top-0 inset-x-0 z-50 bg-base/90 backdrop-blur-md border-b border-edge">
  <div class="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
    <a href="/" class="text-lg font-bold text-white">仮想機関AI計画</a>
    <div class="hidden md:flex items-center gap-6">
      <a href="#section" class="text-sm text-gray-400 hover:text-brand transition-colors">リンク</a>
    </div>
  </div>
</nav>
```

### セクション
```html
<section id="name" class="py-24">
  <div class="max-w-5xl mx-auto px-6">
    <h2 class="text-2xl font-bold text-white mb-8">見出し</h2>
    <!-- content -->
  </div>
</section>
```

### カード
```html
<div class="bg-surface border border-edge rounded-lg p-6 hover:border-brand/50 transition-colors">
  <h3 class="text-lg font-semibold text-white mb-3">タイトル</h3>
  <p class="text-gray-300 leading-relaxed">内容</p>
</div>
```

### ボタン
```html
<!-- Primary -->
<a href="#" class="inline-block bg-brand hover:bg-brand-dim text-white font-medium rounded-lg px-6 py-3 transition-colors">
  ラベル
</a>

<!-- Secondary -->
<a href="#" class="inline-block border border-edge hover:bg-surface text-gray-300 font-medium rounded-lg px-6 py-3 transition-colors">
  ラベル
</a>

<!-- Disabled -->
<span class="inline-block bg-surface text-gray-500 font-medium rounded-lg px-6 py-3 cursor-not-allowed">
  ラベル（準備中）
</span>
```

### バッジ / タグ
```html
<span class="text-xs font-medium text-brand bg-brand-light px-2.5 py-0.5 rounded">
  ラベル
</span>
```

### リンク
```html
<!-- コンテンツ内リンク -->
<a href="#" class="text-brand hover:underline">テキスト</a>

<!-- ナビリンク -->
<a href="#" class="text-sm text-gray-400 hover:text-brand transition-colors">テキスト</a>
```

---

## 8. インタラクション

### 許可するtransition
- `transition-colors` — 背景色・テキスト色・ボーダー色の変化
- `transition-shadow` — カードのホバーシャドウ

これ以外のtransition（transform, scale, opacity等）は使わない。

### duration
- 指定しない（Tailwindデフォルトの150msを使う）

### ホバー
- カード: `hover:border-brand/50`
- ボタン(primary): `hover:bg-brand-dim`
- ナビリンク: `hover:text-brand`
- テキストリンク: `hover:underline`

### フォーカス
- インタラクティブ要素: `focus:outline-none focus:ring-2 focus:ring-brand/50`

---

## 9. レスポンシブ

- モバイルファースト（Tailwindデフォルト）
- 使うブレークポイント: `md:` (768px) と `lg:` (1024px) のみ
- `sm:` と `xl:` と `2xl:` は使わない

| パターン | 実装 |
|---------|------|
| ナビリンク | `hidden md:flex` |
| グリッド2列 | `grid-cols-1 md:grid-cols-2` |
| グリッド3列 | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` |
| Hero文字サイズ | `text-4xl md:text-5xl` |

---

## 10. 角丸・ボーダー・シャドウ

| 要素 | 角丸 |
|------|------|
| カード | `rounded-lg` |
| ボタン | `rounded-lg` |
| バッジ | `rounded` |
| 入力フォーム（将来用） | `rounded-lg` |

- `rounded-md`, `rounded-xl`, `rounded-2xl` 等は使わない
- ボーダーは `border border-edge` で統一
- シャドウは原則使わない（ダーク背景ではボーダーで区切る）

---

## 11. コーディング規約

### HTMLテンプレート
全ページはこの構造で始める：

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ページタイトル | 仮想機関AI計画</title>
  <meta name="description" content="ページの説明">

  <!-- OGP -->
  <meta property="og:title" content="ページタイトル | 仮想機関AI計画">
  <meta property="og:description" content="ページの説明">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://ai-unmanned.com/ページパス">

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">

  <!-- Tailwind CSS v4 -->
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <style type="text/tailwindcss">
    @theme {
      --color-base: #0f172a;
      --color-brand: #2563eb;
      --color-brand-dim: #1d4ed8;
      --color-brand-light: rgba(37, 99, 235, 0.15);
      --color-surface: #1e293b;
      --color-surface-alt: #111827;
      --color-edge: #334155;
      --color-success: #16a34a;
      --color-danger: #dc2626;
      --font-sans: "Noto Sans JP", sans-serif;
    }
  </style>
</head>
<body class="bg-base text-gray-300 font-sans antialiased">

  <!-- nav -->
  <!-- main content -->
  <!-- footer -->

</body>
</html>
```

### ファイル構成
```
site/
├── index.html              # トップ / LP
├── blog/
│   └── *.html              # ブログ記事（将来）
├── css/
│   └── theme.css           # @theme 定義（共通化する場合）
├── js/
│   └── main.js             # JS（必要になった場合のみ）
└── assets/
    ├── icons/              # キャラクターSVGアイコン
    │   ├── providence.svg  # CEO
    │   ├── nazar.svg       # 経営企画部長
    │   └── *.svg           # 各部門
    └── images/
        ├── og-image.png    # OGP画像
        └── *.webp          # サイト内画像（WebP推奨）
```

### ファイルルール
- ファイル名は **ケバブケース** (`about-us.html`, `og-image.png`)
- 画像は `assets/images/` に集約
- SVGアイコンは `assets/icons/` に集約
- 画像形式は **WebP推奨**、PNGはOGP画像のみ
- CSSファイルは `css/theme.css` 1つだけ。増やさない
- JSファイルは `js/main.js` 1つだけ。増やさない（必要になるまで作らない）

### 共通パーツ（ヘッダー・フッター）
ビルドツールがないため、共通パーツはコピーで管理する：
- ナビゲーションとフッターは全ページに同じHTMLをコピー
- 各ページの先頭にコメントで明示：`<!-- 共通ナビ: 変更時は全ページ更新 -->`
- ページ数が5を超えたらSSG導入を検討（CEOに提案）

### 画像
- 必ず `alt` 属性をつける
- `loading="lazy"` を付ける（ファーストビュー画像を除く）
- 幅指定: `width` と `height` 属性を必ず付ける（CLS防止）

---

## 12. 禁止事項

- `style` 属性でのインラインスタイル
- Tailwindクラス以外のカスタムCSS（@theme定義を除く）
- `!important`
- 任意値 `[#xxx]` の使用（すべてトークンを使う）
- キーフレームアニメーション（`@keyframes`, `animate-*`）
- 外部CDN追加（Tailwind・Google Fonts以外）
- `sm:`, `xl:`, `2xl:` ブレークポイント
- `p-5`, `p-7`, `p-9`, `p-10` 等の未許可値
- `rounded-md`, `rounded-xl`, `rounded-2xl` 等の未許可角丸
- `font-mono`
- `font-extrabold`
- `shadow-md` 以上のシャドウ
- `transform`, `scale`, `rotate` 等のトランスフォーム
