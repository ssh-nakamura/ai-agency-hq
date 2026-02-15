---
name: kpi-update
description: KPIと収支を更新する。state.jsonとfinances.mdを最新の実績値に更新する。
---

# KPI・収支更新

## 手順

1. 現在の値を読み込む（並列で）:
   - `docs/state.json`
   - `docs/finances.md`

2. 株主に以下を確認する:
   - 売上の変化はあるか（新規収入等）
   - 新しい支出はあるか
   - Xフォロワー数（手動確認が必要な場合）
   - プラン使用率（%）

3. ccusageでトークン消費量を取得:
   ```bash
   npx ccusage@latest daily --since YYYYMMDD
   npx ccusage@latest monthly
   ```

4. 確認結果に基づき更新:
   - `docs/state.json` のkpi.actual を更新
   - `docs/finances.md` の月次収支を更新
   - finances.mdのトークン消費記録をccusageの実データで更新

4. 更新後のサマリーを報告:

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
