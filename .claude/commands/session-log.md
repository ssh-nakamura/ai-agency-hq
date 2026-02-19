---
name: session-log
description: セッション終了時にログ保存 + HTML報告書を生成する。株主がブラウザで確認できる形式。
---

# セッション終了ルーティン

セッション終了時に以下を順番に実行する。

## 1. 内部ログの作成

`content/logs/YYYY-MM-DD.md` にセッション記録を作成する。

### 命名規則
- 1日1セッション: `YYYY-MM-DD.md`
- 同日2回目以降: `YYYY-MM-DD-s2.md`, `YYYY-MM-DD-s3.md`
- **既存ファイルを確認してから採番する**（`ls content/logs/`）

### テンプレート

```markdown
# セッションログ - YYYY-MM-DD

## 参加者
- CEO
- （呼んだエージェント一覧）

## 実施内容
-

## 決定事項
-

## 成果物一覧
| ファイル | 内容 | 担当 |
|---------|------|------|

## 株主確認事項
-

## 次回やること
-
```

## 2. HTML報告書の自動生成

```bash
python3 tools/session-report.py content/logs/YYYY-MM-DD.md --open
```

`reports/session-YYYY-MM-DD.html` が自動生成され、ブラウザで開かれる。

## 3. レポートダッシュボード更新

```bash
python3 tools/generate-reports-index.py
```

## 4. CEOメモリの更新

`.claude/agent-memory/ceo/MEMORY.md` を更新:
- 新しい確定事項があれば追記
- 失敗と学びがあれば追記

## 5. ドキュメント最新化

- `docs/status.md` — 完了タスクを移動、新規タスクを追加、KPIや収支に変更があれば更新

## 6. トークン消費記録（ccusage使用）

```bash
npx ccusage@latest daily --since YYYYMMDD
```

取得した数値を `docs/status.md` のトークン消費セクションに記録。

## 7. 会話劇ログ生成（オプション）

セッション中にキャラ視点のコンテンツが必要な場合、narrator を呼んで業務ログを会話劇に変換する。
- 入力: `content/logs/YYYY-MM-DD.md`（Step 1で作成した内部ログ）
- 出力: `content/logs/YYYY-MM-DD-drama.md`（会話劇版）
- 不要なセッションではスキップしてよい

## 注意
- **Stopフックがログの存在を検証する**。ログ未保存ではセッション終了がブロックされる
- 全ステップ完了してからセッションを終了する
- HTML報告書が最優先。株主が見るのはこれだけ
- 内部ログは簡潔でいい（CEOの次回参照用）
