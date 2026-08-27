# DW 手2 — `dw_summary` を作り コックピットの6欄へ繋いだ v0.1

- 担当: DW（`DW_CLAUDE`） / 開発票: `ITEM-2DER-EVO-0137`
- 日付: 2026-08-28 08:0x
- 測ったHEAD（作業前）: twoder `a90f56a` / dev-workcell `b003368` / egl `283d685`
- 形式: 前後の数を出す（★指示の逐語「前後の数を必ず出す」）

---

## 0. 前と後（★同じ口＝ `/api/domains` の `cockpit` を front door 経由で引いた）

| | 現在状態 | backlog | 最後に動いた時刻 | 次に何を待っているか | Worker | 上申 | 計 |
|---|---|---|---|---|---|---|---|
| **前**（08-28 07:55） | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **0 / 6** |
| **後**（08-28 08:09） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **6 / 6** |

**全体: 8 / 42 → 14 / 42。**

★✗ の理由は6欄とも逐語「**状態を返す口が無い**」だった
（`domains_view._summary_op` は `*_summary` という命名で状態の口を探すが、`domain_dw` に1本も無かった）。

★**分母は 42（7 Domain × 6欄）**。brief の「7 / 48（8 Domain）」とは鍵が違う ―― 実行時の
`manager_v0.DOMAIN_OPERATIONS` は **7 Domain**（dw / esde / inference / ledger / route_table / structure / sysops）。
★私は brief の数を写さず、毎回 `/api/domains` から引き直した。

### ★後の値（実測・そのまま）
```
現在状態          "ACTIVE"        （鍵= 最後の DW event からの経過 < 3600秒）
backlog           543             （鍵= dispatch._MAP の次の op が NONE/BLOCKED でない TASK 数）
最後に動いた時刻   段ごとの経過秒   PLAN 429 / CREATE 1971 / AUDIT 24295 / COMPLETE 66198 …
次に何を待っているか 95            （鍵= claude_barrier=True かつ op が NONE/BLOCKED でない）
Worker            ["CLAUDE","QWEN_AUDITOR","QWEN_LIVECODER"]   （出所= dispatch.DEFAULT_ACTORS）
上申              142             （鍵= DW 正本の state=JUDGE_REQUIRED。一覧は dw_escalations）
```

---

## 1. 作った物（★2本だけ・★新台帳 0 / 新 state 0 / 新 ID 族 0 / 新 Worker 0 / front door の口 0増）

| 物 | 場所 | 何をするか |
|---|---|---|
| `dw_summary()` | `twoder/domain_dw.py` | Domain の状態だけを返す。**判定しない＝数と名前だけ** |
| `dw_escalations(limit)` | 同上 | 上申（`JUDGE_REQUIRED`）の件数と一覧。**処分も優先順位も決めない** |
| 表に2語 | `manager_v0.DOMAIN_OPERATIONS["dw"]` | ★`to_domain` も `get_domain` も **1行も直していない**（esde / sysops / ledger / structure と同じ形） |

### ★1-1. 兄弟に合わせた（指示の逐語「先に読む」）
`domain_esde.esde_summary` / `domain_sysops.sysops_summary` を先に読み、欄名を揃えた
（`state` / `backlog` / `last_run_age_sec` / `human_decision_waiting` / `workers`）。
authority も先例どおり **`READ_ONLY_INSPECTION`**（明細 +0 / thread +0 / etrace +1＝自分の観測の記録だけ）。
★`sysops_summary` が 2026-08-25 に直した「**自分の実行だけ記録に残っていなかった**」欠けは、**先に塞いだ**
（`_dw_emit` を最初から呼ぶ）。

### ★1-2. 写しを持たない
- state の分類 → `dw.workcell.derive_state`（DW 正本）
- 次の手番 → `dw.dispatch._MAP` と `dispatch.DEFAULT_ACTORS`（DW 正本の表を実行時に引く）
- 完了阻害 → `dw.workcell.completion_blockers`
∴ **`domain_dw` の中に state 語も actor 名も 1つも書いていない。**

---

## 2. ★General 側で 1つ直した（★domain_dw の外・隠さない）

`domains_view.cockpit()` の **上申の欄が、どの Domain でも逐語 `sysops_runtime_escalations` と
`/api/domain_sysops` を固定で返していた**。

∴ **DW が上申の口を持った瞬間に、DW の欄が「sysops の口から取った」と嘘をつく**（実測でそうなった）。

★直し = 実際に一致した操作名をそのまま出し、値はその Domain の summary の `escalations` から引く。
★新しい欄は作っていない。★sysops 側の表示は壊れていない（実測）:

```
dw     上申: connected=true counted=true  field=dw_escalations              value=142  via=to_domain('dw_escalations')
sysops 上申: connected=true counted=false field=sysops_runtime_escalations  value=null via=to_domain('sysops_runtime_escalations')
```
★`counted=false` は「口は在るが summary が数を返していない」という **既存の正しい表示**（埋めていない）。

---

## 3. ★併せて測った（★私の欄が「見えない」原因になる）

`/api/domains` は **1回 約 360秒**（実測 359.6s／server 側 359.54s）。
in-process で **重い口を外すと 11.0秒**、内訳は:

| Domain | 秒 |
|---|---|
| sysops | 0.0 |
| **dw（新）** | **0.27** |
| structure | 1.88 |
| esde | 2.9 |
| inference | 5.86 |
| **ledger** | **★重い口として除外（既知 71秒 → 実測はさらに悪化している見込み）** |
| route_table | 状態の口が無い |

∴ **DW の 6/6 は 0.27秒で出るが、画面に出るまで約6分かかる。**
★これは Ledger Domain の領分 ∴ **私は触らない。上げるだけ。**

---

## 4. 受入（指示 §6 の 2番）

| 条件 | 結果 |
|---|---|
| `dw_summary` が General から呼べる | ✅ `to_domain("dw_summary")` で返る（0.24〜0.27秒） |
| コックピットの DW 行の接続欄数が増えている | ✅ **0/6 → 6/6**（全体 8/42 → 14/42） |
| 前後の数を出した | ✅ 上表 |
| 新しい台帳 / state / ID 族を作っていない | ✅ 0 / 0 / 0 |

---

## 5. していないこと

- `dev-workcell/dw/workcell.py` の状態機械 —— **1文字も触っていない**
- `JUDGE_REQUIRED` の中身の分類（`EVO-0123` の領分）—— **していない**（数えただけ）
- `related_failure_patterns`（`EVO-0124` の領分）—— **触っていない**
- 他 Domain の内部 —— **触っていない**（`domains_view` は General の表示であって Domain の内部ではない・§2 に明記）
- TASK を 1件も進めていない
