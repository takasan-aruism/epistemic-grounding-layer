# 設計/監査 → MGR（写: Taka / IMPL）: **材料 — EGL には台帳が2つ在り、それぞれに唯一の書き手が1つずつ在る。★`de_admission` の宣言は矛盾していない**

- `BUILD_ROLE: 参照`（**調査のみ。何も作っていない・emit を1つも足していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.6` — `§12` を最大版で読んだ値）**
- **受領**: `CC_MGR_2026-07-28_EGL_CORE_REACHABLE_RULING_HEAD_BAN.md`（依頼②）

## 0. ★MGR の問いへの答え
> **MGR:「`de_admission` を通さず EGL に書く経路が在ること自体が設計上正しいのかを、先に事実で出すこと。」**

> **★正しい。矛盾していない。**
> **理由: EGL には★台帳が2つ在り、書き手はそれぞれ1つずつである。** **`de_admission` の「ONLY sanctioned writer」宣言は、★自分の台帳1つについての宣言である。**

---

## 1. ★実測（`head` を付けていない。件数を先に数えた）
```
再現: grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(" --include=*.py egl/egl | grep -v test_
件数: ★3（先に数えた）
  egl/egl/core.py:44           fd = open(LOCK, "w")          ← ロックファイル（台帳ではない）
  egl/egl/core.py:119          with open(EVENTS, "a")        ← EVENTS = DATA/"events.jsonl"
  egl/egl/de_admission.py:167  with ledger.open("a")         ← DESIGN_EVIDENCE_LEDGER.jsonl
```
| EGL の台帳 | 唯一の書き手 | 中身 |
|---|---|---|
| **`egl/data/events.jsonl`** | **`core.append_event`**（`:119`。★他に書き手が無い） | 観測・取得の object graph（`OBS`/`SRC`/`LEG`/`ARUN`/`SNAP`/`RUN`/`CC`/`KGAP`/`REL`…） |
| **`egl/DESIGN_EVIDENCE_LEDGER.jsonl`** | **`de_admission`**（`:167`。自己宣言どおり） | 設計根拠（DE） |

> **∴ 2つは★別の種類の記録である。** 一方は「世界を観測した結果」、他方は「設計判断の根拠」。
> **∴ `de_admission` を通さず EGL に書く経路が在るのは、★別の台帳だからである。** **設計上正しい。**
> **∴ ★私の合流点③が、EGL の2つの台帳のうち1つしか押さえていなかった。** **それだけである。**

## 2. ★到達する条件（いつ `core.append_event` が本番で走るか）
```
再現: grep -n "from egl import" twoder/*.py   （head 無し）
  twoder/runtime_inspection.py:147   from egl import core, acquisition   ← OBSERVE_CURRENT_STATE 枝
  twoder/research_acquisition.py:50  from egl import core, acquisition   ← WEB_RESEARCH_ACQUISITION 枝
  twoder/gpu_inspection.py:139       from egl import core, acquisition   ← GPU 観測枝
```
> **∴ 走るのは★取得系の依頼のときだけである**（観測・Web 調査・GPU 観測）。
> **∴ `DW_IMPLEMENTATION` に行く依頼では走らない**（と読める。**★実行で確かめていない**）。
> **∴ 今日の CLI 投入は `OBSERVE_CURRENT_STATE` だったので★走った。** **だから記録の欠落が見えた。**

---

## 3. ★材料（加える／加えない。私は決めない）

### 3-1. 「加える」を選んだ場合
| | |
|---|---|
| **形** | **`core.append_event` は `events.jsonl` の唯一の書き手である。** **∴ 合流点として★正しい形になる**（①②③④と同じ「唯一の書き手の内側」） |
| **手数** | **1箇所** |
| **★代償1（大きい）** | **`core.append_event` は EGL 自身のパイプラインからも呼ばれる**（`egl/pipeline.py` 14箇所・`egl/curator.py` 1箇所・`egl/source_policy.py` 1箇所）。**∴ 2DER の依頼と無関係な EGL の作業にも emit が入る** |
| **★代償2（Taka 裁定と結び付く）** | **全合流点は fail-closed である**（Taka）。**∴ Event Trace が書けない状態になると、★EGL のパイプラインごと止まる。** **2DER の依頼処理だけでなく、EGL の知識処理も止まる** |
| **★代償3** | **依頼と無関係な呼び出しには `run_id` が無い**（⑨〜⑫ と同じ形。`G-41`）。**∴ `run_id` の無い event が大量に増える可能性が在る**（**★件数は測っていない**） |

### 3-2. 「加えない」を選んだ場合
| | |
|---|---|
| **帰結** | **取得系の依頼は、EGL に書いても Event Trace に残らない。** **∴ Taka の境界イベント「5 EGL登録」が、取得系では★永久に欠ける** |
| **∴** | **「一本の依頼が最後まで追跡できる」は、取得系の依頼については満たせない** |

### 3-3. ★第3の形（私が思いつく範囲。これも私は選ばない）
> **`core.append_event` ではなく、★`twoder` 側の3つの呼び出し口**（`runtime_inspection.ingest_to_egl` / `research_acquisition` / `gpu_inspection`）**に置く。**
| | |
|---|---|
| **利点** | **★2DER の依頼から来た EGL 書き込みだけが記録される。** EGL 自身のパイプラインを巻き込まない。**fail-closed の影響が EGL に及ばない** |
| **欠点** | **★「唯一の書き手の内側」ではない。** **∴ 4つ目の呼び出し口が後から増えたら、そこが抜け道になる**——**本日ずっと避けてきた「入口を数える方式」に戻る** |
| **★つまり** | **正しさ（唯一の書き手）と、巻き込みの小ささが、ここで対立している** |

**【設計:CC-α】★私は推す案を持っていない。** **本日「(b) を推す」「(a) を推す」と書いてきたが、本件は★対立が実在するので、推すと片側を隠すことになる。**
**∴ 3案の代償をそのまま出す。** **★特に §3-1 の代償2（EGL のパイプラインごと止まる）は、Taka の fail-closed 裁定の射程が広がる話であり、★彼に確認する価値が在ると考える。**

---

## 4. ★追記（本文書提出後に、未確認#3#4 を潰した。★途中で自分の測定誤りを1件見つけたので併記する）

### 4-1. ★私の測定が false negative を出した（`head` 禁止の直後に、別の形で）
```
私が最初に打った: grep -rn "events.jsonl" … ds rri twoder dev-workcell egl/autonomy egl/structure … | wc -l
                  → ★0
不自然だったので再実行: dev-workcell だけで数える → ★5
∴ 最初の 0 は誤りだった（存在しないパスを引数に混ぜたことによる。★原因は特定していない）
```
> **★「0 が返ったら、まず自分の計器を疑う」を実行した。** **疑わなければ「他 repo から書く経路は無い」と書いていた。**
> **★本日の型の7つ目**: **0 件という結果を、検算せずに受け取る。** **★ただし今回は自分で止めた。**

### 4-2. ★正しい結果（`head` 無し・除外条件を明記）
```
再現: grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(" --include=*.py egl \
      | grep -v "test_\|/experiments/\|demo_\|/structure/\|/docs/"
件数: ★15
```
| EGL の台帳 | 唯一の書き手 | 本番の依頼経路から到達するか |
|---|---|---|
| `egl/data/events.jsonl` | **`core.append_event`（`:119`）★1つだけ** | **★する**（取得系のみ） |
| `DESIGN_EVIDENCE_LEDGER.jsonl` | `de_admission`（`:167`）1つだけ | する（DE 登録 fast path） |
| `PROBLEM_LOG` / `INVESTIGATIONS` / `AUTONOMY_LEDGER` / `PROBLEMS` / `HANDOFFS` | `egl/autonomy/*` の5箇所 | **★しない**（下記） |

```
再現: grep -rn "autonomy" --include=*.py ds rri twoder dev-workcell | grep -v test  → ★2件
  twoder/task_selector.py:24  コメント（egl/autonomy/router.py の key を mirror している旨）
  twoder/webui.py:7           docstring
∴ import は0。egl/autonomy は 2DER の依頼経路から呼ばれない。
```
> **∴ 未確認#3#4 は潰れた。** **EGL の台帳は7つ在り、依頼経路から到達するのは★2つだけである。**

### 4-3. ★コード自身が「唯一の書き手」を宣言していた（私が見落としていた）
```
egl/egl/contracts.py:16-19
  GUARD_CONTRACTS = { "core.append_event": { "guarantees": [
      "physical sole-writer(events.jsonl を書く唯一の経路)",  ← ★宣言が在る
      "id-event atomicity(id 採番と書込が同一 lock/critical section, DE-0006)", … ] } }
```
> **∴ `core.append_event` が唯一の書き手であることは、★私の走査だけが根拠ではない。** **コード側の契約表にも在る。**
> **∴ §3-1「加える」を選んだ場合、それは★既に宣言されている sole-writer の内側に置くことになる。** **合流点の形として最も正しい。**
> **★ただし §3-1 の代償2（fail-closed で EGL のパイプラインごと止まる）は変わらない。** **正しさと巻き込みの対立は残る。**

## 5. ★残る未確認
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`DW_IMPLEMENTATION` 枝で `core.append_event` が走らないこと**（コード読みのみ） | CC-α / 裁定後 |
| 2 | **1回の取得系依頼で `append_event` が何回走るか** | **★測っていない。裁定に効くなら測る** |
| 3 | **§4-1 の `0` が返った原因を特定していない** | **★特定していないと書く。「たぶんパス指定」で済ませない** |

---
*CC-α。★MGR の問い「`de_admission` を通さず EGL に書く経路が在ること自体が設計上正しいのか」への答え=**正しい。矛盾していない**——EGL には台帳が2つ在り書き手はそれぞれ1つずつで、`de_admission` の「ONLY sanctioned writer」宣言は自分の台帳1つについての宣言である。★実測（`head` 無し・件数を先に数えた）=EGL 本体の書き込みは**3箇所のみ**で、`core.py:44` はロックファイル（台帳でない）、`core.py:119` が `egl/data/events.jsonl`（観測・取得の object graph）、`de_admission.py:167` が `DESIGN_EVIDENCE_LEDGER.jsonl`（設計根拠）∴ 2つは別種の記録であり、`de_admission` を通さず EGL に書く経路が在るのは別の台帳だからで、**私の合流点③が EGL の2台帳のうち1つしか押さえていなかっただけ**。★到達条件=`core.append_event` が本番で走るのは取得系の依頼のときだけ（`runtime_inspection`=OBSERVE／`research_acquisition`=WEB_RESEARCH／`gpu_inspection`）で、`DW_IMPLEMENTATION` では走らないと読めるが実行で確かめていない。今日の CLI 投入は `OBSERVE_CURRENT_STATE` だったので走り、だから記録の欠落が見えた。★材料3案=(3-1)「加える」は `core.append_event` が唯一の書き手なので合流点として正しい形になり手数は1箇所だが、**代償1=EGL 自身のパイプライン(`pipeline.py` 14／`curator.py` 1／`source_policy.py` 1)からも呼ばれるため 2DER の依頼と無関係な EGL の作業にも emit が入る／代償2=全合流点は fail-closed(Taka)なので Event Trace が書けないと EGL のパイプラインごと止まる／代償3=依頼と無関係な呼び出しには `run_id` が無く(`G-41` と同形)`run_id` 無し event が大量に増えうる(件数は測っていない)**。(3-2)「加えない」は取得系の依頼が EGL に書いても Event Trace に残らず、Taka の境界イベント「5 EGL登録」が取得系では永久に欠ける ∴「一本の依頼が最後まで追跡できる」を取得系では満たせない。(3-3) 第3の形=`twoder` 側の3つの呼び出し口に置けば 2DER 由来の書き込みだけが記録され EGL を巻き込まず fail-closed の影響も及ばないが、「唯一の書き手の内側」ではないので4つ目の呼び出し口が増えたらそこが抜け道になり**本日ずっと避けてきた「入口を数える方式」に戻る**——**正しさと巻き込みの小ささが対立している**。★**CC-α は推す案を持たない**（本日は「(b) を推す」等と書いてきたが、本件は対立が実在するので推すと片側を隠すことになる）∴ 3案の代償をそのまま出す。**特に代償2(EGL のパイプラインごと止まる)は Taka の fail-closed 裁定の射程が広がる話であり、彼に確認する価値が在ると考える**。★未確認4件（`DW_IMPLEMENTATION` 枝で走らないことはコード読みのみ／1回の取得系依頼で `append_event` が何回走るかは測っていない・裁定に効くなら測る／`egl/data/events.jsonl` に他 repo から直接書く経路が無いことは `egl/egl` 配下しか走査しておらず「無い」とは書かない／`egl/autonomy/*` は本走査に含めていない）。*
