# デザインルール & コーディング規約

> site-builder エージェントのための唯一のルールブック。
> ここに書いてないことはやらない。迷ったらCEOに確認。

---

## 1. セットアップ

全HTMLの `<head>` に以下を含める：

```html
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
<style type="text/tailwindcss">
  @theme {
    --color-brand: #6c5ce7;
    --color-brand-dim: #5a4bd1;
    --color-brand-glow: rgba(108, 92, 231, 0.15);
    --color-surface: #12121a;
    --color-surface-hover: #1a1a26;
    --color-edge: #1e1e2e;
    --color-success: #00b894;
    --color-danger: #ff6b6b;
    --font-mono: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
  }
</style>
```

※ 本番化時は CDN → Tailwind CLI に切り替える。

---

## 2. カラー

| 用途 | クラス | 補足 |
|------|--------|------|
| ページ背景 | `bg-[#0a0a0f]` | 最深層。これだけ任意値OK |
| カード背景 | `bg-surface` | 浮き要素 |
| ホバー背景 | `hover:bg-surface-hover` | カード・行のホバー |
| ボーダー | `border-edge` | 全ボーダーはこれ |
| 本文テキスト | `text-gray-200` | メインのテキスト |
| 補助テキスト | `text-gray-500` | 日付、注釈など |
| 見出しテキスト | `text-white` | h1, h2のみ |
| アクセント | `text-brand` / `bg-brand` | 要所だけ。多用禁止 |
| 成功 | `text-success` | ステータス表示 |
| エラー | `text-danger` | エラー表示 |

### カラールール
- `text-white` は見出し（h1, h2）とナビロゴのみ。本文には使わない
- `text-brand` はラベル、バッジ、ホバー、リンクに限定
- 背景の階層: ページ → カード(`surface`) → ホバー(`surface-hover`)
- **任意値 `[#xxx]` はページ背景 `bg-[#0a0a0f]` のみ許可。他は全てトークンを使う**

---

## 3. タイポグラフィ

| 要素 | クラス |
|------|--------|
| Hero見出し (h1) | `text-4xl md:text-6xl font-extrabold tracking-tight text-white` |
| セクション見出し (h2) | `text-2xl font-bold text-white` |
| 小見出し (h3) | `text-lg font-semibold text-white` |
| 本文 | `text-base text-gray-200 leading-relaxed` |
| リード文 | `text-lg text-gray-500 leading-loose` |
| セクションラベル | `font-mono text-xs text-brand uppercase tracking-widest` |
| バッジ・タグ | `font-mono text-xs` |
| コード・ターミナル | `font-mono text-sm` |

### タイポルール
- フォントファミリーは2つだけ: デフォルト(sans) と `font-mono`
- フォントサイズは上記テーブルの組み合わせのみ使用
- `text-xl` は使わない（h2の`text-2xl` か h3の`text-lg` を使う）

---

## 4. スペーシング

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

## 5. レイアウト

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
| ドロップダウン（将来用） | `z-30` |
| デフォルト | なし（指定しない） |

---

## 6. コンポーネント

### ナビゲーション
```html
<nav class="fixed top-0 inset-x-0 z-50 bg-[#0a0a0f]/85 backdrop-blur-md border-b border-edge">
  <div class="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
    <a href="/" class="font-mono text-sm font-bold text-white">ロゴ</a>
    <div class="hidden md:flex items-center gap-6">
      <a href="#section" class="text-sm text-gray-400 hover:text-white transition-colors">リンク</a>
    </div>
  </div>
</nav>
```

### セクション
```html
<section id="name" class="py-24">
  <div class="max-w-5xl mx-auto px-6">
    <p class="font-mono text-xs text-brand uppercase tracking-widest mb-3">// Label</p>
    <h2 class="text-2xl font-bold text-white mb-6">見出し</h2>
    <!-- content -->
  </div>
</section>
```

### カード
```html
<div class="bg-surface border border-edge rounded-lg p-6 hover:bg-surface-hover transition-colors">
  <h3 class="text-lg font-semibold text-white mb-3">タイトル</h3>
  <p class="text-gray-200 leading-relaxed">内容</p>
</div>
```

### ボタン
```html
<!-- Primary -->
<a href="#" class="inline-block bg-brand hover:bg-brand-dim text-white font-semibold rounded-lg px-6 py-3 transition-colors">
  ラベル
</a>

<!-- Secondary -->
<a href="#" class="inline-block border border-edge hover:bg-surface text-gray-200 font-semibold rounded-lg px-6 py-3 transition-colors">
  ラベル
</a>

<!-- Ghost（ナビ内など小さいボタン） -->
<a href="#" class="text-sm text-brand hover:bg-brand-glow rounded-lg px-4 py-2 transition-colors">
  ラベル
</a>
```

### バッジ / タグ
```html
<span class="font-mono text-xs text-brand bg-brand-glow border border-brand/25 px-2.5 py-0.5 rounded">
  ラベル
</span>
```

### ターミナル風表示
```html
<div class="inline-block font-mono text-sm text-gray-500 bg-surface border border-edge px-6 py-3 rounded-lg">
  <span class="text-success">$</span> コマンド
</div>
```

### リンク
```html
<!-- コンテンツ内リンク -->
<a href="#" class="text-brand hover:underline">テキスト</a>

<!-- ナビリンク -->
<a href="#" class="text-sm text-gray-400 hover:text-white transition-colors">テキスト</a>
```

---

## 7. インタラクション

### 許可するtransition
- `transition-colors` — 背景色・テキスト色の変化
- `transition-opacity` — 表示/非表示の変化

これ以外のtransition（transform, scale, shadow等）は使わない。

### duration
- 指定しない（Tailwindデフォルトの150msを使う）

### ホバー
- カード: `hover:bg-surface-hover`
- ボタン(primary): `hover:bg-brand-dim`
- ナビリンク: `hover:text-white`
- テキストリンク: `hover:underline`

### フォーカス
- インタラクティブ要素: `focus:outline-none focus:ring-2 focus:ring-brand/50`

---

## 8. レスポンシブ

- モバイルファースト（Tailwindデフォルト）
- 使うブレークポイント: `md:` (768px) と `lg:` (1024px) のみ
- `sm:` と `xl:` と `2xl:` は使わない

| パターン | 実装 |
|---------|------|
| ナビリンク | `hidden md:flex` |
| グリッド2列 | `grid-cols-1 md:grid-cols-2` |
| グリッド3列 | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` |
| Hero文字サイズ | `text-4xl md:text-6xl` |

---

## 9. 角丸・ボーダー

| 要素 | 角丸 |
|------|------|
| カード | `rounded-lg` |
| ボタン | `rounded-lg` |
| バッジ | `rounded` |
| 入力フォーム（将来用） | `rounded-lg` |
| アバター（将来用） | `rounded-full` |

- `rounded-md`, `rounded-xl`, `rounded-2xl` 等は使わない
- ボーダーは `border border-edge` で統一

---

## 10. コーディング規約

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

  <!-- Tailwind CSS v4 -->
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <style type="text/tailwindcss">
    @theme {
      --color-brand: #6c5ce7;
      --color-brand-dim: #5a4bd1;
      --color-brand-glow: rgba(108, 92, 231, 0.15);
      --color-surface: #12121a;
      --color-surface-hover: #1a1a26;
      --color-edge: #1e1e2e;
      --color-success: #00b894;
      --color-danger: #ff6b6b;
      --font-mono: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
    }
  </style>
</head>
<body class="bg-[#0a0a0f] text-gray-200 font-sans antialiased">

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
    └── images/             # 画像
        ├── og-image.png    # OGP画像
        └── *.webp          # サイト内画像（WebP推奨）
```

### ファイルルール
- ファイル名は **ケバブケース** (`about-us.html`, `og-image.png`)
- 画像は `assets/images/` に集約
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

## 11. 禁止事項

- `style` 属性でのインラインスタイル
- Tailwindクラス以外のカスタムCSS（@theme定義を除く）
- `!important`
- 任意値 `[#xxx]` の多用（ページ背景のみ許可）
- キーフレームアニメーション（`@keyframes`, `animate-*`）
- 外部CDN追加（Tailwind以外）
- `sm:`, `xl:`, `2xl:` ブレークポイント
- `text-xl`, `p-5`, `p-7`, `p-9`, `p-10` 等の未許可値
- `rounded-md`, `rounded-xl`, `rounded-2xl` 等の未許可角丸
- `shadow-*`（影は使わない。暗い背景では不要）
- `transform`, `scale`, `rotate` 等のトランスフォーム
