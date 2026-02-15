---
name: shareholder-report
description: 株主報告資料を生成する。週次レポートよりも詳細な資料。株主から依頼があったときに使う。
---

# 株主報告資料生成

## 手順

1. 以下を読み込む（並列で）:
   - `docs/state.json`
   - `docs/actions.md`
   - `docs/finances.md`
   - `docs/roadmap.md`
   - `content/logs/` — 直近のセッションログ
   - 直近の `reports/weekly-*.md`

2. `reports/` ディレクトリにHTML形式で資料を作成する
   - ファイル名: `reports/YYYY-MM-DD-shareholder-report.html`
   - Tailwind CSS v4（CDN）でスタイリング
   - ダークテーマ（サイトと同じデザインシステム）
   - ブラウザで開いて見れる形式

3. 構成:
   - サマリー（3行で全体像）
   - KPI（state.jsonから。目標値との対比）
   - 今期の成果（完了アクション一覧）
   - 収支（finances.mdから）
   - 進捗（roadmap.mdの現在地と完了率）
   - 課題とリスク
   - 次のアクション計画
   - 株主への相談事項（承認待ちリスト）

## 注意
- 数字は実績ベース。推定値には「推定」と明記する
- 株主の時間を奪わない。簡潔に
- 相談事項は判断しやすいように選択肢とコストを明記する
