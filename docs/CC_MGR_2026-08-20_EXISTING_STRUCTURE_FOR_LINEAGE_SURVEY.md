# 宛: Taka ―― **由来と 還流と 階層を ★既存構造で どこまで 表せるか（★調査のみ・★実装 0）**

**2026-08-20 03:1x ／ ★新台帳 0 ／ 分類器 0 ／ 関数 0 ／ 欄 0 ／ 配線 0 ／ ESDE 未実装**
**★SELF_DEV_TOKEN = ★5/5 ／ ★常駐 停止のまま**

---

## 0. 数え方（★先に 宣言）

```
★材料 = ★既存の task・記録・経路・停止理由 だけ
★実例 = ★`E8AAEA8C → 070D062A`（★停止 task → 修理 task）
       ★`B → A36B3881`（★上位欠陥 → その 修理 task）
★『在る』= ★実物の 記録に ★欄として 出た もの だけ
★『無い』= ★探した 範囲を 明記した うえで ★出なかった もの
```

## 1. ★★一覧（★5つの 観点 × ★在る/無い）

| 観点 | 既存で 表せるか | ★実物の 所在（★出た 欄） | 不足 |
|---|---|---|---|
| **parent（何から 発生したか）** | **★部分的** | ★`CREATE.payload.goal` の ★本文に 親 task の id が 文字列で 入る（★実測: `E8AAEA8C`→`070D062A` で ★双方向に 出た） | ★★**欄が 無い**。★本文の 文字列 ∴ ★機械が 引けない |
| **affects（何へ 還流すべきか）** | **★無い** | ★該当する 欄 = ★0（★`twoder/*.py` `dw/*.py` を 語で 走査） | ★★**表現手段が 無い** |
| **hierarchy（TASK/COMPONENT/PIPELINE/SYSTEM）** | **★無い** | ★`FINDING_CATEGORIES` は ★13語 あるが ★★すべて 欠陥の 種類（`dead_guard` 等）＝ ★階層では ない | ★★**階層の 語彙が 無い** |
| **evidence（証拠）** | **★在る** | ★`provenance`（8欄: `ds_input_id` `dw_task_id` `egl_source_refs` `etrace_run_id` `measured_state` `rri_intent_id` `rri_request_id` `trace_id`）／ ★`knowledge_packet`（`A36B3881` は 12欄: `admitted_claims` `open_gaps` `source_trace` 等） | ★★**task 間の 関係は 指せない**（★指すのは ★DS/RRI/EGL の 記録） |
| **disposition（処分）** | **★在る** | ★`DISPOSITION_VERDICTS = {ACCEPTED, PARTIAL, REJECTED, REMAINS}` ／ `defect_class` ／ `tier` ／ `basis` | ★★**『子の 成果で 解消した』を 表す 語が 無い**（★4語は すべて ★その finding 自体の 判定） |

## 2. ★台帳側（ITEM）には **★依存の 欄が 在る**

```
★`/api/resolve?id=ITEM-2DER-EVO-0019` の `record` 欄（★16欄・実物）:
   acceptance / artifact_ids / authority / change_ids / ★depends_on / description /
   evidence_de_ids / item_id / kind / phase_id / registered_at / roadmap_id /
   status / status_note / ★task_ids / title

★★`depends_on` = ★["ITEM-2DER-EVO-0016", "ITEM-2DER-EVO-0017"]（★実データ）
★★`task_ids`   = ★ITEM に 属する task の 一覧（★今夜の 分も 入っている）
```

```
★★＝ ★『ITEM 同士の 依存』は ★既に 表せる。
★★＝ ★『ITEM ↔ TASK の 所属』も ★既に 表せる。
★★但し ―― ★★『TASK ↔ TASK』の 関係は ★どちらの 欄でも 表せない。
```

## 3. ★★実例で 確かめた こと

```
★`E8AAEA8C` の goal 本文に ★task id が 入っている = ★True
★`070D062A` の goal 本文に ★親 `E8AAEA8C` が 出る  = ★True
★`A36B3881` の goal 本文に ★task id が 入っている = ★True
★★∴ ★親子は ★『私が goal の 本文に 書いた から』★読める だけ。
★★∴ ★機械が 作った 関係では ない ／ ★欄でも ない ∴ ★機械は 辿れない。
★（★＝ 今夜 5回 出た 「作れる ／ 繋がらない」の ★記録側の 正体）
```

## 4. ★近いが 別物だった もの（★誤用を 防ぐ ため 明記）

```
★`artifact_registry.supersedes`      … ★成果物の 版の 置き換え（★task 間では ない）
★`knowledge_packet.supersedes_packet_id` … ★知識 packet の 版（★task 間では ない）
★`management_packet.derived_from`    … ★`ART-…`（★成果物 id）から 導いた もの
★`management_packet.affected_artifact_ids` … ★CHANGE が 触った 成果物（★task では ない）
★★＝ ★どれも 『成果物 / packet の 系譜』であって ★『task の 系譜』では ない。
```

## 5. ★★確定した 不足（★4つ・★これ以上は 作らない）

```
★★① ★TASK → TASK の 親子（`parent` / `derived_from`）を 表す ★欄が 無い
      （★いまは ★goal 本文の 文字列 ＝ ★機械が 引けない）
★★② ★『この 成果は どの 停止へ 還流すべきか』（`affects`）を 表す ★手段が 無い
★★③ ★問題が ★TASK / COMPONENT / PIPELINE / SYSTEM の ★どの 階層かを 表す ★語彙が 無い
      （★`FINDING_CATEGORIES` は ★欠陥の 種類 ∴ ★階層では ない）
★★④ ★DISPOSE に ★『子の 成果に よって 解消した』を 表す ★語が 無い
      （★4語 = ACCEPTED / PARTIAL / REJECTED / REMAINS ★すべて その finding 自体の 判定）
```

## 6. ★★既に 在る 部品（★作らずに 使える 見込みの もの）

```
★`ITEM.depends_on`     … ★ITEM 同士の 依存（★実データ 2件）
★`ITEM.task_ids`       … ★ITEM ↔ TASK の 所属（★今夜の task も 入る）
★`provenance` 8欄       … ★DS / RRI / EGL / etrace への 参照（★全 task に 在る）
★`knowledge_packet`    … ★`open_gaps` `source_trace` `admitted_claims` 等（★task に よって 欄数が 違う）
★`DISPOSITION_VERDICTS`… ★4語（★意味を 変えずに 使える）
★★＝ ★①②③④ を 埋める 材料の うち、★『ITEM 経由で TASK を 束ねる』道は ★既に 在る。
   （★但し ★TASK 同士を 直接 結ぶ 道は 無い ―― ★上の 不足①）
```

## 7. ★探した 範囲（★『無い』の 根拠）

```
★走査した 場所 = `/home/takasan/twoder/*.py` ／ `/home/takasan/dev-workcell/dw/*.py`
★探した 語 = parent_task / parent_id / derived_from / blocks / affects / supersedes / child_task
             / layer / tier / scope_level / hierarchy
★当たった file = 6本 ―― ★用法を 1本ずつ 確認し ★§4 の とおり ★すべて 別物と 判定
★台帳側 = `/api/resolve` の `record` 16欄を 実データで 確認
★★推測で 埋めた 欄は ★1つも 無い
```

## 8. ★していないこと

```
★新台帳 0 ／ 分類器 0 ／ 関数 0 ／ 欄 0 ／ 配線 0 ／ ★ESDE 未実装
★A〜E の 個別修正 0（★B の ブートストラップは ★Taka の 別許可で 既に 実施済み・別件）
★実 repo 書き込み 0 ／ 常駐 停止のまま ／ DISPOSE 0（★滞留 2件は 未接触）
★SELF_DEV_TOKEN = ★5/5
```
