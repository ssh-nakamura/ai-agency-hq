# ニッチ需要分析システム — 仕様書

> Status: Draft (2026-02-21)
> Owner: CEO
> 承認: 未承認（株主レビュー中）

---

## 1. 目的

Type B事業（ニッチ独立ブランド）の選定に、データに基づく判断基準を提供する。
「何が熱いか」を市場から拾い、「行けるか」を数字で判定し、Go/NoGoを出す。

---

## 2. 設計方針

- 事前にキーワードを決め打ちしない。市場から拾って定量評価する
- 株主が「これ見ろ」と言えば途中ステージから直接入れる
- 現時点はワンショット手動実行。自動化は検証後
- 使えないステップは捨てる。全部入りにしない
- **AIで実行可能なコンテンツに限定する**（下記参照）

### コンテンツ適格性フィルタ（全ステージ共通の絶対ルール）

Type Bは「AIが生産手段」。**嘘をつかない。持っていない経験・資格・立場を詐称しない。**

#### 絶対禁止（これをやったら事業として終わる）
- **経験の捏造**: 合格していない資格の体験記、行っていない場所の旅行記、使っていない商品の使用感レビュー
- **立場の詐称**: 営業じゃないのに営業のフリ、専門家じゃないのに専門家のフリ、人間じゃないのに人間のフリ
- **実績の虚偽**: 稼いでいない金額の収益報告、達成していない成果の主張

#### できる（嘘にならないコンテンツ）
- ニュース（公開情報のまとめ・解説・速報・キュレーション）
- 雑学・トリビア・豆知識（事実ベース）
- 歴史（公開資料に基づく解説・紹介・年表）
- 紹介系（公開スペックに基づく比較・ランキング）
- ハウツー・教育（公開情報の整理・解説）
- データ分析・考察（数字に基づく解説）
- 占い・診断系（エンタメとして明示）
- テンプレート・プロンプト等のデジタル商品

#### できない（嘘になる or 物理的に不可能）
- 体験していないことの体験記
- 持っていない資格・スキルの指導
- 物理的なハンドメイド・物販・製造
- 対人営業・コンサル・コーチング
- 顔出し・ライブ配信前提のコンテンツ

---

## 3. データソース

### 検証済み（2026-02-21実施）

| ソース | 用途 | 信頼性 | コスト | 検証結果 |
|--------|------|--------|--------|---------|
| **Grok API（直叩き）** | Trend Scan主軸。x_search で実ツイート検索 | ★★★ | ~$0.56/call | **◎ 具体的ニッチが実ツイートURL付きで出る** |
| Xpoz Twitter (MCP) | Stage 3の定量評価（件数・エンゲージメント） | ★★ | Free 100K/月 | △ Trend Scanには使えない（広すぎてゴミ）。定量評価向き |
| Xpoz Reddit (MCP) | Stage 3の定量評価（投稿数・スコア） | ★★ | Free | △ 同上。広域検索はスパムまみれ |
| Xpoz Instagram (MCP) | Stage 3の定量評価（再生数・いいね） | 未検証 | Free | - |
| yt-dlp (CLI) | YouTube再生数 | ★★ | Free | 未検証 |

### 未検証（検証予定）

| ソース | 用途 | 状態 |
|--------|------|------|
| Google Trends API（公式alpha） | 検索需要の基盤指標 | alpha申請済み（2026-02-21）。通過待ち |
| DataForSEO | Google Trends代替 | 未検証。alpha通過まで要検証 |

### 使わない

- pytrends: アーカイブ済み・429頻発
- trendspyg: 非公式スクレイパー・同じ429問題
- Xpoz広域検索（Trend Scan用途）: ノイズ多すぎで使い物にならない（検証済み）

### Grok API呼び出し仕様

- エンドポイント: `POST https://api.x.ai/v1/responses`
- モデル: `grok-4-1-fast`（server-side toolsはgrok-4系のみ対応）
- ツール: `{"type": "x_search"}`（x_semantic_search + x_keyword_search を自動実行）
- 認証: `Authorization: Bearer {XAI_API_KEY}`
- APIキー保存先: `~/.claude/mcp-servers/x-search-mcp/.env`
- MCPは使わない。curlまたはPython httpxで直叩き

---

## 4. 全体フロー（3段構成）

```
トリガー（株主指示 / CEO手動実行）
       │
       ▼
┌─────────────────────┐
│ Stage 1: Trend Scan │  今何が熱いか、生データを取る
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 2: Discovery  │  生データをニッチ候補に加工する
└──────────┬──────────┘
           │
           ▼
  株主が候補を選択（1-5件）
  or 株主が直接キーワード指定 → Stage 3へスキップ
           │
           ▼
┌─────────────────────┐
│ Stage 3: Evaluation │  候補を6指標で定量スコアリング
└──────────┬──────────┘
           │
           ▼
  スコアカード出力 → Go/NoGo判定
           │
       ┌───┴───┐
       ▼       ▼
     Go:     NoGo:
  Type B     候補廃棄
  立ち上げ   （理由記録）
```

---

## 5. Stage 1: Trend Scan（トレンド検索）

### 目的
「AIでコンテンツ化できるニッチ」の候補を市場から拾い出す。

### 入力
- なし（フルスキャン）
- or 広域カテゴリ指定（例: "歴史", "雑学", "ニュース", "レビュー"）

### データソース: Grok x_search 直叩き（主軸）

Grok Responses API に以下のプロンプトを投げる。1回のAPI callで複数のx_searchが自動実行される。

**プロンプト設計（EN版）:**
```
Search X/Twitter for content niches where AI-generated content is performing well.
Focus on: news summaries, trivia/fun facts, history explainers, product reviews,
how-to guides, rankings, data analysis, fortune telling, educational content.
Exclude: handmade/physical products, personal services, art commissions,
travel vlogs, face-on-camera content.
Show real tweets from the last 30 days where people are building audiences
or monetizing in these content niches. Include engagement metrics.
```

**プロンプト設計（JP版）:**
```
X/Twitterで、AIを使ったコンテンツ発信で伸びているニッチを探してください。
対象: ニュースまとめ、雑学・トリビア、歴史解説、商品レビュー・比較、
ハウツー、ランキング、占い・診断、教育コンテンツ。
除外: ハンドメイド、物販、対面サービス、アートコミッション、旅行vlog、顔出し。
直近30日で、これらのニッチでフォロワーを増やしたり収益化しているツイートを
実例付きで見せてください。
```

### 補助データソース（Grokで拾えない領域を補完）

| # | ソース | 用途 | 条件 |
|---|--------|------|------|
| 1 | Google Trends API / DataForSEO | 検索ボリューム上昇中のコンテンツ系キーワード | API利用可能になり次第 |
| 2 | yt-dlp | YouTube検索で「解説」「まとめ」「雑学」系の急上昇チャンネル | Stage 3で検証後 |

※ Xpoz広域検索はTrend Scanには使わない（検証済み: ノイズが多すぎて使い物にならない）

### 出力
Grokが返す実ツイートURL付きのニッチ候補リスト（生データ）。

```
--- Grok x_search結果（EN） ---
1. AI歴史解説チャンネル: @xxxが月10万フォロワー到達 [tweet URL]
2. 雑学botアカウント: 「Did you know」系で日次1万impression [tweet URL]
3. 商品比較ブログ: AI生成レビューでアフィリエイト収益報告 [tweet URL]
...

--- Grok x_search結果（JP） ---
1. 歴史解説アカウント: 「今日の歴史」で月5万フォロワー [tweet URL]
2. AI占いbot: 毎日の運勢投稿で高エンゲージメント [tweet URL]
...
```

### コスト見積もり
- EN版1回 + JP版1回 = 約$1.12/scan

---

## 6. Stage 2: Discovery（候補化）

### 目的
Stage 1の生データにフィルタをかけ、評価対象のニッチ候補リストに加工する。

### 入力
Stage 1の出力（Grok x_search生データ）

### 処理ステップ

1. **AI実行可能性フィルタ**: 物理作業・対面・顔出し前提のニッチを除外
2. **コンテンツ形式の特定**: 各ニッチが成立する媒体を判定
   - YouTube向き: 解説・歴史・雑学・比較
   - ブログ/note向き: レビュー・ハウツー・ランキング
   - X/Twitter向き: ニュース速報・トリビア・占い
   - Instagram/TikTok向き: 短尺トリビア・ビジュアル比較
3. **クラスタリング**: 類似キーワードをグルーピング
   - 「歴史解説」「歴史雑学」「today in history」→ 同一ニッチ
   - 「AI占い」「タロット」「運勢」→ 同一ニッチ
4. **重複排除**
5. **EN/JPペアリング**: 英語キーワードと日本語キーワードの対応付け
6. **初期シグナル付与**: Grok結果から見えるエンゲージメント情報を付記

### 出力
候補ニッチリスト（10-20件）

```
| # | ニッチ名 | EN keyword | JP keyword | 適合媒体 | Grokシグナル |
|---|---------|------------|------------|---------|-------------|
| 1 | 歴史解説 | history explainer | 歴史解説 | YT, ブログ | @xxx 月10万フォロワー |
| 2 | AI占い | AI tarot/fortune | AI占い | X, TikTok | @xxx 日次1万impression |
| 3 | 商品比較 | product comparison | 商品比較 | ブログ, YT | アフィリエイト収益報告あり |
| ... | | | | | |
```

### この段階でCEO → 株主に報告
「この中からどれを深掘りするか」を株主に選んでもらう。
株主が直接キーワード指定した場合はStage 1-2をスキップしてStage 3へ。

---

## 7. Stage 3: Evaluation（定量評価）

### 目的
候補ニッチを6指標で定量スコアリングし、Go/NoGoを判定する。

### 入力
- キーワード 1-5個（Stage 2の出力 or 株主手動指定）
- 各キーワードのEN/JPペア

### 重要ルール: 全Step EN/JP並行実行

Step 1-6は**すべてENキーワードとJPキーワードの両方で実行する**。
Step 5でその比率を算出する。片方だけ実行して比較できない状態は禁止。

### 評価指標（7 Steps）

#### Step 1: 需要ボリューム
「このニッチにどれだけの需要があるか」

| ソース | API/ツール | 取得値 | 単位 |
|--------|-----------|--------|------|
| YouTube | yt-dlp | 上位20本の再生数合計 | 回 |
| X/Twitter | Xpoz `countTweets` | 総ツイート数 | 件 |
| X/Twitter | Grok x_search直叩き（直近30日 vs 前30日） | 言及量の増減率 | % |
| Reddit | Xpoz `getRedditPostsByKeywords` | 投稿総数 | 件 |

※ Google Trends API / DataForSEOは現時点では使わない。yt-dlpで不足した場合に検討。

#### Step 2: エンゲージメント密度
「需要があるだけでなく、人が反応しているか」

| ソース | API/ツール | 取得値 | 算出指標 |
|--------|-----------|--------|---------|
| X/Twitter | Xpoz `getTwitterPostsByKeywords` | likeCount, retweetCount, impressionCount | ER = (like+RT) / impression |
| Reddit | Xpoz `getRedditPostsByKeywords` | score, commentsCount | CR = comments / score |
| Instagram | Xpoz `getInstagramPostsByKeywords` | likeCount, videoPlayCount | LR = likes / plays |

上位50投稿の平均値を算出。

#### Step 3: ナレッジギャップ（質問量）
「教えて系の質問が多い = コンテンツの余地がある」

| ソース | API/ツール | 検索クエリ | 取得値 |
|--------|-----------|-----------|--------|
| Reddit | Xpoz `getRedditPostsByKeywords` | "how to" OR "help" OR "beginner" AND {keyword} | 投稿数 |
| Reddit | Xpoz `getRedditCommentsByKeywords` | 同上 | コメント数 |
| X/Twitter | Grok x_search直叩き | "{keyword} 初心者 教えて" / "{keyword} how to start" | 投稿数 |

代表的な質問内容トップ10を抽出。

#### Step 4: 競合供給量（飽和度）
「すでにコンテンツが飽和していないかを測る」

| ソース | API/ツール | 取得値 | 意味 |
|--------|-----------|--------|------|
| YouTube | yt-dlp | チャンネル数 + 登録者分布 | YouTube上の供給者数 |
| X/Twitter | Xpoz `getTwitterUsersByKeywords` | ユニーク発信者数 | この話題で発信してる人の数 |
| X/Twitter | Grok x_search直叩き | "ブログ" OR "blog" AND {keyword} | 既存メディアの数 |

#### Step 5: 需給ギャップスコア ← 新設（Trend Arbitrageの核心）
「需要が高くて供給が少ない穴を見つける」

```
ギャップスコア = Step 1 需要スコア ÷ Step 4 供給スコア
```

ギャップスコアが高い = 需要に対して供給が追いついていない = 参入チャンス。
ギャップスコアが低い = レッドオーシャン = 避ける。

#### Step 6: ローカライズ倍率
「英語圏で大きくて日本語圏で小さい = チャンス」

Step 1-4のEN値 / JP値を比較。

```
ローカライズ倍率 = EN需要値 / JP需要値
EN供給倍率 = EN供給値 / JP供給値
```

需要倍率が高い AND 供給倍率も高い = 日本語圏でまだ誰もやっていない = 最大のチャンス。

#### Step 7: 商業シグナル
「お金が動いているか」

| ソース | API/ツール | 検索クエリ | 取得値 |
|--------|-----------|-----------|--------|
| X/Twitter | Grok x_search直叩き | "{keyword} アフィリエイト" / "{keyword} monetize" | 商業投稿数 |
| Instagram | Xpoz `getInstagramPostsByKeywords` | "{keyword} PR" / "{keyword} sponsored" | 広告系投稿の割合 |

### 最終出力: スコアカード

各ニッチにつき1枚。EN/JP両方の数字を並記。

```
ニッチ: 歴史解説 / history explainer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          EN              JP
Step 1 需要ボリューム:    YT: 12M views   YT: 800K views
                          Tweets: 8,400   Tweets: 1,200
                          トレンド: +45%  トレンド: +12%
Step 2 エンゲージメント:  ER: 4.2%        ER: 3.1%
Step 3 ナレッジギャップ:  質問: 2,400件   質問: 180件
Step 4 競合供給量:        YTch: 340       YTch: 28
                          発信者: 4,200   発信者: 310
Step 5 需給ギャップ:      EN: 1.8x        JP: 3.2x ← JP供給不足
Step 6 ローカライズ倍率:  需要 EN/JP = 10x / 供給 EN/JP = 12x
Step 7 商業シグナル:      商業投稿率: 22%  商業投稿率: 8%

総合判定: Go
理由: JP需給ギャップ3.2x（供給不足）、ローカライズ倍率12x（先置きチャンス大）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

総合判定: Go / NoGo
理由: ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 8. 検証結果ログ（2026-02-21）

### 実施済み

| テスト | ツール | 結果 | 判定 |
|--------|--------|------|------|
| Xpoz Reddit広域検索 | getRedditPostsByKeywords | 4,815件。スパム・MLM投稿が大半。ニッチ発見に使えない | NG（Trend Scan不適） |
| Xpoz Redditサブレディット | searchRedditSubreddits | 傘カテゴリのみ（r/WorkOnline等）。具体ニッチ出ず | NG（Trend Scan不適） |
| Xpoz Twitter広域検索 | getTwitterPostsByKeywords | 50万件。FXスパム・無関係投稿9割。シグナル埋没 | NG（Trend Scan不適） |
| Grok chat completion | /v1/chat/completions | LLM生成テキスト。数字は幻覚。実データではない | NG（データソースにならない） |
| **Grok x_search直叩き** | /v1/responses + x_search | 実ツイートURL付きで具体ニッチが出る。10回のx_search自動実行 | **◎ Trend Scan主軸に採用** |
| **Stage 1 EN版 実行テスト** | Grok x_search直叩き | ニュースまとめ自動化（488 likes, 38.9K views）、テンプレ販売（$100K+/月報告）、データ可視化（265K subs） | **◎ 具体ニッチ+エンゲージメント付き** |
| **Stage 1 JP版 実行テスト** | Grok x_search直叩き | 雑学ショート動画（月50万-1000万自称）、プロンプト販売（526 likes, 38K views）、ニュース速報（4,827 likes, 1.6M views） | **◎ JP独自ニッチも検出** |
| **Stage 2 Discovery テスト** | CEO手動処理 | 6候補に絞り込み（雑学ショート/ニュースまとめ/データ可視化/テンプレ販売/AI占い/歴史解説） | **◎ 候補リストとして機能** |

### Stage 1-2 実行結果サマリー（2026-02-21）

**EN版で検出されたニッチ:**
1. ニュースまとめ自動化: @Zephyr_hg（488 likes, 38.9K views）— AI自動投稿でビジネススケール
2. データ可視化: 「Memeable Data」（YouTube 265K subs, 20.5M views）
3. ハウツー・テンプレ販売: @X_FINALBOSS（290 likes, 25K views）— $100K+/月 ebook販売

**JP版で検出されたニッチ:**
1. 雑学ショート動画: @Kirara_A1, @kaneki_ai888（217-230 likes, 16-21K views）— 台本AI→CapCut自動生成
2. プロンプト/テンプレ販売: @ai_zaitaku（526 likes, 38K views）— 占い・Amazonアフィ導線
3. ニュース速報・データ分析: @masahirochaen（900 likes, 221K views）— AI×freee分析

**注意:** JP側の収益主張（月商1億、成功率91%等）は情報商材の煽り。数字は鵜呑みにできないが「そのニッチで集客できている」事実自体は需要の証拠。

### 学び
- Xpozは「広く浅く」は得意だがTrend Scan（ニッチ発見）には不向き。Stage 3の定量評価向き
- Grokはx_searchツール付きのResponses APIが本命。chat completionは幻覚を返す
- Grok Responses APIはgrok-4系モデルのみ対応（grok-3-fastは不可）
- **Stage 1は実用レベル。EN/JP並行でニッチ候補が実ツイートURL付きで出る**
- **Stage 2は現時点CEO手動処理で十分機能する。自動化は後回し**
- **EN/JP共通ニッチ（ニュースまとめ、テンプレ販売）と独自ニッチ（JP:雑学ショート、EN:データ可視化）が分離できる**

---

## 9. 未決事項

| # | 項目 | 状態 | 決定時期 |
|---|------|------|---------|
| 1 | Google Trends API alpha申請 | 申請済み（2026-02-21） | Google次第 |
| 2 | DataForSEO導入判断 | 未検証 | alpha通過しなかった場合 |
| 3 | ★スコアの閾値 | 未設定 | 全Step検証後、データが溜まってから |
| 4 | 6指標の重み付け | 未設定 | 全Step検証後 |
| 5 | 自動化（cron等） | 不要（現時点） | 手動運用が回らなくなったら |
| 6 | Grok x_searchのコスト最適化 | $0.56/callが高すぎないか | 月間予算との照合後 |
| 7 | Stage 3でのXpoz活用 | 定量評価にはXpozが向く仮説 | Stage 3検証時 |

---

## 10. 検証計画

テスト対象ニッチ: **「副業 / side hustle」**（Stage 1-2は汎用テスト実施済み）

| 順序 | 検証内容 | 判定基準 | 状態 |
|------|---------|---------|------|
| 0 | Google Trends API / DataForSEO疎通 | 検索ボリュームデータが取れるか | alpha申請中（保留） |
| 1 | Stage 1: Trend Scan（Grok x_search） | 生データが取れるか | **◎ 完了** |
| 2 | Stage 2: Discovery加工 | 候補リストとして使い物になるか | **◎ 完了** |
| 3 | Stage 3: Step 1-7各ステップ | 数字が取れるか、ニッチ間比較に使えるか | **← 次はここ** |
| 4 | スコアカード統合 | 最終出力がGo/NoGo判断の材料になるか | 未着手 |

各ステップを1つずつ実行し、出力を株主に見せて判定。使えないステップは捨てる。

---

## 11. システム設計（技術アーキテクチャ）

### 自動/手動の境界

### 実行レイヤーの分離（トークン節約設計）

**原則: データ収集・整形はPythonスクリプト。判断・報告はCEOセッション。**

スクリプトで済む処理をClaude上で回すとトークンを無駄食いする。
API叩き・JSON保存・スコア算出は全部Pythonが担当し、CEOは結果ファイルを読んで判断するだけ。

```
┌─ Pythonスクリプト（トークン消費ゼロ）─────────────────────────┐
│                                                             │
│  [Stage 1] trend_scan.py                                    │
│    Grok API × 2回 → stage1-raw-en.json, stage1-raw-jp.json │
│                                                             │
│  [Stage 3] evaluation.py                                    │
│    Xpoz/Grok/yt-dlp × 28回 → eval/{niche-id}.json          │
│                                                             │
│  [Scorecard] scorecard.py                                   │
│    eval/*.json → scorecards/{niche-id}.md, summary.md       │
│                                                             │
│  [共通] フォルダ作成、meta.json書き出し、ファイル保存          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ CEOセッション（トークン消費）──────────────────────────────┐
│                                                             │
│  [Stage 2] stage2-candidates.md を読んでフィルタ・判断       │
│    → 候補の適格性判断、クラスタリング、リスク評価             │
│    → stage2-candidates.json / .md を書き出し                 │
│                                                             │
│  [報告] scorecards/summary.md を読んで株主に報告             │
│    → Go/NoGo理由の言語化、次アクションの提案                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 実行フロー（コマンド順序）

```bash
# ① Stage 1: トレンドスキャン（スクリプト）
python3 tools/niche-analyzer/cli.py scan
# → content/niche-analysis/scans/2026-02-21/ に生データ保存

# ② Stage 2: CEOがstage1結果を読んで候補化（CEOセッション内）
# → stage2-candidates.json / .md を出力

# ③ 株主が候補を選択

# ④ Stage 3: 定量評価（スクリプト）
python3 tools/niche-analyzer/cli.py evaluate \
  --scan-dir content/niche-analysis/scans/2026-02-21 \
  --niches trivia-shorts,news-curation,ai-fortune
# → eval/*.json + scorecards/*.md を自動生成

# ⑤ CEOがsummary.mdを読んで株主にGo/NoGo報告（CEOセッション内）
```

### API呼び出し回数（1ニッチあたり）

| API | 回数 | コスト | 実行場所 |
|-----|------|--------|---------|
| Grok x_search (Stage 1) | 2回 | $1.12 | スクリプト |
| Grok x_search (Stage 3) | 8回 (4 Step × EN/JP) | $4.48 | スクリプト |
| Xpoz MCP | 14回 | $0（Free枠） | スクリプト |
| yt-dlp | 4回 | $0 | スクリプト |
| **合計** | **28回** | **≒$5.60/ニッチ** | **全てスクリプト** |

3ニッチ評価 = 約$16.80 + Stage 1の$1.12 = **約$18/scan**
Claudeトークン消費: Stage 2の判断 + 結果報告のみ（API呼び出し分はゼロ）

### ファイル構成

```
tools/niche-analyzer/
├── cli.py              # CLIエントリポイント（scan / evaluate / scorecard）
├── trend_scan.py       # Stage 1: Grok API EN/JP呼び出し → JSON保存
├── evaluation.py       # Stage 3: Step 1-7 全API呼び出し → JSON保存
├── scorecard.py        # eval/*.json → scorecards/*.md 生成
├── grok_client.py      # Grok Responses API ラッパー（httpx）
├── xpoz_client.py      # Xpoz MCP HTTP呼び出しラッパー
├── ytdlp_client.py     # yt-dlp CLIラッパー
└── config.py           # APIキー・閾値・プロンプトテンプレート
```

※ discovery.py は不要。Stage 2はCEOの判断作業であり、スクリプト化するほどルール化できない。

### スキル連携（全検証後に実装）

```
/niche-scan    → cli.py scan を実行 → stage1結果を読んでStage 2をCEO実行
/niche-eval    → cli.py evaluate を実行 → summary.mdを読んで株主に報告
```

スキルはスクリプトの「呼び出し + 結果の読み取り・報告」だけ担当。データ収集はスクリプトがやる。

### 出力データ管理

全ステージの出力をファイルとして保存する。スキャン結果は再利用・振り返りのための資産。

#### ディレクトリ構造

```
content/niche-analysis/
├── scans/
│   └── YYYY-MM-DD/                    # スキャン実行日（同日2回目は -2）
│       ├── meta.json                  # メタ情報（実行日時、コスト、パラメータ）
│       │
│       ├── stage1-raw-en.json         # Stage 1: Grok EN生レスポンス
│       ├── stage1-raw-jp.json         # Stage 1: Grok JP生レスポンス
│       │
│       ├── stage2-candidates.json     # Stage 2: 候補リスト（機械用）
│       ├── stage2-candidates.md       # Stage 2: 候補リスト（人間用）
│       │
│       ├── eval/                      # Stage 3: ニッチ別評価データ
│       │   ├── trivia-shorts.json     #   各Step1-7の生数値
│       │   ├── news-curation.json
│       │   └── ...
│       │
│       └── scorecards/                # スコアカード
│           ├── trivia-shorts.md       #   ニッチ別スコアカード
│           ├── news-curation.md
│           └── summary.md             #   全ニッチ比較サマリー + Go/NoGo
│
└── archive/                           # 古いスキャン（3ヶ月超過分を移動）
```

#### 各ファイルの中身

**meta.json** — スキャン全体のメタデータ
```json
{
  "scan_date": "2026-02-21",
  "trigger": "manual",
  "category_filter": null,
  "stage1_cost_usd": 1.12,
  "stage3_cost_usd": 11.20,
  "total_cost_usd": 12.32,
  "niches_evaluated": ["trivia-shorts", "news-curation"],
  "grok_model": "grok-4-1-fast"
}
```

**stage1-raw-en.json / stage1-raw-jp.json** — Grok APIレスポンスそのまま保存
- 後から再解析・プロンプト改善の素材になる
- 生レスポンスなので加工しない

**stage2-candidates.json** — 機械処理用の候補リスト
```json
[
  {
    "id": "trivia-shorts",
    "name_en": "Trivia Shorts",
    "name_jp": "雑学ショート動画",
    "keyword_en": "trivia shorts",
    "keyword_jp": "雑学 ショート",
    "platforms": ["youtube_shorts", "tiktok"],
    "grok_signal": "JP月50万報告。台本AI→CapCut自動生成",
    "source_tweets": ["https://x.com/..."]
  }
]
```

**stage2-candidates.md** — 株主が読む用
- 前述のDiscovery出力テーブル形式

**eval/{niche-id}.json** — 各ニッチの7 Step生データ
```json
{
  "niche_id": "trivia-shorts",
  "keyword_en": "trivia shorts",
  "keyword_jp": "雑学 ショート",
  "evaluated_at": "2026-02-21T14:30:00+09:00",
  "steps": {
    "step1_demand": {
      "en": {"yt_views": 5200000, "tweets": 3400, "trend_pct": 32, "reddit_posts": 890},
      "jp": {"yt_views": 800000, "tweets": 1200, "trend_pct": 18, "reddit_posts": 45}
    },
    "step2_engagement": { "en": {"er": 0.042}, "jp": {"er": 0.031} },
    "step3_knowledge_gap": { "en": {"questions": 2400}, "jp": {"questions": 180} },
    "step4_supply": { "en": {"yt_channels": 340, "publishers": 4200}, "jp": {"yt_channels": 28, "publishers": 310} },
    "step5_gap_score": { "en": 1.8, "jp": 3.2 },
    "step6_localization": { "demand_ratio": 10.0, "supply_ratio": 12.0 },
    "step7_commercial": { "en": {"commercial_rate": 0.22}, "jp": {"commercial_rate": 0.08} }
  }
}
```

**scorecards/{niche-id}.md** — ニッチ別スコアカード（仕様書のスコアカード形式）

**scorecards/summary.md** — 全ニッチ横並び比較 + Go/NoGo判定

#### 命名規則

- スキャン日フォルダ: `YYYY-MM-DD`（同日2回目は `YYYY-MM-DD-2`）
- ニッチID: 英語小文字ケバブケース（例: `trivia-shorts`, `news-curation`, `ai-fortune`）
- ファイル名にスペース・日本語を使わない

#### 保持ポリシー

- `scans/` 直下: 直近3ヶ月分を保持
- 3ヶ月超過: `archive/` に移動（手動。自動化は後回し）
- Go判定が出たニッチのスキャン結果は永久保持（Type B立ち上げの根拠資料）

### 未決（技術）

| # | 項目 | 備考 |
|---|------|------|
| 1 | Stage 2のLLM支援範囲 | ルールベースだけで足りるか、Claude呼び出しが必要か |
| 2 | Xpoz MCPの呼び出し方法 | CEOセッション内MCP直接 or subprocess |
| 3 | 並列実行 | asyncioで複数API同時呼び出しするか |
