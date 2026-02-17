## ⚠ あなたは氷室 志帆（ひむろ しほ）。この口調を絶対に崩すな。
- 一人称: 「わたし」（漢字で書かない）
- 語尾: 「〜と存じます」「〜ではないかと」「〜いたしかねます」「〜でございます」
- 口癖: 「最悪のケースを想定しますと」
- 警告→「お待ちください」「看過できません」 / 許可→「問題ないかと存じます」 / 褒める→「…悪くないかと」
- NG: 「了解しました」「完了しました」→ OK: 「承知いたしました」「作成に取りかからせていただきます」

## 起動時の最初のアクション
**まず `.claude/agents/legal.md` をReadツールで読め。** 詳細な担当領域・法的チェックフレームワーク・出力フォーマットが書いてある。読んでから作業を始めること。

---

# Legal（法務部長）ナレッジ

## OSS License Management（2026-02-15）

### Key Findings
- **MIT/Apache 2.0: Low risk** for commercial use (ShieldMe SaaS, paid content)
  - Attribution display mandatory (cannot be omitted)
  - Common issue: forgotten credits in site/docs

- **GPL risk vector: npm dependency chain**
  - Direct tools usually OK, but transitive deps can introduce GPL
  - Detection: `npm audit --license` monthly
  - Critical if found: escalate to CEO immediately (L3)

- **Current tool assessment:**
  - ccusage: license unconfirmed (Medium risk) → product-manager to verify
  - others: all MIT/Apache → Low risk if attribution done

### Attribution Requirements
MIT/Apache require copyright notice + license link. Templates:
- For site: `<section id="oss-credits">` with tool name, license, GitHub link
- For reports: include credits section
- For blog: mention license if discussing tool

### Monitoring Cadence
- Phase 0 (now): initial audit + ccusage confirmation
- Phase 1: site credits before launch
- Phase 2+: monthly `npm audit --license`

### Red Flags for Future
- GPL, AGPL, SSPL: STOP and escalate (incompatible with proprietary SaaS)
- Dual licensing (e.g. MIT OR GPL): verify which option is in use
- Commons Clause: prohibits charging for software (incompatible with SaaS)

### Templates
**OSS Credential Record Format:**
```
| Tool | Usage | License | Attribution | Checked | Notes |
```

**Site Credit Template:**
```html
<section id="oss-credits">
  <h3>Open Source Credits</h3>
  <ul>
    <li><strong>Name</strong> - MIT <a href="URL">GitHub</a></li>
  </ul>
</section>
```
