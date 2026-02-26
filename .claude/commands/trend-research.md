# Trend Research — リアルタイムトレンド調査（Team運用）

> 「検索需要」と「ソーシャルバズ」を掛け合わせ、収益化できる空白地帯を見つける。
> CEO + Analyst + Writer の3者がTeamで議論してGo/NoGo判断まで出す。

## 起動

```
/trend-research                    # スキャンモード（今何が熱いか全体を見る）
/trend-research AI副業             # 深掘りモード（テーマ指定）
/trend-research AI副業 note        # 深掘り + 媒体指定
```

## 中核コンセプト: バズ×需要マトリクス

ソーシャルメディアとGoogle Trendsは**別の質問に答える**。両方見て初めて判断できる。

| | バズ高（MCP） | バズ低（MCP） |
|---|---|---|
| **需要高（Google Trends）** | 検証済みトレンド。レッドオーシャンリスク | **静かな需要 = 最高のチャンス**（誰も作ってないのに検索されてる） |
| **需要低（Google Trends）** | ノイズ・一過性。収益化困難 | トレンドではない |

狙うのは **「需要高 × バズ低〜中」** のゾーン。

---

## Step 0: ツール接続チェック（最初に必ず実行）

**MCPが動かないと意味がない。WebSearchで代替するな。**

```
1. Grok MCP確認: ToolSearch "+x_search" → x_get_trending を1回呼ぶ
   → 成功 → バズ分析可能
   → 失敗 → 即エスカレーション（L2: 株主にMCP復旧を依頼）。調査中止。

2. Xpoz MCP確認: ToolSearch "+xpoz-mcp" → Instagram で適当なキーワード検索
   → 成功 → クロスPF分析可能
   → 失敗 → 株主に報告（L1）。Grok単独で続行可。

3. Google Trends API確認: ステータス未定（alpha申請中）
   → 申請URL: https://developers.google.com/search/apis/trends#apply
   → 取得済みなら: python3 tools/core/google_trends.py status で確認
   → 未取得なら: WebSearchで "{トピック} Google Trends 推移" を代替手段として使用

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
TaskCreate: "CEO: 需要ベースライン（Google Trends）"
  description: "JP/US/その他のGoogle Trendsデータを取得。検索需要のベースラインを確立"

TaskCreate: "CEO: バズ分析（Grok + Xpoz MCP）"
  description: "Grok MCP + Xpoz MCPでソーシャルバズデータを収集"
  blockedBy: [needs Google Trends baseline first]

TaskCreate: "CEO: バズ×需要クロス分析 + タイムマシン検出"
  description: "Google Trends × MCPデータを2x2マトリクスで分類。JP vs US比較でタイムマシン候補を特定。共有フォーマットで整理してチームに送る"

TaskCreate: "Analyst: 市場評価"
  description: "CEOの生データ（バズ×需要マトリクス付き）を受け取り、Trend Arbitrage 3条件 + 収益性試算 + 競合密度を評価"

TaskCreate: "Writer: コンテンツ実現性評価"
  description: "CEOの生データを受け取り、媒体適合 + コンテンツ設計 + AI制作可能性を評価"

TaskCreate: "3者合議: Go/NoGo判定"
  description: "CEO・Analyst・Writerの評価を突き合わせて最終判定。成果物をdocs/research/に保存"
  blockedBy: [Analyst, Writer完了後]
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

**順番が重要。需要→バズ→比較→補完→裏取りの順で回す。**

### スキャンモード vs 深掘りモードの分岐【最初に判断】

```
スキャンモード（/trend-research 引数なし）:
  → 候補を事前に決めるな。データから発見する。
  → Phase Aの前に Grok MCP x_get_trending でXトレンドを取得
  → WebSearchで「2026 副業 トレンド」「2026 niche business ideas」等を広く検索
  → AI系に偏るな。美容・健康・金融・教育・趣味・ライフスタイル等を横断的に見る
  → トレンドデータから候補3〜5個をピックアップしてからPhase Aに進む

深掘りモード（/trend-research {テーマ}）:
  → 指定テーマでPhase Aに直接進む
  → ただしPhase E・Fの裏取りは省略するな
```

**過去の失敗（2026-02-26）: AI系3候補を事前に決め打ちしてスキャンを飛ばした結果、バイアスまみれの調査になった。Type Bは「ニッチ独立ブランド」であり、自分たちの得意分野だけ見るのは禁止。**

### Phase A: 検索需要の把握（Google Trends）【最初に実行】

**Google Trends API alpha 申請中。取得後にキーワード指定のInterest Over Time + Related Queriesが使える。**

#### API取得後:
```bash
python3 tools/core/google_trends.py query "{トピック}" --geo JP
```

#### API未取得時（現在）:
```
1. WebSearch で "{トピック} Google Trends 推移 2026" を検索
2. 検索結果から需要推移の傾向を把握
```
→ API取得まではこれが限界。精度は低い。

### Phase B: バズ分析（Grok MCP）

**`x_get_trending`** → Xトレンド一覧。Phase Aの結果と見比べる。
```
→ Google Trendsにもある = 検証済み需要
→ Google Trendsにない = ソーシャル限定のノイズ or 超初期トレンド
```

**`x_search_posts`** → キーワードでX投稿検索
```
→ テーマ指定時: エンゲージメント + 投稿者属性を確認
→ スキャン時: Phase Aの需要トピックのバズ状況を確認
```

**`x_get_user_posts`** → 業界インフルエンサーの発信内容を確認

### Phase C: クロスPF分析（Xpoz MCP）

Grokが拾えないプラットフォームをカバー。

| プラットフォーム | 検索内容 | 確認ポイント |
|---------------|---------|------------|
| **Instagram** | `{トピック}` でリール・投稿検索 | エンゲージメント率、日本語コンテンツ密度 |
| **TikTok** | `{トピック}` で動画検索 | 再生数、日本語 vs 英語比率 |
| **Reddit** | `r/japanlife`, `r/entrepreneur` 等 | 英語圏の議論、日本未上陸トピック |

**媒体間の温度差判定:**
```
X + Insta/TikTok 両方バズ → レッドオーシャン（差別化必須）
Xだけバズ → テキスト向きニッチ（ブログ/note）
Insta/TikTokだけバズ → ビジュアル向き（YouTube/短尺動画）
全PFで弱い → まだ早い or ニッチすぎ（保留）
```

### Phase D: タイムマシン検出【毎回必須】

**MCP比較（英語 vs 日本語）を中心にする。Google Trends APIが使えるようになったら追加。**

```
1. Grok MCP: 同トピックを英語/日本語で検索
   → 英語圏のX投稿量 vs 日本語のX投稿量

2. Xpoz MCP: 同トピックをInstagram/Redditで検索
   → 英語圏のビジュアルコンテンツ量 vs 日本語

3. 総合判定:
   MCP英語有/日本語無 → ★★★（最高のチャンス）
   MCP英語有/日本語弱 → ★★
   MCP英語有/日本語有 → ★（遅い）
   MCP英語なし        → トレンドではない（除外）
```

### Phase E: プラットフォーム市場調査（WebSearch）【必須】

**MCPのフォールバックではない。MCPが対応しない媒体の実態を把握する。特にnoteは必ず検索しろ。**

| 検索対象 | クエリ例 | 目的 |
|---------|---------|------|
| **note（必須）** | `{トピック} note 有料 メンバーシップ 人気 読者数` | 既存プレイヤー・有料記事・購読者規模の把握 |
| **note（必須）** | `{トピック} 日本語 note 週刊 2026` | 定期配信の競合確認 |
| YouTube | `{トピック} site:youtube.com` | 再生数・チャンネル数 |
| Substack | `{トピック} site:substack.com` | 英語圏ニュースレター |
| Amazon Kindle | `{トピック} site:amazon.co.jp Kindle` | 電子書籍の競合状況 |

**Phase Eで既存プレイヤーが見つかったら、Phase Dのタイムマシン判定を上書き修正しろ。**

### Phase F: Grok API裏取り検証【必須・最終チェック】

**Phase A〜EのMCPデータ・WebSearchデータだけでは市場の全体像を見誤る（2026-02-26 AIニュースレター誤判定の教訓）。Grok APIで直接裏取りする。**

```bash
curl -s -X POST "https://api.x.ai/v1/chat/completions" \
  -H "Authorization: Bearer $(cat ~/.claude/mcp-servers/x-search-mcp/.env | grep XAI_API_KEY | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-3",
    "messages": [{"role": "user", "content": "{トピック}の日本語市場について教えて。note、Substack、メルマガ等で定期配信している日本語の{トピック}を全て列挙。購読者数、更新頻度、有料/無料、特徴を含めて。"}],
    "search_mode": "on"
  }'
```

**Grok APIの回答で既存プレイヤーが判明したら:**
- Phase Dのタイムマシン判定を修正
- マトリクスの★を下方修正
- 「Information Gap不成立」と明記

**Grok APIが使えない場合（キー切れ等）→ L2エスカレーション。裏取りなしで先に進むな。**

---

## Step 3: CEO → チームにデータ共有（SendMessage）

以下のフォーマットでAnalystとWriterに送る:

```markdown
## トレンド生データ [日付]

### A. 検索需要ベースライン（Google Trends）
| # | トピック | トラフィック | JP/US | ニュースソース |
|---|---------|------------|-------|-------------|

### B. ソーシャルバズ（Grok + Xpoz MCP）
| # | トピック | X熱量 | Instagram | TikTok | Reddit | 媒体温度差 |
|---|---------|-------|-----------|--------|--------|-----------|

### C. バズ×需要マトリクス分類
| # | トピック | 検索需要 | バズ | 分類 | 判断 |
|---|---------|---------|------|------|------|
| 1 | xxx | 高 | 低 | 静かな需要 | ★★★ 最優先調査 |
| 2 | yyy | 高 | 高 | 検証済み | ★★ レッドオーシャン注意 |
| 3 | zzz | 低 | 高 | ノイズ | ★ 見送り |

### D. タイムマシン候補（Google Trends JP/US差 + MCP英日差）
| # | トピック（英語） | Google US | Google JP | MCP英語 | MCP日本語 | チャンス度 |
|---|----------------|----------|----------|--------|----------|-----------|
```

```
SendMessage:
  type: "message"
  recipient: "trend-analyst"
  content: [上のデータ + "バズ×需要マトリクスのC・Dセクションを重点的に評価せよ。市場評価フェーズの手順に従え"]

SendMessage:
  type: "message"
  recipient: "trend-writer"
  content: [上のデータ + "Cセクションの★★★候補を優先してコンテンツ実現性を評価せよ"]
```

---

## Step 4: Analyst — 市場評価フェーズ

CEOから生データ（バズ×需要マトリクス付き）を受け取ったら、以下を評価:

### バズ×需要マトリクスの検証

CEOのマトリクス分類を検証・修正する:
```
- 「静かな需要（★★★）」候補 → 本当に検索需要があるか？ 競合は本当にいないか？
- 「検証済み（★★）」候補 → 差別化の余地があるか？ ニッチを切り出せるか？
- 「ノイズ（★）」候補 → 本当に一過性か？ 意外な収益モデルはないか？
```

### Trend Arbitrage 3条件判定（★★★候補を優先）

| 条件 | 判定方法 | ○/× |
|------|---------|------|
| **Breakout（急上昇）** | Google Trends推移 + X投稿数の増加率 | |
| **Information Gap（供給不足）** | 検索需要あり + コンテンツ少ない（バズ×需要マトリクスの★★★ゾーン） | |
| **High Intent（収益性）** | アフィリ単価、購買意欲、広告RPM | |

### 収益性の試算

```
- Google Trendsトラフィック指標: {RSSの数値}
- 推定月間検索ボリューム: X（トラフィック指標から推定）
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
- バズ×需要マトリクスで★★★ or ★★
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

## ツール設定情報

### Grok MCP（x_search）— 設定済み
```
サーバー名: x_search
ツール: x_search_posts, x_get_user_posts, x_get_trending
コスト: xAI API（$25無料クレジット。超過後は従量課金 $2.50-5/1Kコール）
キー管理: ~/.claude/mcp-servers/x-search-mcp/.env（正本。python-dotenvで読み込み）
```

### Xpoz MCP（xpoz-mcp）— 設定済み
```
ツール: Instagram/TikTok/Reddit検索
コスト: Free枠 100K件/月（課金情報登録不要）
キー管理: ~/.claude.json headers（HTTPトランスポートのため設定ファイルに必要）
```

### Google Trends API — alpha申請中
```
ステータス: 未取得
申請URL: https://developers.google.com/search/apis/trends#apply
エンドポイント: https://trends.googleapis.com/v1alpha/trends:query
認証: OAuth 2.0（scope: trends.readonly）
取得後にツール実装予定（設計案を先に出す）
```

### エスカレーション基準

| 状況 | 対応 | レベル |
|------|------|--------|
| Grok MCP応答なし | **調査中止。** 株主にMCP復旧を依頼 | L2 |
| Xpoz MCP応答なし | 株主に報告。Grok単独で続行 | L1 |
| 両方MCP応答なし | **調査中止。** 株主に全MCP復旧を依頼 | L2 |
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
