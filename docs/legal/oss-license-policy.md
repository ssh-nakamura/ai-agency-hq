# OSS ライセンス管理方針

> ⚠️ この文書はAIが作成したリスク分析です。
> 法的助言ではありません。最終判断は弁護士等の専門家にご相談ください。

**作成日:** 2026-02-15
**作成者:** legal（法務部長）
**ステータス:** 草案 - 株主確認待ち

---

## 概要

本プロジェクト（仮想機関AI計画）で利用するOSSツールのライセンス管理方針を定める。
目的: 法的リスクを最小化しながら、OSSの効果的な活用を実現する。

---

## 現状確認

### 利用中・導入予定のOSSツール

| ツール | 用途 | ライセンス | 商用利用 | 帰属表示義務 | リスク度 |
|--------|------|-----------|---------|-----------|---------|
| **ccusage** | トークン使用量分析 | **要確認** | - | - | Medium |
| **ccboard** | 使用量ダッシュボード | MIT OR Apache-2.0 | OK | あり | Low |
| **clog** | 会話ログビューア | MIT | OK | あり | Low |
| **Tailwind CSS v4** | Webスタイリング | MIT | OK | あり | Low |
| **npx各種** | CLIツール実行 | 混在（要把握） | - | - | Low-Medium |

---

## 法的リスク分析

### 1. MIT ライセンス（ccboard, clog, Tailwind CSS）

**リスク評価:** **Low**

**ポイント:**
- 商用利用: **OK**
- 再配布: **OK**
- 改変: **OK**
- 条件: **帰属表示（著作権表示）が必須**
- 保証: なし（免責条項あり）

**われわれへの影響:**
- ShieldMe（有料SaaS）や動画事業での利用は問題なし
- ブログ・サイトに帰属表示が必須（後述）
- 訴訟リスク: 帰属表示を行えば極めて低い

**対応:**
- サイト・報告資料内に帰属表示を記載
- `docs/legal/oss-credits.md` で一元管理

---

### 2. Apache 2.0 ライセンス（ccboardの選択肢）

**リスク評価:** **Low**

**ポイント:**
- 商用利用: **OK**
- 再配布: **OK**
- 改変: **OK**
- 条件: **帰属表示 + ライセンステキストの提供が必須**
- 専利権条項: あり（安全装置として機能）

**われわれへの影響:**
- MIT同様、商用利用は問題なし
- Apache 2.0はMITより「厳密」だが、条件は明確で遵守しやすい

**対応:**
- MIT同様、帰属表示 + ライセンステキストを明記

---

### 3. ccusage（GitHub: ryoppippi/ccusage）

**リスク評価:** **Medium** - 情報が不足しているため

**確認すべき項目:**
```
[ ] GitHubでライセンスファイル（LICENSE）の存在確認
[ ] SPDX表記の確認
[ ] GPL系でないことの確認
```

**対応:**
→ product-manager が GitHub確認後、ライセンス情報を `docs/legal/oss-credentials.md` に記録
→ GPL系以外なら Low に格下げ

**チェック手順:**
```bash
# GitHubで確認（Web UI）
https://github.com/ryoppippi/ccusage/blob/main/LICENSE

# あるいはリポジトリ詳細から "About" → "License"
```

---

### 4. npx経由のツール類

**リスク評価:** **Low-Medium** - npm依存チェーン経由のリスク

**リスク要因:**
- 直接利用ツール自体は一般的にライセンス情報を保有
- **問題: 依存パッケージ経由でGPL系が混入する可能性**
  - 例: npm モジュールが（知らず知らずのうちに）GPL依存を持つことがある
  - これが発見されると、われわれも遡及的にGPL準拠を求められるリスク

**対応:**
```bash
# 定期的にライセンス監査を実行
npm audit --license

# または専用ツール
npm install -g license-checker
license-checker --json > docs/legal/npm-licenses.json
```

**確認頻度:** 月1回（新パッケージ導入時は毎回）

---

### 5. GPL系ライセンスが混入した場合

**リスク評価:** **Critical**（ただし可能性は低い）

**GPL（v2/v3）の特徴:**
- 商用利用は可
- 改変は可
- **ただし: 改変・再配布時に、自分たちもGPL準拠が必須（コピーレフト効果）**
  - つまり、ShieldMeのコードもGPL化される必要が生じる
  - これは営利事業に対して重大な支障

**混入経路:**
- npm パッケージの依存チェーン
- 直接利用しなくても、依存パッケージが持つことがある

**対応（予防）:**
- `npm audit --license` で GPL系の有無を定期確認
- GPL系が検出されたら、即座に **法務部長（legal）が CEO に報告**
- 代替パッケージの検討 or GPL準拠の判断を株主に仰ぐ

---

## ライセンス管理の運用フレームワーク

### Phase 0（現在）: 基本記録

**対応者:** legal
**頻度:** 初回 + 新ツール追加時

**実施内容:**
1. 利用中・導入予定の全OSSをリストアップ
2. 各ライセンスを確認
3. `docs/legal/oss-credentials.md` に記録（フォーマット下記）

**保存先:** `/Users/soshunakamura/ai_prodcut/ai-agency-hq/docs/legal/oss-credentials.md`

**フォーマット例:**
```markdown
# OSS ライセンス一覧

| # | ツール名 | 用途 | ライセンス | 帰属表示 | 確認日 | 担当 |
|----|---------|------|-----------|---------|--------|------|
| 1 | ccusage | トークン分析 | MIT | site/about に記載 | 2026-02-15 | legal |
| 2 | ccboard | ダッシュボード | MIT OR Apache-2.0 | site/about に記載 | 2026-02-15 | legal |
| 3 | clog | ログビューア | MIT | site/about に記載 | 2026-02-15 | legal |
```

---

### Phase 1（本番化）: 帰属表示の準備

**対応者:** site-builder（実装） + legal（確認）
**時期:** サイト公開前

**実施内容:**
1. site/about.html（または site/credits.html）に帰属表示を記載
2. ブログ記事で利用ツールを紹介する場合、ライセンスを明記
3. 生成レポートにおいても帰属表示を含める

**帰属表示のテンプレート:**
```html
<section id="oss-credits">
  <h3>利用オープンソースソフトウェア</h3>
  <ul>
    <li>
      <strong>ccboard</strong> - MIT OR Apache-2.0
      <a href="https://github.com/[repository]">GitHub</a>
    </li>
    <li>
      <strong>clog</strong> - MIT
      <a href="https://github.com/[repository]">GitHub</a>
    </li>
    <li>
      <strong>Tailwind CSS</strong> - MIT
      <a href="https://tailwindcss.com/">公式サイト</a>
    </li>
  </ul>
</section>
```

---

### Phase 2（拡張）: ライセンス監査の自動化

**対応者:** product-manager + legal
**時期:** 月1回（CI/CD統合も検討）

**実施内容:**
```bash
# npm audit で定期監査
npm audit --license > docs/legal/npm-licenses-YYYY-MM-DD.json

# 結果をレビュー
legal: GPL系の有無を確認 → CPU に報告
```

**ルール:**
- GPL系が検出 → 即座にCEOに報告（L3エスカレーション）
- 未知のライセンスが出現 → legal が確認してから採用判断

---

## 帰属表示が必須な理由

MIT/Apache 2.0の場合、帰属表示を行わないと：

1. **ライセンス違反** - 契約条項を満たさない
2. **削除要求のリスク** - 著作権者から「表示削除の上で公開停止」を求められる可能性
3. **ブランドリスク** - AI企業として「ライセンスを尊重しない」というレピュテーション毀損

これらは法律相談を求められるレベルではないが、予防することで信用維持につながる。

---

## チェックリスト（実装担当向け）

### 新しいOSSを採用する際

```
[ ] 1. ライセンスを確認（GitHub LICENSE ファイル or package.json）
[ ] 2. 商用利用が許可されていることを確認
[ ] 3. GPL系でないことを確認
[ ] 4. legal に報告し、ocs/legal/oss-credentials.md に記録
[ ] 5. 帰属表示が必須な場合、site に記載予定を確認
[ ] 6. npm audit でリスク検出がないことを確認（npxの場合）
```

### サイト公開前

```
[ ] 1. oss-credentials.md に全OSSが記載されているか確認
[ ] 2. site/credits.html（またはsite/about.html）に帰属表示があるか
[ ] 3. 各ライセンステキストが正確か（word-for-word）
[ ] 4. legal が最終確認
```

### 月次監査（Phase 1以降）

```
[ ] 1. npm audit --license 実行
[ ] 2. 新しいGPL系パッケージがないか確認
[ ] 3. 結果を docs/legal/npm-licenses-YYYY-MM.json に保存
[ ] 4. 問題があれば CEO に報告
```

---

## 推奨事項（ベストプラクティス）

1. **ライセンスポリシーの明文化**
   - 「われわれはGPL系を採用しない」ことを明確に宣言
   - オンボーディング時に全エージェントに周知

2. **定期的なライセンス監査**
   - CI/CD パイプラインに `npm audit --license` を組み込み
   - 月1回、手動で詳細確認

3. **ドキュメント化**
   - 使用技術スタックをドキュメント化（site/tech-stack.html等）
   - マーケティング視点では「透明性」が信用につながる

4. **GPL系発見時の対応フロー**
   - 法務（legal）が即座に CEO に報告
   - CEO が株主に相談 → 代替パッケージ検討 or GPL準拠判断

---

## 結論

**現在の利用予定OSSについてのリスク判定:**

| リスク | 深刻度 | 対応 |
|--------|--------|------|
| MIT/Apache 2.0の商用利用 | **Low** | 帰属表示で対応完了 |
| ccusage のライセンス不明 | **Medium** | GitHub確認後、記録 |
| npm 依存チェーン経由のGPL混入 | **Low** | 月1回のnpm audit |

**実施優先度:**
1. **高** - ccusage のライセンス確認（product-manager）
2. **中** - oss-credentials.md の作成（legal）
3. **中** - npm audit 環境整備（product-manager）
4. **低** - サイト帰属表示の実装（Phase 1）

---

## 関連文書

- `docs/legal/oss-credentials.md` - OSS ライセンス一覧（実装時に作成）
- `docs/legal/` - その他法務関連文書

---

**次のステップ:**
- [ ] 株主が本方針を確認・承認
- [ ] product-manager が ccusage のライセンス確認
- [ ] legal が oss-credentials.md を作成
- [ ] Phase 1 で site に帰属表示を実装
