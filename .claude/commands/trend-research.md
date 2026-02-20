# Trend Research — リアルタイムトレンド調査（Team運用）

> 「今何がバズっているか」「どこに空白があるか」をリアルタイムデータで調査する。
> CEO + Analyst + Writer の3者がTeamで議論してGo/NoGo判断まで出す。

## 起動

```
/trend-research                    # スキャンモード（今何が熱いか全体を見る）
/trend-research AI副業             # 深掘りモード（テーマ指定）
/trend-research AI副業 note        # 深掘り + 媒体指定
```

---

## Step 0: MCP接続チェック（最初に必ず実行）

**このスキルはMCPが動かないと意味がない。WebSearchで代替するな。**

```
1. Grok MCP確認: x_get_trending を1回呼ぶ
   → 成功 → Layer 1 OK
   → 失敗 → 即エスカレーション（L2: 株主にMCP復旧を依頼）。調査中止。

2. Xpoz MCP確認: Instagram で適当なキーワードを1回検索
   → 成功 → Layer 2 OK
   → 失敗 → 株主に報告「Xpoz MCP未接続。Layer 2（Instagram/TikTok/Reddit）スキップ」
   → Xpozだけ死んでいる場合はLayer 1 + Layer 3で続行可。ただし株主に報告必須。

※ Grok MCPが死んでいる場合は調査を実行しない。WebSearchで代替は禁止。
```

---

## Step 1: Team構成（CEOが以下を順番に実行）

### 1-1. TeamCreate

```
TeamCreate:
  team_name: "trend-research"
  description: "トレンド調査 [日付] [モード: スキャン or テーマ名]"
```

### 1-2. タスク作成

```
TaskCreate: "CEO: Layer 1-3 データ収集"
  description: "Grok MCP + Xpoz MCP + WebSearchでトレンド生データを収集。共有フォーマットで整理してチームに送る"

TaskCreate: "Analyst: 市場評価"
  description: "CEOの生データを受け取り、Trend Arbitrage 3条件 + 収益性試算 + 競合密度を評価"

TaskCreate: "Writer: コンテンツ実現性評価"
  description: "CEOの生データを受け取り、媒体適合 + コンテンツ設計 + AI制作可能性を評価"

TaskCreate: "3者合議: Go/NoGo判定"
  description: "CEO・Analyst・Writerの評価を突き合わせて最終判定。成果物をdocs/research/に保存"
  blockedBy: [上の3タスク]
```

### 1-3. チームメンバーspawn

```
Task(analyst):
  name: "trend-analyst"
  team_name: "trend-research"
  model: opus
  prompt: "あなたはtrend-researchチームのAnalyst担当。TaskListを確認し、自分のタスクを取れ。CEOからトレンド生データが届くまで待機。届いたら市場評価フェーズの手順に従って評価せよ。"

Task(writer):
  name: "trend-writer"
  team_name: "trend-research"
  model: opus
  prompt: "あなたはtrend-researchチームのWriter担当。TaskListを確認し、自分のタスクを取れ。CEOからトレンド生データが届くまで待機。届いたらコンテンツ実現性評価フェーズの手順に従って評価せよ。"
```

### 1-4. CEOがデータ収集を開始（Step 2へ）

---

## Step 2: CEO — データ収集フェーズ

### Layer 1: Grok MCP — Xリアルタイムバズ（メイン）

MCPツール3種を使い分ける:

**`x_get_trending`** → 今Xで何がトレンドか一覧取得
```
→ トレンド一覧を取得。ここから「おっ」と思うものをピックアップ
```

**`x_search_posts`** → キーワード指定でX投稿検索
```
→ テーマ指定時: そのテーマのリアルタイム投稿・エンゲージメントを取得
→ スキャン時: トレンド一覧から気になるものを深掘り
```

**`x_get_user_posts`** → 特定ユーザーの投稿取得
```
→ 業界インフルエンサーが何を話しているか確認
```

### Layer 2: Xpoz MCP — Instagram/TikTok/Reddit（補完）

Grokが拾えないプラットフォームをカバーする。

```
対応PF: Instagram, TikTok, Reddit（Twitter/Xも可だがGrokがメイン）
Free枠: 100K件/月（課金情報登録不要）
制限: トレンド調査のみに使用。社内情報を含む検索は禁止
```

**検索パターン:**

| プラットフォーム | 検索内容 | 確認ポイント |
|---------------|---------|------------|
| **Instagram** | `{トピック}` でリール・投稿検索 | エンゲージメント率、ファセルス運用の有無、日本語コンテンツ密度 |
| **TikTok** | `{トピック}` で動画検索 | 再生数、日本語 vs 英語の投稿比率、バズパターン |
| **Reddit** | `r/japanlife`, `r/entrepreneur` 等で検索 | 英語圏の議論内容、日本未上陸のトピック発見 |

**Xpoz → Grok比較（同トピックの温度差）:**
```
X/Twitterでバズ + Instagram/TikTokで弱い → テキスト向きニッチ（ブログ/note）
X/Twitterで弱い + TikTok/Instagramでバズ → ビジュアル向きニッチ（YouTube/短尺動画）
全PFでバズ → レッドオーシャン（避ける or 差別化必須）
全PFで弱い → まだ早い or ニッチすぎ（タイムマシン候補として保留）
```

### Layer 3: WebSearch — MCP非対応データの補完

**MCPのフォールバックではない。MCP非対応の媒体・指標を取るためのもの。**

| 検索対象 | クエリ例 | 目的 |
|---------|---------|------|
| Google Trends | `{トピック} Google Trends 2026` | 検索ボリューム推移の確認 |
| YouTube | `{トピック} site:youtube.com` | 再生数・チャンネル数確認 |
| note | `{トピック} site:note.com` | 有料記事の有無・スキ数確認 |
| Substack/Beehiiv | `{トピック} site:substack.com` | 英語圏ニュースレターの存在確認 |

### Layer 4: タイムマシン検出（英語→日本語ギャップ）【毎回必須】

**毎回必ず実行。** 海外にあって日本にないものを見つける。

```
1. 英語でGrok + Xpoz検索: "{topic in English}"
2. 日本語でGrok + Xpoz検索: "{同トピック日本語}"
3. 比較:
   - 英語あり・日本語あり → 参入遅い（★）
   - 英語あり・日本語弱い → チャンス（★★）
   - 英語あり・日本語なし → 最高のチャンス（★★★）
   - 英語なし → トレンドではない（除外）
```

---

## Step 3: CEO → チームにデータ共有（SendMessage）

以下のフォーマットでAnalystとWriterに送る:

```markdown
## トレンド生データ [日付]

### Xバズ（Grok MCP取得）
| # | トピック | 投稿例 | エンゲージメント | 熱量 |
|---|---------|--------|----------------|------|

### クロスプラットフォーム状況（Xpoz MCP）
| # | トピック | Instagram | TikTok | Reddit | YouTube | note | 媒体温度差 |
|---|---------|-----------|--------|--------|---------|------|-----------|

### タイムマシン候補（英語あり→日本語弱/なし）
| # | 英語トピック | 海外状況 | 日本語状況 | 推定ラグ | チャンス度 |
|---|------------|---------|-----------|---------|-----------|
```

```
SendMessage:
  type: "message"
  recipient: "trend-analyst"
  content: [上のデータ + "市場評価フェーズの手順に従って評価せよ"]

SendMessage:
  type: "message"
  recipient: "trend-writer"
  content: [上のデータ + "コンテンツ実現性評価フェーズの手順に従って評価せよ"]
```

---

## Step 4: Analyst — 市場評価フェーズ

CEOから生データを受け取ったら、以下を評価:

### Trend Arbitrage 3条件判定

各候補に対して:

| 条件 | 判定方法 | ○/× |
|------|---------|------|
| **Breakout（急上昇）** | 検索ボリューム推移、X投稿数の増加率 | |
| **Information Gap（供給不足）** | 検索結果の質・鮮度、競合アカウント数 | |
| **High Intent（収益性）** | アフィリ単価、購買意欲、広告RPM | |

### 収益性の試算

```
- 推定月間検索ボリューム: X
- 推定CTR（1位想定）: Y%
- 推定コンバージョン率: Z%
- 推定単価（アフィリ or 有料記事）: ¥W
- 推定月収: X × Y% × Z% × ¥W = ¥???
```

### 競合密度

```
- 日本語の直接競合: N件（具体名）
- 英語圏の先行者: N件（具体名）
- 参入障壁: 高/中/低
```

**評価完了 → SendMessageでCEOに報告 → TaskUpdate で自タスクをcompleted**

---

## Step 5: Writer — コンテンツ実現性評価フェーズ

CEOから生データを受け取ったら、以下を評価:

### 媒体適合判定

| 候補トピック | note | ブログ | YouTube | TikTok | Instagram | X | 最適媒体 |
|------------|------|--------|---------|--------|-----------|---|---------|
| | ○/×/△ | ○/×/△ | ○/×/△ | ○/×/△ | ○/×/△ | ○/×/△ | |

### コンテンツ設計

最適媒体が決まったら:

```
- フォーマット: ハウツー? リスト? ストーリー? レビュー?
- トーン: 辛口の先輩? 実験者の独白? データの翻訳者? 熱量のある初心者?
- 文字数/尺:
- 更新頻度:
- Type A/B判定: 仮想機関AI計画ブランドで出す(A) or 匿名独立ブランド(B)
```

### AIで制作可能か

```
- AI単独で書ける度: 高/中/低
- 一次データが必要か: はい/いいえ（必要なら何が必要か）
- ペルソナの維持難度: 高/中/低
- anti-slopチェック通過見込み: 高/中/低
```

**評価完了 → SendMessageでCEOに報告 → TaskUpdate で自タスクをcompleted**

---

## Step 6: 3者合議 — Go/NoGo判定

AnalystとWriterの報告が揃ったら、CEOが合議タスクを開始:

```markdown
## Go/NoGo判定表

| 候補 | CEO判断 | Analyst評価 | Writer評価 | 総合 |
|------|--------|------------|-----------|------|
| | トレンド熱量 | 収益性 × 競合密度 | 制作可能性 × 媒体適合 | Go/NoGo |

### Go判定の条件（全部満たす）
- Trend Arbitrage 3条件のうち2つ以上○
- 推定月収 ¥30,000以上
- AIで制作可能（一次データ不要 or 取得可能）
- anti-slopチェック通過見込み: 中以上

### NoGoの場合
- 理由を記録して次の候補へ
- 3候補連続NoGoなら調査範囲を変える
```

---

## Step 7: 完了処理

```
1. 成果物を保存: docs/research/trend-{テーマslug}-{YYYY-MM-DD}.md
2. Go判定の候補 → docs/business/type-b-registry.md に追加
3. チームメンバーにshutdown_request送信
4. TeamDelete で team を解散
5. 株主に結果を報告
```

---

## MCP設定情報

### Grok MCP（x_search）— 設定済み
```
サーバー名: x_search
ツール: x_search_posts, x_get_user_posts, x_get_trending
コスト: xAI API（$25無料クレジット。超過後は従量課金 $2.50-5/1Kコール）
```

### Xpoz MCP（xpoz-mcp）— 要セットアップ
```
設定コマンド:
claude mcp add --transport http --scope user xpoz-mcp https://mcp.xpoz.ai/mcp --header "Authorization: Bearer <Xpoz APIトークン>"

取得先: https://www.xpoz.ai/ でアカウント作成 → APIトークン取得
コスト: Free枠 100K件/月（課金情報登録不要）
対応PF: Twitter/X, Instagram, TikTok, Reddit
無効化: claude mcp remove xpoz-mcp
```

### エスカレーション基準

| 状況 | 対応 | レベル |
|------|------|--------|
| Grok MCP応答なし | **調査中止。** 株主にMCP復旧を依頼 | L2 |
| Xpoz MCP応答なし | 株主に報告。Layer 1 + Layer 3で続行 | L1 |
| 両方応答なし | **調査中止。** 株主に全MCP復旧を依頼 | L2 |
| xAI無料クレジット枯渇 | 株主に従量課金の承認を依頼 | L4 |

---

## `/trend-scout` との棲み分け

| | `/trend-scout` | `/trend-research` |
|---|---------------|-------------------|
| レベル | GTM戦略（市場参入判断） | コンテンツ制作（何を作るか） |
| 問い | 「どの市場に参入すべきか」 | 「今何がバズっていて、どこが空白か」 |
| 運用 | writer単独 | **CEO + Analyst + Writer のTeam** |
| データ | WebSearch（二次情報） | **Grok MCP + Xpoz MCP（一次データ）** |
| 頻度 | 月1回 | 週1〜随時 |
| 判断 | CLPR分析 + GTMスコアリング | **Trend Arbitrage 3条件 + 3者合議** |
| タイムマシン | オプション | **毎回必須** |

---

## 定期実行

| 頻度 | モード | 目的 |
|------|--------|------|
| **週1回** | スキャン | 新トレンドの発見、タイムマシン候補の更新 |
| **随時** | 深掘り | Go判定が出た候補のコンテンツ設計 |
| **月1回** | 全媒体横断 | 媒体別のトレンド変化を定点観測 |
