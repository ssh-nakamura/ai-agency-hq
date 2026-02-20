---
name: weekly-report
description: 週次レポートを生成する。docs/status.mdとdocs/plan.md、セッションログを元に作成する。
---

# 週次レポート生成

## 引数
- $ARGUMENTS: 週番号（例: "W08"）
  - 引数なし → 今週

## 手順

### 1. データ収集（自動）

```python
python3 -c "
import sys; sys.path.insert(0, '.')
from tools.core.status_parser import StatusParser
from tools.core.log_parser import collect_week_logs, summarize_logs
import json

sp = StatusParser()
print('=== KPI ===')
print(json.dumps(sp.get_kpi(), ensure_ascii=False))
print('=== FINANCE ===')
print(json.dumps(sp.get_finance(), ensure_ascii=False))
print('=== ACTIONS ===')
print(json.dumps(sp.get_actions_by_section(), ensure_ascii=False))
print('=== PENDING ===')
print(json.dumps(sp.get_pending_approvals(), ensure_ascii=False))

logs = collect_week_logs()
summary = summarize_logs(logs) if logs else {}
print('=== LOG SUMMARY ===')
print(json.dumps(summary, ensure_ascii=False, default=str))
"
```

以下も読み込む:
- `docs/plan.md` — 事業計画・ロードマップ

### 2. レポート作成

`reports/weekly-YYYY-WXX.md` に保存（例: reports/weekly-2026-W08.md）

### フォーマット

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
- 成果は完了済みアクション + セッションログの実施内容から抽出する
- 相談事項はstatus.mdの「株主承認待ち」から抽出する
