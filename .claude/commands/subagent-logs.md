サブエージェントの会話ログをHTMLに変換して表示する。

## 手順

1. `tools/subagent-log-viewer.py` を実行してHTMLを生成する:

```bash
python3 tools/subagent-log-viewer.py
```

オプション: 特定のセッションだけ生成する場合はセッションIDを引数に渡す:
```bash
python3 tools/subagent-log-viewer.py 617c131a-a4c3-48c4-9fc8-52135bdd7987
```

2. 生成されたHTMLをブラウザで開く:

```bash
open reports/subagent-logs.html
```

3. reports/subagent-logs.html をgitにコミットする（ログの永続化）

## 注意
- Claude Codeのセッションログは30日で自動削除される（`cleanupPeriodDays`設定）
- HTMLをgit管理しておけば、元のJSONLが消えてもログは残る
- セッション終了時に `/session-log` と一緒に実行すること推奨
