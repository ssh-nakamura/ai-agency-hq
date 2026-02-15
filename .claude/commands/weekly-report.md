---
name: weekly-report
description: 週次レポートを生成する。docs/state.json、docs/actions.md、docs/finances.md、content/logs/のセッションログを元に、CLAUDE.mdの週次レポートフォーマットに従って作成する。
---

# 週次レポート生成

## 手順

1. 以下を読み込む（並列で）:
   - `docs/state.json` — 現在のKPI
   - `docs/actions.md` — 今週のアクション進捗
   - `docs/finances.md` — 収支状況
   - `content/logs/` — 今週のセッションログ（直近7日分）

2. CLAUDE.mdの週次レポートフォーマットに従い、レポートを作成する

3. `reports/weekly-YYYY-WXX.md` に保存する（例: reports/weekly-2026-W07.md）

4. state.jsonのweeklyReportCountをインクリメントする

## フォーマット（CLAUDE.mdより）

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
- 数字は全てstate.jsonとfinances.mdの実績値を使う。推定値を混ぜない
- 成果は完了済みアクションから抽出する
- 相談事項はactions.mdの「株主承認待ち」から抽出する
