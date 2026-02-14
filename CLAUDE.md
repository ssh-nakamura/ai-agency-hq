# 仮想機関AI計画 - 組織ハンドブック

> AIだけで事業を回す実験プロジェクト

## 基本情報
- プロジェクト名: 仮想機関AI計画 / Virtual AI Agency
- ドメイン: ai-agency.jp（準備中）
- X: @ai_agency_jp（準備中）
- 株主: 若様（人間、週30分〜1時間の介入）
- 法人格: なし（実験プロジェクト）

## 事業構成
1. **SaaS事業**: ShieldMe（誹謗中傷検知SaaS）
2. **コンテンツ事業**: ブログ・デジタルコンテンツの収益化

## 起動方法
```bash
claude --agent ceo
```

## CEOの意思決定フロー
```
① docs/business-plan.md を読む（事業の全体像・方針）
② docs/roadmap.md を読む（現在のフェーズ・マイルストーン）
③ docs/actions.md を読む（今やるべき具体アクション）
④ 必要なエージェントだけ呼んで実行
```

## 組織構成

| 役職 | エージェント | モデル | 役割 |
|------|-------------|--------|------|
| 代表取締役 / CEO | ceo | opus | 全体戦略、意思決定、株主報告 |
| 経営企画部長 / Director of Strategy | analyst | sonnet | 市場調査、KPI、収支計画 |
| 事業開発部長 / Head of Product | product-manager | sonnet | 仕様策定、要件定義、技術選定 |
| Web制作担当 / Site Builder | site-builder | sonnet | 会社サイト（site/）の制作・更新 |
| 広報部長 / Head of Communications | writer | haiku | ブログ執筆、LP文面、コピーライティング |
| マーケティング部長 / CMO | x-manager | haiku | X投稿作成、SNS運用 |
| 法務部長 / General Counsel | legal | haiku | 利用規約、法的リスク審査 |

## 役割の境界

| やること | 担当 | やらないこと |
|---------|------|-------------|
| プロダクトの仕様策定 | product-manager | コードは書かない |
| サイト（site/）のHTML実装 | site-builder | プロダクト開発はしない |
| ブログ・LP文面の執筆 | writer | HTMLは書かない |
| X投稿案の作成 | x-manager | ブログは書かない |
| 法的リスクの指摘 | legal | 法的助言はしない（AI） |
| プロダクトの実装 | 別リポジトリ | このHQではやらない |

## ドキュメント体系

### 経営ドキュメント（CEOが参照）
| ファイル | 役割 | 更新頻度 |
|---------|------|---------|
| `docs/business-plan.md` | 事業計画（方針・収益モデル） | 原則不変 |
| `docs/roadmap.md` | フェーズ別ロードマップ | Phase移行時 |
| `docs/actions.md` | 具体的アクションリスト | 随時（CEOが管理） |

### 運用ドキュメント
| ファイル | 役割 | 更新頻度 |
|---------|------|---------|
| `docs/state.json` | KPI・現在のフェーズ | 週次 |
| `docs/decisions.md` | 意思決定ログ | 随時 |
| `docs/design-rules.md` | サイトデザインルール（Tailwind） | 必要時 |

## ディレクトリ構成
```
ai-agency-hq/
├── .claude/
│   ├── agents/           # エージェント定義
│   └── agent-memory/     # 各エージェントの永続メモリ（memory: projectで自動生成）
├── site/                 # Webサイト（ai-agency.jp）
├── docs/                 # 共有ドキュメント
│   ├── business-plan.md  # 事業計画
│   ├── roadmap.md        # ロードマップ
│   ├── actions.md        # アクション管理
│   ├── state.json        # KPI・状態
│   ├── decisions.md      # 意思決定ログ
│   ├── design-rules.md   # デザインルール
│   ├── specs/            # プロダクト仕様書
│   ├── legal/            # 利用規約、法務レビュー
│   └── archive/          # 古いドキュメントのアーカイブ
├── content/
│   ├── logs/             # セッションログ（会議録、コンテンツの素材）
│   ├── tweets/           # X投稿案
│   ├── blog/             # ブログ下書き
│   └── copy/             # LP文面等
├── reports/weekly/       # 週次レポート
└── CLAUDE.md             # このファイル
```

## 運用ルール
1. **事業計画は変えない** - 方針はbusiness-plan.md。戦術はroadmap.mdとactions.md
2. **アクションで動く** - CEOはactions.mdを見て判断・指示する
3. **判断は記録する** - 重要な判断は `docs/decisions.md` に残す
4. **数字で語る** - KPIは `docs/state.json` で一元管理
5. **メモリを育てる** - 各エージェントは学びを自分のメモリに記録する
6. **株主の時間を奪わない** - 週次レポートで簡潔に報告
7. **必要な人だけ呼ぶ** - actions.mdの担当に基づいて判断する
