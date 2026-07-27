# 設計/監査 → MGR（写: Taka / IMPL）: Build 9 差し戻しを受領。**ただし作る対象が変わる — 帳簿を読むプログラムは既に在る**

- `BUILD_ROLE: 参照`（**`CC_DESIGN_2026-07-27_BUILD9_SPEC_LEDGER_QUERY.md` v1.0 は SUPERSEDED by 本文書。IMPL は v1.0 から作らないこと**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.5）**
- **受領した文書**: `CC_MGR_2026-07-27_BUILD9_SENT_BACK_PATH_MISSING.md` / `CC_MGR_2026-07-27_D14_D15_RECEIVED_NEXT_IS_BUILD_CAPABILITY.md`

## 0. 差し戻しを受ける（先に）
**指摘は正しい。** MGR §2 の「`BUILD_CAPABILITY` 経由で 2DER に作らせ、経路を実証する」は**私の SPEC に1度も現れていない。** 落とした。
**特に「順序が不可逆」の指摘に反論しない。** **手で書いた後では「2DER が作れるか」はもう測れない。**

**ただし、着手前の確認（MGR §3）を進めた結果、(a) でも (b) でもない事実が出た。先に出す。**

---

## 1. ★★帳簿を読むプログラムは、既に在る【監査:CC-α・コード構造】

```
twoder/ids.py （88行・DE-0180）
```
**docstring 逐語（先頭）:**
> **"2DER canonical ID resolver (DE-0180). Every 2DER-issued id resolves through here to its owning store's real record.** This is what makes 'every candidate field is backed by a 2DER-issued id' checkable: an id is valid iff resolve(id) returns a record. **Operating principle: we only ever handle things registered in 2DER — an id that does not resolve is a hole, not something to fill from memory.**"

**`resolve(rid)` が扱う接頭辞と持ち主（docstring と本体の実装が一致していることを実読で確認）:**

| 接頭辞 | 持ち主 | 実装（`twoder/ids.py`） |
|---|---|---|
| `UTT-` / `DEV-` / `THREAD-` | **DS** | `ds.phase0.utterances()` / `dialogue_events()` |
| `OBS-` `SRC-` `ARUN-` `RUN-` `LEG-` `SNAP-` | **EGL** | `egl.core.get_state(rid)` |
| `DE-` | **EGL DE 台帳** | `DESIGN_EVIDENCE_LEDGER.jsonl` を走査 |
| `ADM-` | **EGL admission** | `egl.de_admission.resolve_admission` |
| `RREQ-` / `RINT-` / `RSIG-` | **RRI** | `rri.intent_record.resolve` |
| `TASK-` | **DW** | `dw.workcell._read_events` / `derive_state` |
| `ART-` / `CHG-` | twoder | `artifact_registry` |
| `ROADMAP-` `PHASE-` `ITEM-` `AMEND-` | twoder | `roadmap_registry` |
| `INTV-` | twoder | `intervention` |
| `AUTHP:` / `AUTHD:` | twoder | `authority.resolve_policy` |

**∴ 私が Build 9 SPEC §1-2 で「IMPL が接頭辞と台帳の対応表をコードから確認して作れ」と書いたものは、既に存在している。**
**私はそれを作らせようとしていた。** **「既存を読む。作り直さない」に反していた。**

### 1-1. しかも「無いものを埋めない」規律まで、既に書かれている
> **"an id that does not resolve is a hole, not something to fill from memory"**
> **`resolve()` は解決できない時 `None` を返す。** `egl.core.get_state` が `{}` を返す場合も **`None` に落として「未解決」を保つ**（逐語コメント: `# get_state returns {} for unknown ids -> treat as unresolved`）。

**∴ 私が SPEC §1-3 で新設しようとした3状態のうち、`ANSWERED` / `NOT_FOUND` の区別は既に実装されている。**
**新規に要るのは `NOT_ANSWERABLE`（＝接頭辞そのものが未対応）だけである。**

### 1-2. ★これは本日6回目の「正しく作ったが作用する場所に無い」である
```
再現: grep -rn "from twoder import ids\|import ids\b" --include=*.py twoder/ rri/ ds/ dev-workcell/
```
**【未確認】上記は未実行である。** **本文書では「配線が無い」と断定しない**（本日5回、ソースを読んで動作を断定して誤った）。
**確実に言えるのは1つだけ**: **`SELECTED_ACQUISITION_METHOD` の8種のいずれも `ids.resolve` を呼んでいない**（Build 8 監査 §2-1 で列挙済み）。**∴ front door から `ids.resolve` へ到達する経路は無い。**

### 1-3. ★私は `ids.resolve()` を実行していない（運用方針 v1.5）
**読んだだけである。動かしていない。**
- **理由**: 本日、私は「ソースに在る」を「動く」と読み替えて5回誤った。**同じことをここでしない。**
- **かつ**、`resolve()` を私が叩くことは**台帳の中身を front door を通さずに得る行為**であり、v1.3 §6-7 が止めようとしているものそのものである。
- **∴「`ids.resolve` は動くか」の検証は、本 build の受入1にする。** **私が先回りして確かめない。**

---

## 2. ★MGR の (a)/(b) に答える — **どちらでもない。(c) を提案する**

| MGR の選択肢 | 私の判断 |
|---|---|
| **(a) 経路を通して「帳簿を読むプログラムを作れ」と依頼する** | **★このまま出すべきでない。** **既に在るものを作らせることになる。** 2DER が2本目を作れば、`ids.py` と重複した読み口が生まれる——**境界にとって最悪の結果である**（読む経路が2本になると、どちらが正典か決まらない） |
| **(b) 経路が使えない理由を書く** | **該当しない。** 経路が使えない理由は見つかっていない |
| **★(c)** | **依頼の中身を「作れ」から「配線せよ」に変える。経路の実証は維持する** | 

### 2-1. (c) の内容
**front door から `BUILD_CAPABILITY` / `MODIFY_EXISTING` として入れる依頼を、次に変える:**

> **既存の `twoder/ids.py::resolve` を、front door から呼べる acquisition method として配線せよ。新しい resolver を作らないこと。**

- **成果物**: 配線1本（`SELECTED_ACQUISITION_METHOD = "LEDGER_QUERY"` の分岐 + `ids.resolve` の呼び出し + 未対応接頭辞の `NOT_ANSWERABLE`）。
- **経路の実証は失われない。** **「Claude が外から依頼し、2DER が作る」は、依頼の中身が何であっても測れる。** **MGR §2-1 の目的2はそのまま成立する。**
- **むしろ実証として強くなる**: **依頼が小さいほど、失敗したときに「経路の限界」だと言い切れる。** 大きな依頼で失敗すると、経路の限界なのか依頼が難しすぎたのかが分からない。

### 2-2. 順序は守る
**MGR §3 の「IMPL に手で書かせるのは結論が出た後」を守る。** **本文書は結論を出していない。裁定を待つ。**
**私は SPEC v2.0 をまだ書いていない。** **裁定が出てから書く。**

---

## 3. ★先に出す実装可能性（feasibility-first・裁定の材料）

**経路が本件で詰まりうる場所を、先に3つ挙げる。当たっても外れても記録する。**

| # | 詰まりうる場所 | 根拠 |
|---|---|---|
| **F1** | **worker の生成物が一時 workspace に置かれ、`twoder/` に配置されない可能性** | 過去の実依頼の文面に「**一時workspace内に**」「**本番repoや既存ledgerは変更せず**」が繰り返し現れる（`rri_records` の REQUEST 群・Build 8 前に確認済）。**∴ 配置まで届かないのが既定の可能性が高い** |
| **F2** | **`submit.py` の routing 差し込みは本番の分岐変更であり、worker がそこまで触れるかは未確認** | `twoder/submit.py` は front door 本体。**触れないなら「作れるが置けない」で止まる** |
| **F3** | **planner が `MODIFY_EXISTING` を扱えるかは未確認** | `build_planner.py` は `BUILD_CAPABILITY` の PLAN actor と docstring に書かれている。**`MODIFY_EXISTING` も同じ `DW_IMPLEMENTATION` へ行く（`submit.py:391`）が、planner の対象かは読んでいない** |

**F1/F2 が起きた場合の扱い（MGR §2-3 の指示どおり）:**
- **手で代替しない。** **「作れるが置けない」を経路の限界として記録し、MGR に上げる。**
- **★そしてそれは、そのまま Taka の「外注で生成、配置するまで」の**配置**が未実装であることの発見になる。** **v1.4 §1-4 で Claude に残された役割は「生成・配置まで」であり、配置の経路が無いなら、そこが次の欠落である。**

---

## 4. 私の誤り（消さない）
1. **MGR の指示の半分（`BUILD_CAPABILITY` 経由）を SPEC から落とした。** 差し戻しは正当。
2. **既に在る `twoder/ids.py` を読まずに、同じものを作る SPEC を書いた。** **「既存を読む。作り直さない」に反した。** **§1 を見つけたのは、MGR の差し戻しで着手が止まったからである。** **差し戻しが無ければ、重複した読み口を1本作っていた。**
3. **`ids.resolve()` を実行していない。** 動作は **【未確認】** のまま置く（v1.5）。

---
*CC-α。Build 9 差し戻しを受領（`BUILD_CAPABILITY` 経由の指示を落としたのは私の誤り・順序不可逆の指摘にも反論しない）。★着手前確認で対象が変わった——帳簿を読むプログラムは既に在る: `twoder/ids.py::resolve`(DE-0180) が15系統の接頭辞を持ち主のストアへ解決しており、docstring に「解決しない id は穴であって記憶から埋めるものではない」と no-fabrication 規律まで書かれ、`{}` を `None` に落として未解決を保つ実装まで在る。∴ 私が SPEC §1-2 で作らせようとした対応表も §1-3 の ANSWERED/NOT_FOUND も既存。新規に要るのは NOT_ANSWERABLE（未対応接頭辞）だけ。★本日6回目の「正しく作ったが作用する場所に無い」——ただし配線の不在は断定せず、確実なのは acquisition method 8種のいずれも ids.resolve を呼んでいないことのみ。★`ids.resolve()` は実行していない（読んだだけ・v1.5）。私が叩くこと自体が front door を通さない読みであり、動作検証は本 build の受入1にする。★MGR の (a)/(b) はどちらも採らず (c) を提案: 依頼を「作れ」から「既存の ids.resolve を配線せよ」に変える——既に在るものを作らせると読み口が2本になり、どちらが正典か決まらず境界にとって最悪。経路の実証は依頼の中身に依らず成立し、依頼が小さいほど失敗を「経路の限界」と言い切れるので実証としてはむしろ強い。feasibility を先出し: F1 生成物が一時workspaceに留まり配置されない／F2 worker が submit.py の分岐を触れるか未確認／F3 planner が MODIFY_EXISTING を扱うか未確認。F1/F2 が起きたら手で代替せず「作れるが置けない」を記録＝Taka の言う「生成・配置まで」の配置が未実装という発見になる。SPEC v2.0 は裁定後に書く。*
