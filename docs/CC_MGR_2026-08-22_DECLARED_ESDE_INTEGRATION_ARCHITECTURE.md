# declared — `ESDE_INTEGRATION_ARCHITECTURE`（実測・調査のみ／★実装しない）

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3` / **ESDE 正本 v0.1**)
Taka 指示「MGR指示 — ESDE統合準備 / Integration Architecture」(2026-08-22)に対する**最初の成果物**。
**★コードは1行も変えていない。★新しい Manager / Worker / 台帳 / ID / 経路 / state を1つも作っていない。**
測ったHEAD: twoder `8b64b1f` / dev-workcell `68c3b4c` / egl `5babb3a`

---

## 0. ★先に2つ訂正する

### 訂正1 ―― 「ESDE という語が衝突している」は**誤り**

私は調査の途中で「`esde_stream` / `formal_esde_operators` / `run_esde_task` / 正本 が別物を指す＝CONFLICT」と書いた。
**Taka の説明（2026-08-22）で誤りと分かった。**逐語の趣旨：

> ESDE は**アリズム哲学を実践的に応用するための具体的な手順**。先行研究として NLP Like な **ESDE Language** と
> 注意センターなどを扱う **ESDE Genesis** がある。どちらも ESDE 原理で作られているので ESDE であることに変わりはない。
> **2DER ですら原理的には ESDE の論理がいたるところに散りばめられている。**
> 今回提案しているのは**より具体的で実践的な ESDE の利用**。

∴ **同一原理の複数世代が同居しているのであって、CONFLICT ではない。**
残る問題は語の衝突ではなく、**「機械がどの世代の成果物かを区別する規則が無い」**という点だけ。

### 訂正2 ―― 私の**探索範囲が狭かった**

本日ここまでの調査は**すべて `ds rri egl dev-workcell twoder` の5 repo に限っていた**。
実測: **`/home/takasan/esde/ESDE-Research` が範囲外だった**（**44GB / 43,069 files** ―
`csv 20,095 / json 7,601 / parquet 5,106 / py 838 / md 490 / jsonl 365`）。
構成 = `autonomy / cognition / developmental / docs / ecology / genesis / language / legacy / primitive / scripts / unified`
規模 = `primitive 13G / unified 1.2G / language 430M / genesis 33M`。
理論の正本は `docs/esde_axioms_unified.md`（`egl/experiments/formal_esde_operators.json` が
`SRC-ESDE-AXIOMS-FORMAL (esde_axioms_unified.md, frozen ea9fe6d3)` として参照している source）。

**∴ 本日までに私が書いた「無い」「0件」は、すべて5 repo に限った話である。**
**★本 declared でも `esde/ESDE-Research` の中身は調査していない（README と docs の一覧のみ）。UNVERIFIED として残す。**

---

## 1. 9項目の状態（★推測で埋めない）

| 項目 | 状態 | 実測 |
|---|---|---|
| **IDENTITY** | **PRESENT（候補あり）** | 下記 §2 |
| **CALLER** | **PRESENT（絞れた）** | 下記 §3 |
| **TIMING** | **UNVERIFIED** | Manager 側であることまでは確定。どの契機かは未確定 |
| **INPUT** | **PRESENT** | 下記 §4 |
| **OUTPUT** | **UNVERIFIED** | 正本§12 の全欄を何の形で載せるか未確定 |
| **STORAGE** | **PRESENT（候補あり）** | 下記 §5 |
| **READER** | **MISSING** | ESDE 評価結果を読む側は**現在1つも存在しない** |
| **AUTHORITY** | **UNVERIFIED** | 既存の門を通す形は在る。ESDE 結果が何を止める/進めるかは未確定 |
| **TEST** | **未定義** | 下記 §8 に計画を置く（Taka の6項目に沿う） |

---

## 2. IDENTITY ―― 既存体系を作用ベースで全件調査（★新 ID を作らない）

**探索範囲** = `ds rri egl dev-workcell twoder` の `*.py` 全件。**`esde/ESDE-Research` は含まない。**

### 既存 ID 体系と生成主体

| ID | 生成 | 決定論か |
|---|---|---|
| `TASK-2DER-` | `sha1(raw_input)[:8].upper()`（`submit.py:769,827`） | **依頼文から導出** |
| `TASK-2DER-EXP-` | `sha1(candidate_id)`（`experiment_candidate.py:114`） | 導出 |
| `TASK-2DER-AUTO-` | `sha1(item_id + ts)`（`select_and_create.py:72`） | 導出 |
| `ART-` | `sha1(repo + "\|" + relative_path)[:10]`（`artifact_registry.py:31`） | **path から導出** |
| `APPROVAL-` | `sha1(task_id\|operation_class\|action_type\|ts)[:10]`（`authority.py:151`） | 導出 |
| `FN-` | `sha1(name)[:8]`（`function_table.py:register`） | **名前から導出** |
| `ITEM-2DER-EVO-####` | 手で採番（`roadmap_registry.register_item`） | 手 |
| `DE-####` | EGL 側 | 手/機械 |

### ★`axis_id` は既に占有されている

```
approve_account.py:44   rows.append({"axis_id": aid, "axes_version": "adopted", "name": name, ...})
                        → egl/structure/ACCOUNT_AXIS_NAMES.jsonl（会計科目の軸）
rri_formal.py:23        research_axis（別物）
twoder/axis_delta.py    （別物）
```

**∴ 新しく `AXIS-*` を作ると3つ目の意味になる。Taka の禁止事項どおり作らない。**

### ★私が台帳 note に書いてきた `AXIS=…` には読み手が無い

作用ベースで検索した結果、`status_note` 中の `AXIS=` 文字列を**機械が読む関数は0件**。
∴ 私が本日 20回以上書いた `AXIS=…` は**自由文だけで、機械の持ち物ではない**。
正本 §4 の言い方では **identity rule が未成立**。

### ★本命候補 ―― `twoder/function_table.py`

正本 §4「既存identityにESDE評価結果を束縛できるなら、それを優先する」に対する候補。

| 観点 | 実測 |
|---|---|
| **canonical source** | `ETRACE.PATH`（既存 event_trace）。逐語「★append-only は route_adopt と同じ器」 |
| **identity** | `function_id = "FN-" + sha1(name)[:8]` |
| **writer** | `register()` **1つだけ**。逐語「★書くのは この関数だけ(★機械で数えられる)」 |
| **uniqueness** | 名前の sha1 ∴ 同名は同 id |
| **lifecycle** | `register` ↔ **`revoke`** の**両方**。逐語「★取り消しも1行 足す(★消さない)。★読む側が最後の行を採る」 |
| **reader** | `_rows()` / `function_list()` / `function_index` / `function_table_view` / **front door `/api/control?include=function_table`**（`webui.py:1340-1344`） |
| **authority** | `A.gate_for_item("REGISTER_FUNCTION", "ITEM-2DER-EVO-0058")` を通す |
| **cross-reference** | `from_component` / `votes` / `authority_decision` / `registered_by`（**認証済み識別**・逐語「★body から詐称できない」） |
| **設計方針の逐語** | 「★新台帳0・口0増・新しい承認工程0」 |
| **現在の分母** | 記録 **170件** / `by_origin = {hand: 8, machine: 1}` |
| **逐語の注意** | 「★hand の8語は module の定数=★記録から来ていない(★実績と読まない)」 |

**∴ `register↔revoke` の対称性・単一 writer・front door までの reader・authority 通過・既存の器 が
すべて揃っている既存体系は、私が調べた範囲では これ1つだけ。**

**★但し ESTABLISHED にしない。** 欄が ESDE 評価結果（正本§12 の13欄）を載せられるかは **UNVERIFIED**。

### ★DEAD_APPROACH の門との関係（実測）

`submit.py:360` に **DEAD-APPROACH HARD GUARD が routing の前**に在る。
判定は `failure_memory._mentions_dead_revival(raw, rec)` = **`match_keywords` 一致 かつ `_LIVE_VERBS` 一致**。

```
DEAD_APPROACH 5件。うち1件が AFE/Formal structural operators（ref = DE-0103 / DE-0104）
  match_keywords = ['afe', 'run_afe', 'formal esde', 'structural operator', 'aruism operator']
_LIVE_VERBS = ['live','detector','検出器','常時','always-on','always on','wire','組み込','復活',
               'reconnect','再接続','revive','有効化']
```

**★判定器に直接聞いた結果（台帳は読んでいない）**

| 依頼文 | BLOCK |
|---|---|
| 「ESDE の評価を 2DER の内部で使えるようにしてほしい」 | **0件（通る）** |
| 「ESDE を live detector として動かしてほしい」 | **0件（通る）** |
| 「構造の欠損を継続的に見つける仕組みを…」 | 0件 |
| 「**formal ESDE** の operator を **live で復活**させてほしい」 | **1件（正しく止まる）** |

**∴ 今回の統合は DEAD_APPROACH に当たらない。★但し境界は1語（`formal esde`）。**
**★依頼文に "formal" を入れると止まる。**
（補足：`TASK-2DER-D7977C1A` の `egl_source_refs` は **`["DE-0103","DE-0104"]`** ―― あの task は
**この門の部分文字列誤爆を直すもの**だった。同じ門に繋がっている。）

---

## 3. CALLER ―― 既存経路から逆算（★先に場所を決めない）

**`twoder-route-worker.service`（稼働中）が既に構造を継続観測している。**その module 冒頭の逐語：

> ★一文定義: 2DER で実際に何がどこからどこへ通ったかを、**証拠付きで観測・更新する機構**。
>
> **★これが判断しないもの（★正本 §3）**
> 　期待された機能か ／ 結果が正しいか ／ この機能は必要か ／ **他機能との連動が正しいか** ／ 全体目的との整合性
> 　―― どれも **Manager の仕事**。ここは「実際に何が起きたか」だけを扱う。
>
> **★正本 §12 逐語「Route Worker に Manager の責務を追加しない」**

**∴ ESDE 評価が扱う対象（連動性・整合性・必要性）は、正本が明示的に「Route Worker の仕事ではない」と
切り分けている。CALLER は Manager 側。★Route Worker に足すのは明示的に禁止されている。**

**Route Worker は CALLER ではなく INPUT の供給者。**

---

## 4. INPUT ―― 既存の証拠源（★新しい raw evidence 台帳を作らない）

| 源 | 取り方 | 状態 |
|---|---|---|
| 経路表 | `route_worker` が維持 | PRESENT |
| event_trace | `ds/etrace`（`ETRACE.PATH`） | PRESENT |
| 台帳 | front door `GET /api/resolve` / `/api/ledgers`（**直読は禁止**・本日1回・累計54回 拒否された） | PRESENT |
| 実行の痕跡 | `GET /api/etrace?task_id=` | PRESENT |
| 制御面 | `GET /api/control` 既定の欄 = `roadmap / forecast / recent_de / recent_chg / interventions / completion / offramp_flags / resolvable` ／ `include=` で `edge_measures / observed_edges / function_table / function_index / function_first` | PRESENT |
| task / artifact / authority | `/api/state` / `artifact_registry` / `authority` | PRESENT |
| **ESDE 先行体系** | `esde/ESDE-Research`（44GB） | **★UNVERIFIED（未調査）** |

---

## 5. STORAGE ―― 候補は既存の器

正本 §6 と Taka §6 に従い、**ESDE 専用の raw evidence 台帳は作らない**。
保存が要るのは「**導出された評価結果 ＋ evidence reference ＋ evaluation identity**」のみ。

**候補**: `function_table` と同じ器（`ETRACE.PATH` への append）。理由 = 単一 writer・append-only・
front door に reader が既に在る・authority を通す・**新台帳0**。

**★但し確定しない。** 欄が正本§12 の13欄を載せられるかが **UNVERIFIED**。

---

## 6. READER ―― **MISSING**

**ESDE 評価結果を読む側は、現在1つも存在しない。**
Taka §6 逐語「**writerあり / readerなし の構造を作ってはならない**」。
∴ **writer を決める前に reader を決める必要がある。**

reader の候補（実測で在るもの）:
- `manager_v0` の巡回（`whose_turn` / `tick` の判断材料）
- front door の `/api/control`（既に `function_table` を返している）
- 状況表（`2der_status.sh`）

**どれを reader にするかは未確定 ＝ UNVERIFIED。**

---

## 7. AUTHORITY ―― **UNVERIFIED**

既存の形は在る（`A.gate_for_item(...)` を通してから1行書く＝`function_table.register` と同じ作法）。
**ESDE 結果が何を止める / 進めるかは未確定。**

Taka §9 逐語「**Claude の判断そのものをシステムの authority にしない**」
正本 §7「層を飛び越えて結果だけ作る実装は、機能が動いても violation」
∴ **初期は「止めない・記録するだけ」から始めるのが層を破らない**（これは私の見立て。確定ではない）。

---

## 8. TEST 計画（Taka の6項目に沿う・★実装前に定義）

| # | 試験 | 材料（★すべて実在する既知欠陥から取る） |
|---|---|---|
| 1 | **既知欠陥 再検出** | `ENERGIZATION_ADJUDICATION` writer 0 ／ `principal_of` 呼び手0 ／ `merge_records` 呼び手0 ／ `run_until_barrier.py` 呼び手0 ／ `bridge_minter` import 不能 ／ `GATE` が `_machine_registry` に無い |
| 2 | **陰性対照** | `function_table.register↔revoke`（対称性が在る）／ `apply_cycle` の `from twoder import patch_bridge`（正しい import）を CONFLICT にしないこと |
| 3 | **非干渉** | 評価を足しても既存 task の進行・authority・completion が変わらないこと（before/after で DW events と state 分布を比較） |
| 4 | **証拠追跡** | 評価結果から元の event / task / artifact へ機械的に戻れること |
| 5 | **版・identity** | 古い正本（例：正本§13 の記述）や未登記 artifact を判定材料に混入させないこと |
| 6 | **片側欠損** | writer だけ / reader だけ を意図的に作り、SYMMETRY が検出すること |

**★1の材料は全部、本日 実測で確定した実在の欠損。作り話ではない。**

---

## 9. 既存1〜18経路との関係

**未確定（UNVERIFIED）。** Taka §5 の指示どおり「1〜18のどこかに入る」と仮定していない。
`§3` で CALLER が Manager 側と絞れたが、**Manager のどの契機か**は決めていない。
候補（実測で在るもの・優先順位は付けない）:
`record_stages` の後 ／ `receive_finished` の後 ／ `PROPOSE_COMPLETE` の前 ／ 独立した非同期 ／ 複数地点。

---

## 10. Qwen / 機械 / Claude の役割分離（Taka §8 §9）

```
LLM(Qwen)   仮説・候補・異常の発見のみ。★文章そのものを証拠にしない
2DER(機械)  全件取得・分母・照合・identity 確認・証拠化。★確定はここ
Claude      当面の上級監査。★判断そのものを authority にしない
            ★正解候補への昇格は「独立した複数主体の結果が一致し、参照した機械証拠まで一致した」時のみ
```

**★本日の実例**: 監査（Claude）は本日 **自分の誤りを3件 訂正した**（`build_plan` 副作用0／`run_until_barrier` の機構／
欠損 ID の帰属）。私（MGR）も **6件以上**訂正した。∴ **Claude の出力を無条件に正解として保存してはならない**
という Taka の指示は、本日の実測で裏付けられている。

---

## 11. MISSING / CONFLICT / UNVERIFIED 一覧

```
MISSING     ESDE_RESULT_HAS_NO_READER          結果を読む側が存在しない
            AXIS_STRING_HAS_NO_MACHINE_READER  台帳 note の AXIS= を読む関数 0件

CONFLICT    （★無し。訂正1のとおり「ESDE の語の衝突」は誤りだった）

UNVERIFIED  TIMING                             Manager のどの契機か
            OUTPUT                             正本§12 の13欄を何の形で載せるか
            AUTHORITY_EFFECT                   ESDE 結果が何を止める/進めるか
            FUNCTION_TABLE_FIELD_FIT           既存の欄が13欄を載せられるか
            ESDE_RESEARCH_ASSETS_UNSURVEYED    esde/ESDE-Research(44GB) を調査していない
            ROUTE_1_18_ATTACHMENT              1〜18経路との接続点
```

---

## 12. 実装するとした場合の最小差分候補（★実装しない・候補のみ）

**現時点で提示できる候補は無い。** 理由 ―― **READER が MISSING** であり、
Taka §6「writer あり / reader なし の構造を作ってはならない」に反するため、
**writer 側の差分を先に書くこと自体ができない。**

∴ **次に確定すべきは READER。** それが決まるまで差分候補を出さない。

---

## 13. DECISION

**DESIGN_HOLD。**
Taka §12 の GO 条件12件のうち、満たしたのは **IDENTITY（候補確定）/ CALLER（絞り込み）/ INPUT / STORAGE（候補）/ TEST 計画** の5件。
**未達 = TIMING / OUTPUT / READER（MISSING）/ AUTHORITY 境界 / writer-reader 両方 / 経路接続の説明 / 監査の全欄検査。**

**★実装しない。★新しい Manager / Worker / 台帳 / ID / 経路 / state を1つも作っていない。**
