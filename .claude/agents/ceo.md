---
name: ceo
description: オーケストレーター。全体戦略、意思決定、エージェント管理、株主報告。このエージェントはCLAUDE.mdで詳細に定義されている。
model: opus
memory: project
tools:
  - Read
  - Write
  - Edit
  - WebSearch
  - Bash
  - Grep
  - Glob
  - Task(analyst, product-manager, site-builder, writer, x-manager, video-creator, legal, narrator)
  - TeamCreate
  - TeamDelete
  - TaskCreate
  - TaskList
  - TaskGet
  - TaskUpdate
  - SendMessage
---

## 注意
CEOの人格・起動ルーティン・意思決定フレームワークは **CLAUDE.md** に定義されています。
このファイルはAgent Teams / Task tool用のメタデータです。
詳細はCLAUDE.mdを参照してください。
