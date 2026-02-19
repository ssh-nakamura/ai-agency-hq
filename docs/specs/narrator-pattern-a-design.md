# narrator Pattern A 設計書

## 調査者: CEO（オーケストレーター）
## 調査日: 2026-02-19
## ステータス: 設計完了・株主レビュー待ち

---

## 1. 問題定義

前回のnarrator試験で、全8キャラクターが**実際にはエージェントが生成していない内容**を語る「パターンC」が発生した。

| パターン | 定義 | 正否 |
|---------|------|------|
| A | 実際のエージェント出力を、対応するキャラの口調に変換 | ✅ 正解 |
| B | 出力したエージェントのキャラのみ登場 | △ Aの副次ルール |
| C | 全キャラが架空の発言をする | ❌ 発生した問題 |

**要件**: narrator は Pattern A で動作すること。

---

## 2. 先行事例の調査結果

### 調査方法
- Web検索: 「narrative AI agent event log to character dialogue」「StoryBox narrator agent」「AutoGen TransformMessages」「AI character conversion pipeline」等
- 論文・プロダクト: 5件を精査

### 主要事例

| 事例 | 方式 | narrator との類似性 |
|------|------|-------------------|
| **StoryBox** (Narrative AI) | イベントログ → Narrator Agent → 散文 | ✅ 最も近い。構造化ログをキャラ視点の文章に変換 |
| **LIGS** (CHI 2025) | キャラカード + イベントログ → キャラ台詞生成 | ✅ キャラプロフィール + 事実ログの2入力構造が同一 |
| **Neuro-sama** | 構造化データ → キャラLLM → 音声 | ✅ 入力が構造化、出力がキャラ口調のテキスト |
| **AutoGen TransformMessages** | メッセージ変換パイプライン | △ 変換レイヤーの概念は同じだが汎用的 |
| **Narrative Science (Quill)** | 構造化データ → 自然言語レポート | △ キャラ性は薄いが「データ→文章」変換の元祖 |

### 先行事例からの学び

1. **入力は構造化すべき**: StoryBox/LIGS とも、自由文ではなく `{agent, action, result}` 形式の構造化入力を使用
2. **キャラプロフィールは別ファイルで管理**: LIGS の「キャラカード」パターン → narrator.md に既に実装済み
3. **Prompt Engineering + Few-shot で十分**: LIGS論文でファインチューニング不要と結論。Role Prompting + 数例の例文で精度確保可能
4. **登場キャラは入力に基づいて決定**: StoryBox は関与したエージェントのみ登場させる

---

## 3. 内部ログ構造の調査結果

### 調査方法
- 実セッション `617c131a` (Teams方式, 5308行, 61サブエージェント) を精査
- 実セッション `0ba3b1bb` (Task方式) を精査
- `content/logs/` の人間可読ログ5件を精査
- `tools/dashboard/server.py` の `detect_agent()` ロジックを確認

### データソース一覧

#### A. Task方式（サブエージェント）

**結果通知の形式**:
```xml
<task-notification>
<task-id>ad664fa</task-id>
<status>completed</status>
<summary>Agent "KPI目標値の提案+調査レビュー" completed</summary>
<result>
完了しました。CEOへの報告をまとめます。
---
## 報告（analyst → CEO）
（エージェントの実際の出力テキスト）
</result>
</task-notification>
```

**エージェント特定方法**:
1. `<summary>` 内の description（Task 呼び出し時の description パラメータ）
2. 親JSONL の `Task` tool_use ブロック: `"subagent_type": "analyst"`

#### B. Teams方式（チームメイト）

**レポートの形式**:
```xml
<teammate-message teammate_id="site-builder" color="blue" summary="LP実装完了、Task #1をcompletedに更新">
# サイト更新報告

## 対応内容
- LP（index.html）を新規作成。writerのドラフト（lp-draft-v1.md）の文面を忠実に反映

## 変更ファイル
- `site/index.html`（新規）
...
</teammate-message>
```

**エージェント特定方法**:
1. `teammate_id` 属性に直接エージェント名が入る（最も信頼性が高い）
2. `summary` 属性に要約

#### C. セッションログ（content/logs/）

**形式** (人間可読Markdown):
```markdown
## 参加者
- CEO（リードエージェント）
- analyst（KPI提案）
- product-manager（ShieldMe MVP仕様書）

### 2. 4エージェント並行稼働
| エージェント | タスク | 結果 |
|---|---|---|
| analyst | A-004 KPI目標値提案 | 承認。3シナリオ×3フェーズ×3事業 |
| writer | A-006 LP文面ドラフト | 承認。キャッチコピー「社長も、部長も、全員AI。」 |
```

**エージェント特定方法**:
1. 「参加者」セクション
2. テーブルの「エージェント」列

#### D. サブエージェント詳細ログ（content/logs/*-{agent-name}.md）

**形式** (例: `2026-02-15-session3-video-creator.md`):
```markdown
# セッションログ - 2026-02-15（セッション3）
## video-creator による A-011 完了報告

**実施者**: video-creator（動画制作担当）
**タスク**: A-011: YouTube動画パイプラインの調査・設計
**成果物**: `docs/specs/video-pipeline-design.md`

## 実施内容
### 1. 起動ルーティン実行
### 2. Web調査実施
（実施した検索5クエリ、結果の詳細）
```

---

## 4. 実現可能性の評価

### 技術的実現可能性: ✅ 高い

| 要素 | 評価 | 根拠 |
|------|------|------|
| エージェント出力の取得 | ✅ 容易 | Task/Teams とも構造化されたテキストで返る |
| エージェント名の特定 | ✅ 確実 | Task: subagent_type / Teams: teammate_id / ログ: 参加者セクション |
| キャラ口調への変換 | ✅ 先行事例で実証済み | LIGS論文: Prompt Engineering + Few-shot で十分 |
| 事実の維持 | ⚠️ 要ガードレール | 変換ルールでハルシネーション防止が必要 |
| 参加エージェントの判定 | ✅ 容易 | ログに明示的に記載されている |

### 入力データの品質: ✅ 十分

- セッションログは **何を誰がやったか** が明確に記録されている
- 成果物の具体的内容（ファイルパス、キャッチコピー、数値等）も含まれている
- 議論メモや株主とのやり取りも記録されている

### リスク

| リスク | 深刻度 | 対策 |
|--------|--------|------|
| キャラが事実にない発言をする | High | 変換ルールで「ログにない出来事を語るな」を明示。入力テキストを引用形式で渡す |
| 関与していないキャラが登場する | Medium | 入力に参加エージェント一覧を明示し、「この一覧にないキャラは登場させるな」と指示 |
| 口調が混ざる | Low | Few-shot例文を充実させる。narrator.md に既に各キャラ3例文あり |

---

## 5. 設計

### 5.1 narrator の入力フォーマット（CEOが渡す）

```markdown
## 変換指示

### 参加エージェント（このキャラのみ登場させること）
- analyst
- writer
- site-builder

### セッション概要
（1-3行の要約）

### エージェント別の実績
#### analyst
（task-notification の <result> 部分、または teammate-message の本文をそのまま貼る）

#### writer
（同上）

#### site-builder
（同上）

### CEO判断・コメント（零として語らせる）
（CEOの発言・判断をそのまま貼る）
```

### 5.2 narrator の処理フロー

```
1. 入力を受け取る
2. 参加エージェント一覧を確認
3. 各エージェントの実績テキストを読む
4. 対応するキャラクターの口調で「そのエージェントが実際にやったこと」を語らせる
5. CEO（零）が最後にまとめる（CEOも参加した場合のみ）
6. 参加していないエージェントは登場させない
```

### 5.3 変換ルール（narrator.md に追加）

```markdown
## Pattern A 変換ルール

### 絶対ルール
1. **参加エージェント一覧に含まれるキャラのみ登場させる**
2. **各キャラの発言は、対応するエージェントの実績テキストに基づく内容のみ**
3. **実績テキストにない数字・事実・成果物を捏造しない**
4. **キャラの「視点」は加えてよいが、「事実」は加えない**
   - ✅ OK: 凛「あら、競合がこの価格帯に来ましたのね」（analystが実際に競合調査した場合）
   - ❌ NG: 凛「わたくし、法的リスクも確認いたしましたわ」（analystは法務をやっていない）

### 許可される表現
- キャラ同士の相槌・リアクション（事実に反しない範囲）
- キャラの性格に基づく感想・評価（「悪くない」「これバズる」等）
- 関係性に基づくやり取り（凛と翔のバトル等）— ただし事実の範囲内

### 禁止される表現
- ログに記載のないエージェントのキャラを登場させること
- エージェントが行っていない作業をキャラに語らせること
- 実績テキストにない数値・ファイル名・機能名を出すこと
```

### 5.4 入力の生成方法（CEO側の手順）

#### Task方式のセッション
```
1. session-log スキルでセッションログを生成（content/logs/YYYY-MM-DD.md）
2. ログから参加エージェントと各エージェントの成果を抽出
3. 上記入力フォーマットに整形
4. narrator を Task で呼び出し
```

#### Teams方式のセッション
```
1. teammate-message の本文をそのまま各エージェントの実績として使用
2. 参加エージェント一覧は TeamCreate 時のメンバーから取得
3. 上記入力フォーマットに整形
4. narrator を Task で呼び出し
```

#### 手動（既存セッションログから）
```
1. content/logs/YYYY-MM-DD.md を読む
2. 参加者セクションからエージェント一覧を抽出
3. 各エージェントの成果を実施内容テーブルから抽出
4. 入力フォーマットに整形して narrator に渡す
```

### 5.5 出力の保存先

| 出力 | 保存先 |
|------|--------|
| 会話劇版セッションログ | `content/logs/YYYY-MM-DD-drama.md` |
| キャラ視点ブログ記事 | `content/blog/YYYY-MM-DD-slug.md`（writerと連携） |
| キャラ口調X投稿案 | `content/tweets/YYYY-MM-DD-character.md` |
| YouTube台本のキャラ版 | `content/videos/scripts/YYYY-MM-DD-title.md` |

---

## 6. 実装計画

### 変更ファイル

| # | ファイル | 変更内容 |
|---|---------|---------|
| 1 | `.claude/agents/narrator.md` | Pattern A 変換ルールを追加（Section 5.3 の内容） |
| 2 | `.claude/agents/narrator.md` | 入力フォーマットの仕様を追加（Section 5.1 の内容） |
| 3 | `.claude/commands/session-log.md` | Step 6 の narrator 呼び出し手順を Pattern A に合わせて更新 |

### 変更しないもの
- narrator.md のキャラクター定義（8キャラ分のプロフィール・例文）→ そのまま
- narrator.md の起動ルーティン → そのまま
- narrator.md の部門間連携・エスカレーション → そのまま
- 他のエージェント定義 → 変更不要
- テスト → narrator.md の構造は変わらないため既存テスト全通しのまま

### 実装手順
```
1. narrator.md に Pattern A 変換ルールを追加
2. narrator.md に入力フォーマット仕様を追加
3. session-log.md の Step 6 を更新
4. pytest 全通し確認
5. 実セッションログ（2026-02-15-session3.md）を使って narrator テスト実行
6. 出力が Pattern A を満たしているか検証
```

---

## 7. テスト計画

### テスト1: 実データによる変換テスト
- **入力**: `content/logs/2026-02-15-session3.md`（4エージェント参加）
- **期待**: analyst, product-manager, video-creator, writer, CEO の5キャラのみ登場
- **検証**: site-builder, x-manager, legal, video-creator 以外のキャラが語っていないこと

### テスト2: 事実の正確性テスト
- **入力**: 同上
- **検証**: 各キャラの発言が、対応するエージェントの実績と矛盾しないこと
  - 凛（analyst）: 「KPI目標値」「3シナリオ×3フェーズ」に言及 → ✅
  - 凛（analyst）: 「LP文面」に言及 → ❌（writerの仕事）

### テスト3: 非参加キャラの排除テスト
- **入力**: analyst のみ参加のセッション
- **期待**: 凛（analyst）と零（CEO）のみ登場
- **検証**: 他の6キャラが一切登場しないこと

---

## 8. 結論

Pattern A は**技術的に実現可能**。理由:

1. **入力データが構造化されている**: Task/Teams/セッションログ、いずれの方式でもエージェント名と出力テキストが明確に分離されている
2. **先行事例で方式が実証済み**: StoryBox, LIGS が同じ「構造化ログ → キャラ口調変換」パイプラインを採用し成功
3. **キャラプロフィールが既に充実**: narrator.md に8キャラ分の口調・例文・関係性が定義済み
4. **Prompt Engineering で十分**: ファインチューニング不要。変換ルール + Few-shot で精度確保可能

**次のアクション**: 株主承認後、上記実装計画に従って narrator.md を更新し、実データテストを実行する。
