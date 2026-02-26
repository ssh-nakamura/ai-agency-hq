# ホームページ自動生成システム — 仕様書

> 対象リポジトリ: site-generator（別リポジトリ）
> 承認: 2026-02-26 株主承認済み

---

## 概要

事業者（行政書士、薬局、士業、クリニック等）向けのホームページを、ヒアリングシート回答から自動生成するシステム。

### ゴール
- ヒアリングシート回答 → 本番品質のHTML一式を自動出力
- 1サイト30分以内で完成
- ブログ記事もコマンド1つで追加可能

---

## プロジェクト構造

```
site-generator/
├── templates/             # 業種別テンプレート定義（JSON）
│   ├── gyoseishoshi.json  # 行政書士
│   ├── pharmacy.json      # 薬局
│   └── generic.json       # 汎用（士業・クリニック等）
├── generate.py            # メイン生成スクリプト
├── blog_gen.py            # ブログ記事生成スクリプト
├── hearing_sheet.html     # クライアント配布用ヒアリングシート
├── output/                # 生成物出力先
│   └── {client_name}/
│       ├── index.html
│       ├── blog/
│       │   ├── index.html
│       │   └── posts/
│       └── sitemap.xml
└── README.md
```

---

## 1. テンプレート定義（JSON）

各業種のデザイントーン・構成を定義する。generate.py はこのJSONを読んでサイトを生成する。

### テンプレートJSON構造

```json
{
  "industry": "行政書士",
  "design": {
    "tone": "権威・信頼・実績",
    "font_jp": "Noto Sans JP",
    "font_display": "DM Serif Display",
    "colors": {
      "primary": "#1b4f8a",
      "primary_deep": "#0f2847",
      "accent": "#c9a84c",
      "bg": "#ffffff",
      "bg_alt": "#f4f8fd",
      "text": "#1a2332",
      "text_sub": "#4a5568"
    },
    "border_radius": "rounded-2xl",
    "cta_shape": "rounded-lg",
    "hero_style": "dark_fullwidth"
  },
  "sections": [
    "hero",
    "features",
    "services",
    "pricing",
    "flow",
    "cta_banner",
    "access",
    "contact",
    "footer"
  ],
  "seo": {
    "schema_type": "LegalService",
    "keywords_pattern": "{地域} {業種} {サービス名}"
  }
}
```

### 薬局テンプレート例

```json
{
  "industry": "薬局",
  "design": {
    "tone": "清潔・温かみ・安心",
    "font_jp": "Zen Maru Gothic",
    "font_display": "Outfit",
    "colors": {
      "primary": "#738a57",
      "primary_deep": "#475637",
      "accent": "#93a578",
      "bg": "#faf9f5",
      "bg_alt": "#f6f7f4",
      "text": "#333d29",
      "text_sub": "#5b6e44"
    },
    "border_radius": "rounded-3xl",
    "cta_shape": "rounded-full",
    "hero_style": "light_organic"
  },
  "sections": [
    "hero",
    "about",
    "services",
    "message",
    "faq",
    "access",
    "contact",
    "footer"
  ],
  "seo": {
    "schema_type": "Pharmacy",
    "keywords_pattern": "{地域} {業種} {サービス名}"
  }
}
```

### デザイントーンの差別化ルール

テンプレートを新規作成する際、以下の4軸すべてで既存テンプレートと異なるようにする：

1. **フォント** — 丸ゴシック / ゴシック / 明朝 を混ぜる
2. **配色** — 色相を90度以上離す（青系の次は緑系、次はベージュ系など）
3. **形状** — 角丸の大きさ、CTAのピル型 vs 角丸、カード vs リスト
4. **ヒーロー構造** — ダーク全幅 / ライト左寄せ / 中央揃え+イラスト背景

---

## 2. メイン生成スクリプト（generate.py）

### 入力
ヒアリングシート回答をYAMLまたはJSONで受け取る。

```yaml
# hearing.yaml（サンプル — 値はすべてダミー）
基本情報:
  事業所名: サンプル行政書士事務所
  代表者名: 山田太郎
  業種: 行政書士
  住所: 東京都千代田区丸の内1-1-1
  電話番号: 03-0000-0000
  メール: info@example.com
  営業時間: 平日 10:00〜19:00
  定休日: 土日祝
  駐車場: なし

サイトの目的:
  - 存在を知ってもらう
  - 信頼感を伝えたい
  - 問い合わせを増やしたい

必要な機能:
  - 問い合わせフォーム
  - Googleマップ
  - 料金表
  - ブログ

サイトの印象: 信頼・実績
好みの色: 青系

載せたい内容:
  強み: スピード対応
  サービス: 建設業許可、外国人ビザ申請
  メッセージ: ""  # 空の場合はAIが生成

素材:
  images/hero.jpg: ヒーロー背景
  images/representative.jpg: 代表者写真
  # 画像がない場合は省略 → CSS装飾で代替
```

### 処理フロー

```
1. hearing.yaml 読み込み
2. 業種からテンプレートJSON選択（なければ generic.json）
3. Tailwind CSS ベースでHTML生成
4. 以下を自動生成・埋め込み:
   a. 全セクション HTML
   b. JSON-LD 構造化データ
   c. OGP meta tags
   d. sitemap.xml
   e. robots.txt
5. output/{事業所名}/ に出力
```

### 実装要件

#### 技術スタック
- **CSS**: Tailwind CSS CDN（`https://cdn.tailwindcss.com`）のみ使用
- **カスタムCSS**: 最小限（アニメーション定義のみ許可）
- **JS**: バニラJSのみ。フレームワーク不要
- **フォント**: Google Fonts CDN
- **画像**: クライアント提供画像を優先配置。未提供時はCSS + 絵文字 + SVGで代替
- **フォーム**: Formspree（`https://formspree.io/f/{id}`）
- **地図**: Google Maps Embed API（iframe）

#### 著作権リスク最小化ルール（重要）
- デザインはすべて Tailwind CSS のユーティリティクラスで構成する
- カスタムCSSプロパティは色・フォント定義とアニメーションのみ
- 外部テンプレートやテーマのコードを参照・コピーしない
- ストックフォト等の外部画像素材を使用しない（クライアント提供画像 or CSS装飾のみ）
- これにより、デザインの出所がMITライセンスのTailwindに帰属できる

#### レスポンシブ対応
- モバイルファースト
- ブレークポイント: `md:` (768px) のみ使用
- ハンバーガーメニュー: JS最小限（classList.toggle）
- タップターゲット: 44px以上

#### SEO要件
- `<title>`: `{事業所名} | {地域}の{業種} - {キャッチフレーズ}`
- `<meta description>`: 120文字以内
- OGP: og:title, og:description, og:type, og:url
- JSON-LD 構造化データ（後述）
- semantic HTML: header, nav, main, section, article, footer
- 見出し階層: h1は1つのみ、h2→h3の順序を守る

#### JSON-LD 構造化データ

業種に応じて自動生成する。

行政書士の場合:
```json
{
  "@context": "https://schema.org",
  "@type": "LegalService",
  "name": "{事業所名}",
  "description": "{meta description}",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "{住所}",
    "addressLocality": "{市区町村}",
    "addressRegion": "{都道府県}",
    "addressCountry": "JP"
  },
  "telephone": "{電話番号}",
  "email": "{メール}",
  "openingHours": "{営業時間をISO形式に変換}",
  "url": "{サイトURL}"
}
```

薬局の場合:
```json
{
  "@context": "https://schema.org",
  "@type": "Pharmacy",
  "name": "{事業所名}",
  "medicalSpecialty": "Pharmacy",
  "description": "{meta description}",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "{住所}",
    "addressLocality": "{市区町村}",
    "addressRegion": "{都道府県}",
    "addressCountry": "JP"
  },
  "telephone": "{電話番号}",
  "email": "{メール}",
  "openingHours": "{営業時間をISO形式に変換}",
  "url": "{サイトURL}"
}
```

#### 業種別の広告規制チェックリスト（生成時に準拠すること）

**行政書士:**
- 事実に合致しない広告禁止
- 「絶対許可が取れます」等の断定表現NG
- 他事務所との比較広告禁止（「地域最安値」NG）
- 誤認を招く表現禁止

**薬局（薬機法）:**
- 医薬品の効能効果の保証表現禁止
- 虚偽・誇大広告禁止
- 安全性の保証表現禁止

**共通ルール:**
- 実績数字（「○○件」「○○%」）は仮値を入れ、コメントで `<!-- 要確認: 実数を入れてください -->` を付与
- 料金は仮値を入れ、同様にコメント付与

---

## 3. ブログ記事生成（blog_gen.py）

### 使い方

```bash
python3 blog_gen.py \
  --title "記事タイトル" \
  --body "本文（\n\nで段落区切り、## で見出し）" \
  --desc "meta description" \
  --date "2026-03-01"  # 省略時は今日
```

### 処理
1. `blog/posts/YYYYMMDD-{slug}.html` を生成
2. `blog/index.html` の記事一覧を自動更新（新しい順）
3. 記事末尾にCTA（無料相談導線）を自動挿入

### 記事テンプレート要件
- ナビにトップページとコラム一覧へのリンク
- パンくず: トップ > コラム > 記事タイトル
- 記事末尾に「この記事に関するご相談 → 無料相談はこちら」CTA
- 本文スタイル: 行間2.0、段落間1.5rem、見出しに下線
- サイト本体と同じTailwind config・配色を共有

### ブログ一覧ページ
- 記事タイトル + 日付 + description の一覧
- 新しい順に表示
- クリックで個別記事に遷移

---

## 4. ヒアリングシート（hearing_sheet.html）

クライアント配布用。スマホ最適化。

### 要件
- モバイルで5分で回答できるUI
- チップ型タップ選択（チェックボックスではなく div onclick）
- セクション: 基本情報 / サイトの目的 / 必要な機能 / サイトの印象 / 載せたい内容 / お手持ちの素材 / その他
- 「おまかせ」選択肢を各所に配置
- 最下部に「回答をコピー」ボタン → 全回答をテキスト整形してクリップボードにコピー
- コピーしたテキストをLINEやメールで送ってもらう運用

### 「回答をコピー」出力フォーマット
```
【ホームページ制作 ヒアリングシート回答】

■ 基本情報
事業所名：○○
代表者名：○○
...

■ サイトの目的
○○、○○

■ 必要な機能
○○、○○
...
```

---

## 5. デプロイ手順

### デモ確認（Netlify Drop）
1. output/{client_name}/ フォルダをまるごと https://app.netlify.com/drop にドラッグ
2. 30秒でURL発行 → クライアントにLINEで送付

### 本番公開（Cloudflare Pages）
1. GitHubリポジトリに push
2. Cloudflare Pages でリポジトリ連携
3. カスタムドメイン設定
4. SSL自動適用

### ドメイン取得・DNS設定の自動化（将来対応）

Cloudflare Registrar API を利用した半自動化フロー:

```
1. ドメイン空き確認     → 自動（API）
2. ドメイン購入         → 株主承認ボタン（決済が絡むため手動承認）
3. DNS設定             → 自動（API）
4. Cloudflare Pages連携 → 自動（API）
5. SSL証明書発行       → 自動（Cloudflare標準）
```

※ 初期はダッシュボード手動運用。案件数が増えたらAPI自動化に移行する

### 画像の配置

クライアントから画像を受け取った場合の配置ルール:

| 画像種別 | 配置先 | ファイル名規約 |
|---------|--------|---------------|
| ヒーロー背景 | heroセクション背景 | `hero.jpg` |
| 代表者写真 | aboutセクション / メッセージ | `representative.jpg` |
| 店舗外観 | accessセクション | `exterior.jpg` |
| スタッフ集合写真 | aboutセクション | `staff.jpg` |
| ロゴ | ヘッダー / フッター | `logo.png` |
| その他 | 適切なセクションに自動配置 | `photo-{n}.jpg` |

- 画像は `output/{client_name}/images/` に格納
- 画像がない場合は CSS装飾 + 絵文字 + SVGアイコンで代替（劣化しないデザイン）
- 画像最適化: WebP変換 + lazy loading を自動適用

---

## 6. 納品チェックリスト

生成後に以下を確認:

- [ ] モバイル表示崩れなし（Chrome DevTools で確認）
- [ ] 全リンク動作確認（ナビ、CTA、電話番号タップ）
- [ ] 電話番号の `tel:` リンクが正しい
- [ ] Googleマップが正しい位置を表示
- [ ] フォーム送信先（Formspree）が設定済み
- [ ] JSON-LD が Google Rich Results Test で valid
- [ ] Lighthouse スコア 90+ (Performance, SEO)
- [ ] 実績数字・料金がクライアント確認済み
- [ ] 広告規制に抵触する表現がない
- [ ] OGPが正しく設定されている
- [ ] sitemap.xml が存在する
- [ ] `<!-- 要確認 -->` コメントがすべて解消されている

---

## 7. 料金体系

AI自動生成による価格破壊モデル。従来の制作会社（¥300,000〜500,000）の1/15以下。

| 項目 | 金額 |
|------|------|
| サイト制作費 | ¥20,000 |
| Googleビジネスプロフィール設定 | ¥10,000（オプション） |
| 構造化データ・SEO基本設定 | 制作費に込み |
| 月次保守（更新対応） | ¥3,000/月 |
| 月次保守＋ブログ2本 | ¥5,000/月 |
| ドメイン・ホスティング実費 | ¥1,500/年（クライアント負担） |

---

## 8. 実装優先順位

1. **generate.py** — ヒアリングYAMLからHTML一式を生成
2. **テンプレートJSON 2種** — 行政書士 + 薬局
3. **blog_gen.py** — ブログ記事生成・一覧更新
4. **hearing_sheet.html** — クライアント配布用
5. **generic.json** — 汎用テンプレート（士業・クリニック）
