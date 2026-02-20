---
name: kpi-update
description: KPIと収支を更新する。status.mdを最新の実績値に更新する。
---

# KPI・収支更新

## 引数
- $ARGUMENTS: なし（常にフル更新）

## 手順

### 1. 現在値の確認（自動）

```python
python3 -c "
import sys; sys.path.insert(0, '.')
from tools.core.status_parser import StatusParser
import json

sp = StatusParser()
print('=== KPI ===')
print(json.dumps(sp.get_kpi(), ensure_ascii=False))
print('=== FINANCE ===')
print(json.dumps(sp.get_finance(), ensure_ascii=False))
print('=== FIXED COSTS ===')
print(json.dumps(sp.get_fixed_costs(), ensure_ascii=False))
"
```

### 2. トークン消費取得（自動）

```python
python3 tools/core/ccusage.py --json
```

結果をstatus.mdのトークン消費テーブルに反映:

```python
python3 -c "
import sys, json; sys.path.insert(0, '.')
from tools.core.status_parser import StatusParser
from tools.core.ccusage import run_daily, totals

rows = run_daily()
sp = StatusParser()
sp.update_token_table(rows)
t = totals(rows)
print(f'Updated: {t[\"total_tokens_m\"]}M tokens, \${t[\"total_cost_usd\"]}')
"
```

### 3. 株主に確認

以下は自動取得できないため、株主に確認:
- 売上の変化はあるか（新規収入等）
- 新しい支出はあるか
- Xフォロワー数（手動確認が必要な場合）
- プラン使用率（%）

### 4. status.md更新

確認結果に基づき `docs/status.md` を更新:
- KPIセクション（実績テーブル）を更新
- 収支セクション（月次収支テーブル）を更新
- トークン消費記録を更新（Step 2で自動反映済み）

### 5. 報告

```
**KPI更新完了**
- 売上: ¥X → ¥Y
- ユーザー: X → Y
- 支出: ¥X → ¥Y
- 収支: ¥X
- トークン使用率: X%
```

## 注意
- 推定値を入れない。確認できた実績値のみ更新する
- 変化がない項目は触らない
- 数値の出所を明確にする（「株主確認」「システム通知」等）
