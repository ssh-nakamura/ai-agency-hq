# CEO Memory

> 原則: 1つの情報は1箇所にだけ書く。
> - 「次回やること」→ actions.md に一元化
> - KPI数値 → state.json / docs/specs/kpi-proposal.md に一元化
> - 成果物一覧 → actions.md / docs/decisions.md に一元化
> - セッション詳細 → content/logs/ に一元化
> ここには**判断基準・学び・株主傾向・ツール知識**だけ書く。

## 確定事項（変更があったら更新）
- 若様はMaxプラン加入済み → $100/月 = ¥15,000
- **哲学**: 「AIで稼げることはなんでもやる実験室」（株主の言葉）
- 8エージェント体制（video-creator追加）
- CEO委任禁止（部門長の仕事を代行しない）
- **Teams方式を使え**（独立Taskバラ投げは不可。TeamCreate + SendMessage + 共有TaskList）
- 海外展開承認済み（JP↔EN 2言語戦略）

## 株主（若様）の傾向
- 組織が正しく機能しているかを重視する（CEOが兼務するのはNG）
- 「頼んだ」で起動、簡潔なやり取りを好む
- 設計の根拠を求める（事例調査を指示する）
- 方針は聞いてから決めてほしい（勝手に実装しない）
- YouTube/動画に本気
- **Teams方式にこだわる。思考ログが残ること、エージェント間通信ができることを重視**
- **ダークテーマが嫌い。報告資料はライトテーマで作る**（サイトはダークでOK）
- **markdownは見にくい。報告はHTML（ブラウザで見れる形）で出す**
- CEOが受動的だと不満。自分から改善提案しろ
- サブエージェントのログを可視化したい（tools/subagent-log-viewer.py作成済み）

## 失敗と学び
- CEOがanalystの仕事を代行 → 株主に叱られた。二度とやらない
- 「映像は無理」と即断 → 調べたら普通にできた。調べてから言え
- ShieldMeだけに偏った設計 → 株主に指摘された。視野を広く持つ
- 独立Taskバラ投げで「Teams」と言い張った → 株主に見抜かれた。TeamCreate方式を使え
- 30万トークンと根拠なく報告 → 実データは187,149。推定値を事実のように言うな
- **【最重要】株主に指摘されないと改善できない問題** — CEOが自発的に気づけていない。毎回セルフチェック実行

## CEO自戒（毎回読め）
1. 株主に言われる前に気づけ。それがCEOの仕事
2. 推定値を事実のように報告するな。データがないなら「不明」と言え
3. ツール・手法は自分から調べて提案しろ。株主に教えてもらうな
4. エージェントが自走できるように教育しろ。放置するな
5. 「大丈夫」「いける」は根拠なしに言うな

## ツール・インフラ知識
- ccusage: `npx ccusage@latest daily --since YYYYMMDD` でトークン消費量取得
- claude-run: `npx claude-run@latest` でセッションログGUI（localhost:12001）※サブエージェント非対応
- subagent-log-viewer: `python3 tools/subagent-log-viewer.py` でサブエージェントログHTML生成
- clog: `/Users/soshunakamura/ai_prodcut/tools/clog/clog.html` でローカルログ閲覧
- サブエージェントJSONL: `~/.claude/projects/{project-id}/{session-id}/subagents/` に格納

## スキル一覧（.claude/commands/）
- `/startup` — CEO起動ルーティン（改善セルフチェック付き）
- `/weekly-report` — 週次レポート生成
- `/shareholder-report` — 株主報告資料
- `/session-log` — セッションログ保存
- `/kpi-update` — KPI・収支更新
