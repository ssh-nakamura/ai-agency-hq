---
name: shareholder-report
description: 株主報告資料を生成する。週次レポートよりも詳細な資料。株主から依頼があったときに使う。
---

# 株主報告資料生成

## 引数
- $ARGUMENTS: 期間（例: "2月前半", "W08"）
  - 引数なし → 直近1週間

## 手順

### 1. データ収集（自動・並列で）

```python
python3 -c "
import sys; sys.path.insert(0, '.')
from tools.core.status_parser import StatusParser
from tools.core.log_parser import collect_week_logs, summarize_logs
from tools.core.ccusage import run_daily, totals
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
print('=== PHASE ===')
print(sp.get_phase())
"
```

以下も読み込む:
- `docs/plan.md` — 事業計画・ロードマップ（進捗・完了率の算出用）
- `content/logs/` — 対象期間のセッションログ
- 直近の `reports/weekly-*.md`（あれば）

### 2. HTML資料作成

`reports/YYYY-MM-DD-shareholder-report.html` に作成:
- Tailwind CSS v4（CDN）でスタイリング
- ダークテーマ（サイトと同じデザインシステム）
- ブラウザで開いて見れる形式

### 3. 構成

- サマリー（3行で全体像）
- KPI（status.mdの実績テーブル。目標値との対比）
- 今期の成果（完了アクション一覧 + ログから抽出した成果物）
- 収支（status.mdの月次収支テーブル）
- 進捗（plan.mdのロードマップ現在地と完了率）
- 課題とリスク
- 次のアクション計画
- 株主への相談事項（承認待ちリスト）

## 出力
成果物: `reports/YYYY-MM-DD-shareholder-report.html`

## 注意
- 数字は実績ベース。推定値には「推定」と明記する
- 株主の時間を奪わない。簡潔に
- 相談事項は判断しやすいように選択肢とコストを明記する
