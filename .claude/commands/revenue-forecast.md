---
name: revenue-forecast
description: 収支シミュレーション・シナリオ分析。analystを呼び出して数字を回す。
---

# 収支予測

## 引数
- $ARGUMENTS: 対象と期間（例: "ShieldMe 6ヶ月", "全事業 年間"）
  - 引数なし → CEOが対象を決めてから開始

## ワークフロー

### Step 1: 前提条件の確認（CEO）
- 対象事業（ShieldMe / コンテンツ / 動画 / Type B / 全体）
- 予測期間（3ヶ月 / 6ヶ月 / 12ヶ月）
- 現在の収支（`docs/status.md` から取得）
- 前提となるアクション（LP公開、X開設等のタイミング）

### Step 2: シミュレーション（analyst）
analystをTask起動:

```
対象: {事業}
期間: {N}ヶ月
現在の状態:
  - 売上: {status.mdから}
  - 月間コスト: {status.mdから}
  - ユーザー数: {status.mdから}

以下の3シナリオで月次P/Lを作れ:
1. 保守シナリオ（想定の50%の成長）
2. 標準シナリオ（計画通り）
3. 楽観シナリオ（想定の150%の成長）

各シナリオに:
- 月次の売上・支出・利益テーブル
- 損益分岐点の到達時期
- キャッシュフロー推移
- 主要な前提条件と感度分析

python3 tools/core/status_parser.py でstatus.mdの現在値を取得してから計算せよ。
成果物: docs/specs/{slug}-forecast.md
```

### Step 3: レビュー（CEO）
- 前提条件は妥当か
- 楽観シナリオに依存していないか
- 株主に見せて判断を仰ぐ必要があるか

## 出力
成果物: `docs/specs/{slug}-forecast.md`

## 注意
- 推定値を確定値のように書かない
- 前提条件を必ず明記（「X API契約後」「LP公開後」等）
