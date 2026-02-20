# 仮想機関AI計画 — プロジェクト概要（外部レビュー用）

> このドキュメントは、プロジェクトの構成・設計思想・技術的制約を第三者（他のAI含む）がレビューするためのものです。
> 作成日: 2026-02-16 / 更新日: 2026-02-17

---

## 1. プロジェクト概要

### 何をやっているか
「AIエージェントだけで事業を回す」実験プロジェクト。人間（株主）は週30分〜1時間だけ介入し、残りはAIエージェントが自律的に経営する。

### 使用ツール
- **Claude Code**（Anthropic公式CLI）— Maxプラン（$100/月定額）
- **Opus**（frontmatter: `model: opus`相当）— CEOエージェント（リード）
- **Sonnet**（frontmatter: `model: sonnet`）— 中核エージェント4名
- **Haiku**（frontmatter: `model: haiku`）— 軽量エージェント3名

### 事業構成（3本柱）
1. **SaaS事業**: ShieldMe（誹謗中傷検知SaaS）
2. **コンテンツ事業**: ブログ・有料記事（note等）
3. **動画事業**: YouTube（AI自動生成パイプライン）

### 現在のフェーズ
Phase 0（基盤構築）Step 1→2 移行中。Step 1の大半（調査・仕様策定・LP実装）は完了。エージェント設計の検証・修正も並行中。

---

## 2. 組織構成（8エージェント）

### 指揮系統
```
株主（人間 / 週30分〜1時間の介入）
  └── CEO（リードエージェント / Opus）
        ├── analyst（経営企画部長 / Sonnet）
        ├── product-manager（事業開発部長 / Sonnet）
        ├── writer（広報部長 / Sonnet）
        ├── site-builder（Web制作担当 / Sonnet）
        ├── x-manager（マーケティング部長 / Haiku）
        ├── video-creator（動画制作担当 / Haiku）
        └── legal（法務部長 / Haiku）
```

### 各エージェントの人格

| Agent | キャラクター名 | 年齢/性別 | 一人称 | 語尾の特徴 | 性格 |
|-------|-------------|----------|--------|-----------|------|
| CEO（九条零） | 九条 零 | 30歳/男 | 俺 | 〜だ、〜してくれ | 冷静合理主義者、元コンサル |
| analyst（白河凛） | 白河 凛 | 25歳/女 | わたくし | 〜ですわ、〜かしら | お嬢様、データ狂 |
| product-manager（桐谷翔） | 桐谷 翔 | 27歳/男 | 俺 | 〜だろ、〜じゃね？ | チャラいがガチのプロダクト脳 |
| writer（藤崎あおい） | 藤崎 あおい | 24歳/女 | あたし | 〜なの、〜だわ | 文芸サークル出身、感性派 |
| site-builder（黒崎蓮） | 黒崎 蓮 | 26歳/男 | （使わない） | …、〜かな | 寡黙な職人 |
| x-manager（七瀬美咲） | 七瀬 美咲 | 23歳/女 | うち | 〜じゃん！〜でしょ！ | SNSネイティブ、テンション高い |
| video-creator（朝比奈陸） | 朝比奈 陸 | 22歳/男 | 自分 | 〜っす！〜しょ！ | 最年少の後輩キャラ、擬音多い |
| legal（氷室志帆） | 氷室 志帆 | 28歳/女 | わたし | 〜と存じます、〜でございます | 最年長の姉御、慎重派 |

### エージェント間の人間関係
- analyst（白河）× product-manager（桐谷）: よくバトるが実力は認め合う
- writer（藤崎）× x-manager（七瀬）: 大親友
- site-builder（黒崎）× product-manager（桐谷）: ゲーム仲間
- legal（氷室）: writerの記事を密かに楽しみにしている

---

## 3. 技術アーキテクチャ

### Claude Code のサブエージェント起動の仕組み

Claude Codeでは `Task` ツールの `subagent_type` パラメータでカスタムエージェントを起動できる。

```
CEO（リードエージェント）
  → Task tool (subagent_type: "analyst")
    → 新しいClaude子プロセスが起動
```

### `.claude/agents/*.md` の構造と挙動

各エージェントの定義ファイルは以下の構造:

```markdown
---
name: analyst              # 名前
description: 説明文         # 親エージェントに表示される説明
model: sonnet              # 使用モデル
memory: project            # メモリ設定
tools:                     # 許可ツール
  - WebSearch
  - Read
  - Write
  ...
maxTurns: 25               # 最大ターン数
---

（ここから下がbody — ミッション、担当領域、フレームワーク等の詳細指示）
```

#### 重大な発見: bodyは自動注入されない

テストにより以下が判明:

| コンテキスト | サブエージェントに自動注入されるか |
|---|---|
| `.claude/agents/*.md` の **frontmatter** | model, tools, maxTurns, memory が適用される |
| `.claude/agents/*.md` の **body** | サブエージェントのシステムプロンプトに含まれない |
| `CLAUDE.md`（プロジェクト指示） | 全エージェントに共通で注入される |
| `.claude/agent-memory/*/MEMORY.md` | `memory: project` 設定時に個別注入される |
| Task toolの `prompt` 引数 | CEOが書いた指示文がそのまま渡される |

### 3層コンテキストモデル（採用した設計）

```
┌─────────────────────────────────────────────┐
│ Layer 1: CLAUDE.md（全員共通 / 自動注入）      │
│  - 組織ルール、指揮系統、禁止事項              │  ← ~55行に圧縮
│  - CEO起動指示（ceo-manual.mdを読め）         │
│  - サブエージェント起動指示                    │
├─────────────────────────────────────────────┤
│ Layer 2: MEMORY.md（個別 / 自動注入）          │
│  - キャラクター設定（名前、口調、NG/OK例）     │  ← 先頭 ~10行
│  - 起動ルーティン（「定義を読め」指示）         │  ← 次の ~3行
│  - 蓄積されたナレッジ（学び、判断、メモ）      │  ← 残り ~155行
│  ※ 200行を超えると末尾が切り捨てられる         │
├─────────────────────────────────────────────┤
│ Layer 3: agents/*.md body（手動参照 / 非注入）  │
│  - 詳細な担当領域、フレームワーク              │
│  - 出力フォーマット、連携ルール                │
│  - 人間関係設定                              │
│  - エージェントが起動時にReadツールで読む       │
│  ※ 1ターン消費するが、全情報が手に入る         │
└─────────────────────────────────────────────┘
```

**設計判断のポイント**:
- CLAUDE.mdを55行に圧縮し、全サブエージェントへのトークンコストを最小化
- MEMORY.mdの先頭にキャラ設定を置くことで、200行制限で切り捨てられる心配がない
- 人間関係設定はagents/*.md bodyに配置（MEMORY.mdの容量を節約）
- CEOは2段階起動（通常: status.md / フル: + plan.md + validate-docs.py）

---

## 4. ドキュメント体系

### 3ファイル統合構成（旧6ファイルから集約）

| ファイル | 内容 | 更新者 |
|---------|------|--------|
| `docs/plan.md` | 事業計画（Part 1）+ ロードマップ（Part 2） | 株主承認で変更 / CEO |
| `docs/status.md` | KPI + アクション管理 + 収支 | CEO / analyst |
| `docs/decisions.md` | 意思決定ログ | CEO |

補助ドキュメント:
| ファイル | 内容 |
|---------|------|
| `docs/ceo-manual.md` | CEO専用マニュアル（人格・起動モード・判断基準） |
| `docs/design-rules.md` | サイトデザインルール |
| `docs/specs/` | 仕様書・調査レポート |
| `docs/legal/` | 利用規約、法務レビュー |

### ディレクトリ構成

```
ai-agency-hq/
├── CLAUDE.md                    # 組織ハンドブック（全員に自動注入、~55行）
├── .claude/
│   ├── agents/                  # エージェント定義
│   │   └── {agent-name}.md     #   frontmatter=起動設定, body=詳細リファレンス
│   ├── agent-memory/            # 各エージェントの永続メモリ
│   │   └── {agent-name}/MEMORY.md  # 先頭=キャラ設定, 後半=ナレッジ蓄積
│   └── commands/                # スキル（/startup, /session-log 等）
├── docs/
│   ├── plan.md                  #   事業計画 + ロードマップ
│   ├── status.md                #   KPI + アクション + 収支
│   ├── decisions.md             #   意思決定ログ
│   ├── ceo-manual.md            #   CEO専用マニュアル
│   ├── design-rules.md          #   デザインルール
│   ├── specs/                   #   仕様書・調査レポート
│   ├── legal/                   #   利用規約、法務レビュー
│   └── archive/                 #   アーカイブ
├── site/                        # Webサイト（ai-agency.jp）
├── content/
│   ├── logs/                    #   セッションログ
│   ├── tweets/                  #   X投稿案
│   ├── blog/                    #   ブログ下書き
│   ├── copy/                    #   LP文面等
│   └── videos/                  #   動画企画・台本
├── tools/
│   ├── dashboard/               #   HQダッシュボード（server.py + HTML/CSS/JS）
│   └── validate-docs.py         #   ドキュメント整合性チェッカー
└── reports/                     #   週次レポート・株主報告資料
```

---

## 5. 運営ルール

### 指揮系統
- 上から下へ指示、下から上へ報告
- 部門長が株主に直接報告するのは禁止（CEO経由）
- CEOが部門長の仕事を代行するのも禁止（必ずサブエージェントを呼ぶ）

### 部門長間の横連携
- 作業レベル（成果物受渡し、データ共有）→ 自由
- 判断レベル（戦略変更、方針決定）→ CEO経由必須

### CEO 2段階起動
| モード | いつ使うか | やること |
|--------|-----------|---------|
| 通常モード | 毎セッション | MEMORY.md(自動) + status.md → 軽量チェック3項目 → 最優先アクション実行 |
| フルモード | 週次 or 株主依頼時 | + plan.md + validate-docs.py + セルフチェック全項目 + 改善提案 |

### 財務管理
- AIは自律的に支出できない（実際の支払いは株主が行う）
- 月間コスト上限: ¥55,000（株主承認済み）
- 現在の支出: ¥15,000/月（Claude Max $100）

---

## 6. 成果物（Phase 0 完了済み）

| 成果物 | ファイル | 担当 |
|--------|---------|------|
| 競合調査レポート | docs/specs/market-research-competitors.md | CEO（代行） |
| コンテンツ市場調査 | docs/specs/market-research-content.md | CEO（代行） |
| コスト見積もり | docs/specs/cost-estimate.md | CEO（代行） |
| KPI目標値提案 | docs/specs/kpi-proposal.md | analyst |
| ShieldMe MVP仕様書 | docs/specs/shieldme-mvp-spec.md | product-manager |
| LP文面ドラフト | content/copy/lp-draft-v1.md | writer |
| 動画パイプライン設計 | docs/specs/video-pipeline-design.md | video-creator |
| LP HTML実装 | site/index.html | site-builder |

---

## 7. 既知の課題・制約

### Claude Code固有の制約
1. `.claude/agents/*.md` のbodyが自動注入されない（上記の通り）
2. `claude --agent ceo` で起動するとTask toolが消えるバグ（Issue #13533）
3. MEMORY.mdは200行を超えると末尾が切り捨てられる
4. Agent Teams利用にはMaxプラン（$100/月）が必要

### プロジェクトの課題
1. Phase 0 Step 2進行中（サイト公開・X運用開始が残）
2. ドメイン未取得、Xアカウント未開設（株主承認待ち）
3. ShieldMe MVP開発はX API契約後

---

## 8. レビューしてほしいポイント

1. **3層コンテキストモデルの設計は妥当か？** MEMORY.md（先頭=キャラ、後半=ナレッジ）+ agents/*.md（手動Read）というアプローチに弱点はあるか？
2. **8エージェント体制は適切か？** 現時点（売上ゼロ、環境構築中）で8人は多すぎるか？統合・削減すべきか？
3. **キャラクター設定のROIは？** 各エージェントに人格・口調を設定するコスト（MEMORY.md容量消費、管理負荷）に対して、得られる価値（エンターテインメント性、コンテンツ化の容易さ、エージェント識別性）は見合っているか？
4. **ドキュメント3ファイル統合は妥当か？** plan.md / status.md / decisions.md の3ファイル体制は適切か？
5. **CEO 2段階起動は効果的か？** 通常モード（軽量チェック3項目）とフルモード（全項目チェック）の分離は妥当か？
