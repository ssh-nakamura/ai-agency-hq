# アクション管理

> 今やるべき具体的なタスク。ロードマップ（roadmap.md）の現在のStepから生成される。
> CEOが更新・管理する。完了したらロードマップの進捗も更新すること。

---

## 現在のフェーズ: Phase 0 - Step 1→2 移行中

---

## 今週のアクション

### 最優先

| ID | アクション | 担当エージェント | 状態 | 備考 |
|----|-----------|----------------|------|------|
| A-016 | エージェント定義の更新（スキル参照・自走力強化） | CEO | 未着手 | 全エージェントの.mdにスキル一覧・横連携ルール・自走ガイドを追加 |
| A-017 | Claude-Memプラグインの導入 | CEO | 未着手 | `/plugin marketplace add thedotmack/claude-mem` |
| A-018 | claude-office-skills導入 + プレゼンデザインルール策定 | CEO + site-builder | 未着手 | pptxgenjs/LibreOffice依存。design-rules-pptx.md作成 |
| A-012 | ShieldMe価格プランの再検証（API単価実測含む） | product-manager + analyst | 未着手 | Phase 1開始前に100件実測 |

### 次に着手

| ID | アクション | 担当エージェント | 状態 | 前提条件 |
|----|-----------|----------------|------|---------|
| A-019 | 海外コンテンツローカライズ戦略の策定 | writer + video-creator | 未着手 | 海外トレンドリサーチの工程を企画パイプラインに組み込む |
| A-020 | 英語版コンテンツ展開の設計 | writer + site-builder | 未着手 | サイト多言語化、ブログ・YouTube英語版の運用フロー |
| A-008 | X初投稿案の作成 | x-manager | 未着手 | LP完成後（A-007完了済み） |
| A-009 | 利用規約・プライバシーポリシー草案 | legal | 未着手 | ShieldMeのAIカウンセリング機能の法的リスクも確認 |
| A-013 | ブログ初回記事の執筆（日英両方） | writer | 未着手 | LP公開後に着手 |

### 保留（Phase 1以降）

| ID | アクション | 担当エージェント | 備考 |
|----|-----------|----------------|------|
| A-014 | ShieldMe MVP開発（別リポジトリ） | 開発チーム | X API契約（株主承認）後 |
| A-015 | YouTubeチャンネル開設・初動画制作 | video-creator | ツール契約（株主承認）後 |

### 株主承認待ち

| ID | 承認事項 | 金額 | 備考 |
|----|---------|------|------|
| S-001 | X API Basic契約 | $100/月（≒¥15,000） | ShieldMe MVP開発に必須 |
| S-002 | 動画制作ツール契約 | ¥3,000〜12,000/月 | 最小 or 推奨構成を選択 |
| S-003 | ドメイン取得（ai-agency.jp） | 年間¥1,500〜3,000 | サイト公開に必要 |

---

## 完了済み

| ID | アクション | 担当 | 完了日 | 成果物 |
|----|-----------|------|--------|--------|
| A-021 | スキル作成（startup, weekly-report, shareholder-report, session-log, kpi-update） | CEO | 2026-02-15 | .claude/commands/*.md |
| A-007 | LP制作（HTML実装） | site-builder | 2026-02-15 | site/index.html |
| A-004 | KPI目標値の提案 | analyst | 2026-02-15 | docs/specs/kpi-proposal.md |
| A-005 | ShieldMe MVP仕様書の作成 | product-manager | 2026-02-15 | docs/specs/shieldme-mvp-spec.md |
| A-006 | LP文面のドラフト | writer | 2026-02-15 | content/copy/lp-draft-v1.md |
| A-011 | YouTube動画パイプラインの調査・設計 | video-creator | 2026-02-15 | docs/specs/video-pipeline-design.md |
| A-010 | エージェント設計をAgent Teams方式に改修 | CEO | 2026-02-15 | CLAUDE.md, .claude/agents/*.md |
| A-001 | 誹謗中傷対策SaaS市場の競合調査 | CEO（代行） | 2026-02-14 | docs/specs/market-research-competitors.md |
| A-002 | コンテンツ事業の収益モデル調査 | CEO（代行） | 2026-02-14 | docs/specs/market-research-content.md |
| A-003 | 月次コスト見積もり（API・インフラ） | CEO（代行） | 2026-02-14 | docs/specs/cost-estimate.md |

---

## 更新ルール

### 誰が更新するか
- **CEOのみ**がこのファイルを更新する
- 他のエージェントはCEOに報告し、CEOが反映する

### アクションの追加
```markdown
| A-XXX | アクションの内容 | 担当エージェント | 未着手 | 備考や前提条件 |
```
- IDは `A-` + 3桁の連番（A-001, A-002...）
- 新しいStepに入ったらIDはリセットしない（通し番号）

### 状態の更新
- `未着手` → `進行中` → `完了`
- 完了したら「完了済み」テーブルに移動し、完了日と成果物パスを記入

### 上限とアーカイブ
- **「完了済み」は直近10件だけ残す**
- 10件を超えたら古いものから `docs/archive/actions-YYYY.md` に移動する
- 「今週のアクション」は最大15件。超える場合は「保留」に回す

### フォーマットを崩さない
- テーブルのカラムを変えない
- セクション構成（最優先 / 次に着手 / 保留 / 完了済み）を変えない
