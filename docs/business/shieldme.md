# ShieldMe ステータス

> 更新者: analyst（数値）、product-manager（進捗）
> 最終更新: 2026-02-19

---

## 概要（1行）

SNS・Webメディアの誹謗中傷をAIがリアルタイム検知・通知するSaaS。

---

## KPI

| 指標 | 現在値 | Phase 2目標（標準シナリオ） |
|------|--------|--------------------------|
| MRR | ¥0 | ¥225,000 |
| 有料ユーザー数 | 0 | 150人 |
| ARPU | - | ¥1,500/月 |
| 損益分岐ユーザー数 | - | 17人 |
| チャーンレート | - | 5%以下（目標） |

出典: docs/specs/kpi-proposal.md

---

## 進捗

### 国内

- MVP仕様書: 確定済み（docs/specs/shieldme-mvp-spec.md）
- 価格プラン: 検討中（A-012: 競合PostGuardの月額¥500登場により再検証必須）
- 開発: 未着手（Phase 1開始・X API契約後に着手予定）
- ベータテスター: 未募集
- 競合動向: PKSHA Post Guard（月額¥500プランを2026-02-19確認）、Mimamorn、matte等

### 海外（グローバル展開）

- 現状: 戦略未策定
- 主要海外競合: Brandwatch、Mention、Brand24（価格帯・機能の詳細調査が必要）
- 課題: 日本語特化の誹謗中傷検知モデルを海外展開するには多言語対応が必須
- アクション: 海外競合調査後、グローバル展開可否をCEOに提言（要調査）

---

## 課題

| 優先度 | 課題 | 担当 | 備考 |
|--------|------|------|------|
| 高 | API単価の実測（100件テスト） | product-manager + analyst | Phase 1開始前に必須 |
| 高 | PostGuard月額¥500への価格戦略対応 | analyst + product-manager | 差別化軸の再定義 |
| 中 | X API Basic契約（株主承認待ち） | CEO | $100/月、S-001 |
| 中 | ベータテスター5名確保 | x-manager + writer | Phase 1タスク |

---

## 次のアクション

1. **A-012**: ShieldMe価格プランの再検証（API単価実測含む）- product-manager + analyst
2. **S-001**: X API Basic契約の株主承認取得 - CEO
3. Phase 1開始後にMVP開発着手（別リポジトリ）
