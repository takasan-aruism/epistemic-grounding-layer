# 【監査＋判定案】`Request` は切れていない — **★First FAIL は `Ledger`。★配線は3点 前進した**

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-31 01:3x / TYPE=FINDING
- **運用方針 確認済（版: v2.8）** ／ **受領**: `CC_IMPL_2026-07-31_D144_TASK_WIRING_BUILT.md`（監査対象）／`CC_MGR_2026-07-31_D145_…md`（§1-1 の依頼）
- **2DER 優先原則**: ①読み出しの口のみ ②「今回の依頼の入力内容・受理時刻に到達できるか」 ③**★到達できた（§1）** ④実装しない ⑤該当なし ／ **`:8005` 未使用**

---

# 1. ★MGR §1-1 の依頼 — **★到達できる。`Request` は PASS のまま**

| 到達先 | ★結果（★私が既存の口だけで取った。★連番も合成 id も当てていない） |
|---|---|
| **入力内容** | **★到達できる。** `GET /api/state?task_id=TASK-2DER-0C458F38` の **`goal`** が依頼文 |
| **受理時刻** | **★到達できる。** 同じ応答の `etrace_run_id=ETR-b24887a08d12` → `GET /api/resolve` の **`ENTRY.ts = 2026-07-31T01:09:04.434584`**（★receipt `01:09:04.434285` と **300µs 差**／★POST `01:09:04.429024` の直後）。**★ENTRY に依頼文も入っている** |
| 手がかり | **★応答が返す `task_id`**（★第2試行は `trace_key` だった） |

## 1-1. ★ただし「同じ PASS」ではない（★言い換えない）
```
★第2試行: trace_key ★1つから、入力・受理時刻・RRI・実行・観測・応答へ★1段で到達できた
★今回    : ★task_id 経由の★2段になった（task_id → /api/state → goal ／ → etrace_run_id → ENTRY.ts）
★かつ ★trace_key そのものは解決できない（A-3 ×）
∴ ★D-140 で作った `SUBMIT-` の口は、★この経路では★使われなくなった（★壊れたのではなく、★prefix が外れた）
```
> **★MGR の指摘は正しい**: **「既存 ID が不変」と「新しい依頼で通る」は別物である。**
> **★私は両方 確かめた。★前者は IMPL の申告どおり、★後者も通った。**

---

# 2. ★これは私の設計ミスである（★先に書く）

```
★私は SPEC を書くとき、★`webui.py:661` の `key = (tid or "SUBMIT") + "-" + 乱数` を★既に読んでいた
  （★第1試行の調査で自分で引用している）。
★それなのに「task を作れ」と指示したとき、★task が出来ると prefix が `SUBMIT-` から外れることを
  ★予見しなかった。
∴ ★D-140 の修正の前提を、★私の SPEC が外した。
★IMPL は原因まで特定して止めた。★IMPL の判断は正しい。★私の指示が足りなかった。
```

---

# 3. ★IMPL の申告を独立に取り直した（★全一致）

| 受入 | IMPL | ★私の再検証 | |
|---|---|---|---|
| A-1 / A-2 | task 生成・`resolved=true` | **`TASK-2DER-0C458F38` → `resolved=true` / `events=1` / `CREATED`** | 一致 |
| **A-3** | **×** | **`TASK-2DER-0C458F38-vhDl1Q` → `resolved=false`** | 一致 |
| A-4 | ○（口を選ぶ必要が在る） | `/api/state` の `egl.source_refs` → `OBS-00963〜66` → `ARUN-00962〜65` | 一致 |
| B-1 | `gpu`/`nvidia` 0件 | **★私の走査でも 0件**（大小無視・打ち切り無し） | 一致 |
| B-2 | 1ファイル・1 hunk | **★1ファイル / 1 hunk / 13挿入1削除** | 一致 |
| C-1 | 基準値10件 不変 | **★私が取り直して 10件とも不変** | 一致 |
| 副作用 | tasks 156→157 | **★私の実測でも 157（+1）** | 一致 |

---

# 4. ★判定案（★Taka の8点。★確定は MGR）

| 配線 | 第2試行 | **★今回** | 根拠 |
|---|---|---|---|
| **Request** | PASS | **★PASS** | 入力内容（`goal`）・受理時刻（`ENTRY.ts`）に到達（§1）。**★経路は `task_id` 経由に変わった** |
| **RRI** | PASS | **★PASS** | `/api/state` の `rri` ／ `ETR-b24887a08d12`(22 event) |
| **Task** | **FAIL** | **★PASS** | **★task が作られ、引ける**（`events=1`/`CREATED`）。応答が `task_id` を返すので Request から辿れる |
| **Runtime** | （Task の下流としては未確認） | **★PASS（★但し書きつき）** | `ARUN-00962〜65` が投入の内側で実行され、**★task から辿れる**。**★但し「task が起動したから走った」ではない**（★観測は submit の中で走り、★記録が `task_id` で束ねられている）。**★因果ではなく同居である** |
| **Observation** | — | **★PASS** | `OBS-00963〜66` が引ける |
| **Ledger** | FAIL | **★FAIL ← ★First FAIL** | **★生出力（`blob://…`）に既存の口から到達できない**（★今回 触っていない） |
| **DW** | FAIL | **★FAIL** | 要約が無い（★DW は動いていない・`dev-workcell` 無変化） |
| **Response** | FAIL | **★FAIL** | 生の配列・GPU 使用率は欠落のまま |

```
★Last PASS  : Observation
★First FAIL : Ledger
★前進       : ★3点（Task / Runtime / Observation が FAIL・未確認 → PASS）
★First FAIL が ★Task → ★Ledger へ動いた
```

## 4-1. ★IMPL の5行と、私の判定の違い（★差分だけ）
```
★IMPL: Last PASS = Task の生成 ／ First FAIL = A-3（trace から task）
★私  : Last PASS = Observation ／ First FAIL = Ledger
★理由: A-3 は★受入の項目であって、★Taka の8点の配線ではない。
       ★入力内容へは task_id 経由で到達できた ∴ ★Request も Task も切れていない。
★★A-3 は「配線の切断」ではなく「★D-140 で作った口が、この経路で使われなくなった」である。
  ★次の1件の候補ではあるが、★今回の First FAIL ではない。
```

---

# 5. ★次に直す1件（★私の案。★1件だけ。★実施しない）

> ### **★`Ledger` — 生出力（`blob://…`）に既存の口から到達できるようにする。**

**★理由**: **★Taka の順序どおり、★最初に切れている地点だからである**（Request/RRI/Task/Runtime/Observation は PASS）。

## 5-1. ★併せて渡す（★私が決めない1点）
```
★A-3（新形式 trace_key が解けない）を、★どのファイルで直すか。★IMPL は「設計判断」として保留した。★正しい。
★私の案: ★`webui.py:661` 側で trace_key の prefix を常に `SUBMIT-` にする。
★理由  : ★`ids.py` 側で `TASK-…-<乱数>` を扱うと、★`TASK-` が「DW task」と「submit trace」の
         ★2つを指すことになる ＝ ★本日 我々が13回 潰してきた形の再生産である。
★★ただし これは「次の1件」ではない（★Ledger が先）。★順番は MGR が決める。
```

---

# 6. ★登記（★MGR `D-145` §4 の指示。★id は設計が採った）
```
G-86  ★同じ応答の中に「実測でない値」と「実測」が並ぶ
      （`/api/state` の `egl.current_claims` に「GPU使用率 約0.92 (92%)」＝ DE-0072/0170/0171 由来。
       ★今回の実測に使用率は無い）
★直さない。★資料: gap 85 → 86。★JSON と MD の食い違い 0 件。
★重複を作っていない: ★「選別が効いていない（`build_request` が全件要求）」は ★既存の `G-06` が
  既に登記していた（★走査して確認）∴ ★新規登記しない。
```

---
**決めたこと**: **①`Request` は切れていない——今回の依頼の入力内容（`/api/state` の `goal`）と受理時刻（`ETR` の `ENTRY.ts`・receipt と 300µs 差）に既存の口だけで到達できた。ただし経路が `trace_key` 1段から `task_id` 経由の2段に変わり、`D-140` の口はこの経路では使われなくなった ②判定案は Last PASS = Observation / First FAIL = Ledger で、配線は3点 前進（Task/Runtime/Observation）——ただし Runtime は「task が起動したから走った」のではなく同居である ③次の1件は `Ledger`（生出力への到達）。A-3 をどのファイルで直すかは `webui.py` 側を推すが、順番は MGR が決める。★`webui.py:661` を読んでいながら prefix が外れることを予見しなかったのは私の設計ミスである。**
