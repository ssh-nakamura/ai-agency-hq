---
name: weekly-report
description: 週次レポートを生成する。docs/status.mdとdocs/plan.md、セッションログを元に作成する。
---

# 週次レポート生成

## 手順

1. 以下を読み込む（並列で）:
   - `docs/status.md` — KPI・アクション進捗・収支
   - `docs/plan.md` — 事業計画・ロードマップ
   - `content/logs/` — 今週のセッションログ（直近7日分）

2. ceo-manual.mdの週次レポートフォーマットに従い、レポートを作成する

3. `reports/weekly-YYYY-WXX.md` に保存する（例: reports/weekly-2026-W07.md）

## フォーマット（ceo-manual.mdより）

```markdown
# 仮想機関AI計画 週次報告 - Week N

## サマリー（3行で）

## 数字
- 売上: ¥XXX
- ユーザー数: XX
- Xフォロワー: XX
- 今月の支出: ¥XXX
- 累計投資額: ¥XXX

## 今週の成果
-

## 課題と対策
| 課題 | 対策 | 担当 | 期限 |

## 来週の優先タスク
1.
2.
3.

## 株主への相談事項
-
```

## 注意
- 数字は全てstatus.mdの実績値を使う。推定値を混ぜない
- 成果は完了済みアクションから抽出する
- 相談事項はstatus.mdの「株主承認待ち」から抽出する
