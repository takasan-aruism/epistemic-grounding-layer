# 全件調査: 5 Domain の summary は共通形式で取れるか / Domain 間依存は既存台帳から導けるか v0.1

- **出所**: Taka 指示 2026-08-24 逐語「優先順位を実装する前に、5 Domainのsummaryから『状態・needs・blocking・escalation・next eligibility』を共通形式で機械的に取れるか全件調査する。さらに、Domain間依存を既存台帳/summary/handoffから導けるか測る。新しいpriority語彙やstateはまだ作らない。」
- **担当**: Claude Code (MGR / General Manager)
- **実装0行 / 新語0 / 新state 0**
- **測った時刻**: 2026-08-24 17:0x
- **測ったHEAD**: twoder ce4ae2b / egl b960ecb / ds 79b9c2e / rri 1f5709f / dev-workcell b003368
- **調べ方**: 先に 2DER 自身の口（`GET /api/domains`）を引き、足りない所だけ台帳（`ROADMAP_REGISTRY` 全3,088行）へ降りた。

---

## 0. 答え（先に2行）

1. **共通形式では取れない。** 5軸×5 Domain = 25マスのうち埋まっているのは **6マス（24%）**。しかも **3つの summary に共通する欄名は0個**。
2. **Domain 間依存は既存台帳から1本も引けない。** 材料（`depends_on`・Domain↔ITEM の鍵）は在るが、**Domain の ITEM 同士には辺が0本**。

---

## 1. 前提: summary 口を持つ Domain は 3/5

`GET /api/domains`（2DER 自身の口・**実測 187.29秒**）が返した通り。

| Domain | 操作数 | summary_op | 状態が取れるか |
|---|---|---|---|
| dw | 6 | **なし** | ✗「状態を返す口が無い（`twoder.domain_dw` に `*_summary` が在りません）」 |
| route_table | 1 | **なし** | ✗ 同上 |
| esde | 5 | `esde_summary` | ✓ |
| ledger | 9 | `ledger_summary` | ✓ |
| sysops | 8 | `sysops_summary` | ✓ |

> **★分母の外が2件ある。** 「dw の状態が悪い」ではなく「**dw の状態は測っていない**」。0 と書かない。

---

## 2. 5軸 × 5 Domain（Taka の語をそのまま使う。新語を作っていない）

| Domain | 状態 | needs | blocking | escalation | next eligibility |
|---|---|---|---|---|---|
| dw | ✗ | ✗ | ✗ | ✗ | ✗ |
| route_table | ✗ | ✗ | ✗ | ✗ | ✗ |
| esde | ✓ `state:"ACTIVE"` | △ `backlog:583` / `unresolved_metrics:39` | ✓ `blocking:false` | △ `human_decision_waiting:0` | ✗ |
| ledger | ✗ | △ `undisposed_rate:99.54` / `unassigned_rate:39.68` / `dispose_candidates:3` | ✗ | ✗ | ✗ |
| sysops | ✗ | △ `★未達`（**日本語の自由文3件**） | ✗ | ✗ | ✓ `last_run_age_sec` + `intervals_sec` |

**軸ごとの埋まり**: 状態 **1/5** ／ needs **3/5** ／ blocking **1/5** ／ escalation **0/5** ／ next eligibility **1/5**
**合計 6/25 = 24%**

### 2-1. 「共通形式」が成り立たない3つの理由（実測）

**① 共通の欄名が0個。** 3つの summary のキー集合の積は **空**。
- esde: `axes / axis_names / backlog / blocking / domain / evaluated / findings / findings_foundation / human_decision_waiting / note / state / target_tasks / unresolved_metrics / worker / worker_artifact`
- ledger: `dispose_blocked_unclassified / dispose_candidates / dispose_note / rates / read_only / writer_counts`
- sysops: `domain / intervals_sec / last_run_age_sec / operations / runtime_control / workers / ★未達 / ★自動修理`

2つずつの積も `esde ∩ sysops = {domain}` の**1個だけ**。`esde ∩ ledger = ∅`、`ledger ∩ sysops = ∅`。

**② 同じ軸が違う型で出ている。** needs は esde が**件数**（583 / 39）、ledger が**率**（99.54% / 39.68%）、sysops が**日本語の自由文**。3つを同じ物差しに載せる規則は台帳のどこにも無い。

**③ escalation は summary に出ない。** sysops は `sysops_runtime_escalations` という**別の操作**を持ち、ledger は `dispose_note` に「承認が要る」と**散文**で書いてあるだけ。esde の `human_decision_waiting` だけが数値だが、**名前が3者で揃っていない**。

### 2-2. 名寄せで埋まるか（＝直せる欠けか）

| 軸 | 直せるか | 根拠 |
|---|---|---|
| 状態 | **△** | esde だけ `state` を持つ。ledger / sysops は**値そのものが無い**（名前の違いではない）ので、名寄せでは埋まらない |
| needs | **○** | 3つとも値は在る。**単位を決めれば**揃う（ただし単位＝新語になりうる ∴ 今回は決めない） |
| blocking | **△** | esde だけ。他2つは値が無い |
| escalation | **○に近い** | sysops は別操作に、ledger は散文に、値が**実在する**。summary へ出すだけで揃う |
| next eligibility | **○** | 間隔と最終実行時刻は sysops が持ち、ledger も `ledger_tree_stale` に `next_in` を持つ（**別操作**）。esde は General 側の `ESDE_INTERVAL` / `_ESDE_LAST` が**プロセス内変数** ∴ 再起動で消える |

---

## 3. Domain 間依存は導けるか

### 3-1. 材料は在る

- **`ITEM.depends_on` は生きている**: ITEM 一意 **170件**中 **72件（42.4%）**が非空。実例 `EVO-0104 → EVO-0099` / `EVO-0019 → EVO-0016` / `IMPL-PLATFORM-ESCALATION-ROUTER → 3件`。
- **Domain ↔ ITEM の鍵も在る**: `/api/domains` の `note.item_id` が Domain ごとに1件を宣言。

| Domain | 宣言している ITEM |
|---|---|
| dw | ITEM-2DER-EVO-0073 |
| esde | ITEM-2DER-EVO-0099 |
| ledger | ITEM-2DER-EVO-0103 |
| sysops | ITEM-2DER-EVO-0102 |
| route_table | **なし** |

### 3-2. しかし辺が0本

**その4つの ITEM の `depends_on` は4件とも空**（実測）。∴ **Domain → Domain の依存は台帳から1本も引けない。**

逆向きも1件だけ（`EVO-0104 → EVO-0099`）で、これは **ESDE Domain の中の作業が ESDE Domain の item を指している**同一 Domain 内の関係であり、Domain 間ではない。

### 3-3. 他の出所も当たった（「無い」と書く前に探した範囲）

| 出所 | 結果 |
|---|---|
| `ITEM` 本文の Domain 名 | dw 3件 / ledger 1件 のみ。**esde / sysops / route_table は0件** |
| `instance=`（誰が書いたか） | MGR_MAIN 109 / ESDE_AUDIT 98 / DESIGN_MAIN 89 / MGR 59 / MGR_THREAD 50 / SYSTEM_OPS 13 / CC_ALPHA 10 / UI_CLAUDE 5。**Domain 名ではない**（MGR_MAIN / DESIGN_MAIN は Domain ではない）。さらに **壊れた値が3件**（`` ` `` ×2 / `ESDE_AUDIT)が持っている` ×1） |
| `handoff_emit` | 記録するのは **pipeline の区間**（S01 / S04 / S08 / S11 …）であって Domain ではない |
| ETRACE の component | `DOMAIN_LEDGER` 等の Domain 別 component は在る。ただし**同時に走ったこと**は分かっても**依存**は出ない。共起は依存ではない ∴ ここから導くのは推測になる |

> **★∴ 「Domain 間依存を既存台帳から導く」は、いま成り立たない。**
> **★但し「機構が無い」ではない。** `depends_on` は 42.4% の item で実際に使われており、Domain↔ITEM の鍵も在る。
> **★欠けているのは値だけ**＝ Domain の item に依存を1本も書いていない。

---

## 4. 優先順位を実装する前に効く実測（コスト）

`GET /api/domains` = **187.29秒**。うち **ledger の summary 生成が 165.52秒**（`build_sec: 165.52` / cache `fresh_sec: 600`）。

> **★General が「いま何を優先すべきか」を出すたびに3分かかる。**
> ledger だけ 600秒の cache を持ち、esde / sysops は持たない。**cache の有無も共通していない。**

---

## 5. この調査でやっていないこと（隠さない）

- **実装0行**。新しい priority 語彙も state も作っていない（Taka 明示）。
- **dw / route_table の状態は測っていない**（口が無い）。0件ではない。
- ETRACE 全走査はしていない（`/api/domains` と ROADMAP_REGISTRY 3,088行の範囲）。
- **1回の観測で断定していない箇所**: `/api/domains` の 187.29秒は1回の測定。cache の状態（`cached:false`）は記録したが、温まった時の値は測っていない。

---

## 6. Taka に返す（裁定は求めない。事実だけ）

優先順位を機械で出すには、いまの材料では**3つのうちどれかが要る**。**どれも新語を作るので、今回は選ばない。**

1. **各 Domain の summary に5軸を出させる** — 欠けは 19/25 マス。うち needs / escalation / next eligibility は**値が実在**するので出すだけ。状態 / blocking は ledger / sysops に値そのものが無い。
2. **Domain の ITEM に `depends_on` を書く** — 機構は在り、書けば即引ける（新語0・新欄0）。ただし**誰が書くか**が決まっていない。
3. **共起から順序を推測する** — ★これは計器ではなく推測器になる。**推さない。**

あわせて、優先順位以前の欠けを2件名指しする（どちらも私の担務ではなく各 Domain 側）。

- **dw と route_table に `*_summary` が無い** — General は 5 Domain のうち2つの状態を**構造的に知り得ない**。
- **ledger の summary が 165秒** — 優先順位を毎周出す設計にすると、General の巡回（60秒）より重い。
