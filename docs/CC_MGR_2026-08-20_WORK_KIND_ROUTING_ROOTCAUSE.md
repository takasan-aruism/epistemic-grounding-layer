# 宛: Taka ―― **なぜ 7回 起きたか ―― ★仕事の 種類と 納品形式が 同一視されている**

**2026-08-20 05:5x ／ ★MGR 自身の 調査 ／ ★実装 0 ／ ★投入 0 ／ ★既存コード 変更 0**
**★SELF_DEV_TOKEN = ★5/5 ／ ★常駐 停止のまま ／ ★DISPOSE 0**

---

## 0. ★入口が 持つ 語（★正本・逐語）

```
★`rri/rri/request_type.py:17`
REQUEST_TYPES = ["OBSERVE_CURRENT_STATE", "BUILD_CAPABILITY", "MODIFY_EXISTING",
                 "RESUME_PRIOR", "DECIDE", "OTHER"]
```

**★Taka の 7種別との 対応（★実測）:**

| Taka の 種別 | 入口の 語 | 判定 |
|---|---|---|
| OBSERVE | `OBSERVE_CURRENT_STATE` | ★在る |
| **INVESTIGATE** | **★同じ 語に 吸収**（逐語「find out / inspect / ★investigate / check the CURRENT state」） | **★独立して 無い** |
| DECIDE | `DECIDE` | ★在る |
| **DESIGN** | ― | **★語が 無い** |
| IMPLEMENT | `BUILD_CAPABILITY` / `MODIFY_EXISTING` | ★在る（★2語） |
| **VERIFY** | ― | **★語が 無い** |
| **REPORT** | ― | **★語が 無い** |

```
★★＝ ★7種別の うち ★入口で 独立して 分類できるのは ★3つだけ（OBSERVE / DECIDE / IMPLEMENT）。
★★＝ ★INVESTIGATE・DESIGN・VERIFY・REPORT は ★入口に 存在しない。
```

## 1. ★★経路（★submit.py の 実物・分岐の 順に）

```
★RRI_INTENT_HOLD  (:485-491)  … `stops_before_action` かつ strategy が PREMISE_PROBE/DEFER
                                 → ★`DW_TASK_ID = None` ／ ★return（★task を 作らない）
★RUNTIME_INSPECTION (:601)    … `request_type == "OBSERVE_CURRENT_STATE"` または
                                 (needs_current かつ egl_empty)
                                 → 読み取り観測を 実行し EGL へ ingest
                                 → ★★:659 `W.create_task(_obs_task, …)` ＝ ★★DW task を 作る
★DW_IMPLEMENTATION (:693-696) … BUILD_CAPABILITY / MODIFY_EXISTING
                                 → ★:696 で task id を 作り ★DW task を 作る
★EGL_RESEARCH     (:762-768)  … ★`else:` ＝ ★DECIDE / OTHER
                                 → ★`DW_TASK_ID = None` ／ 逐語「no DW task; knowledge acquisition」
```

## 2. ★★DW の 状態機械（★正本 `dw/dispatch.py:28-39`・★全9行）

```
CREATED                  → PLAN         (MANAGER)
READY_FOR_IMPLEMENTATION → ★GENERATE    (CODING_WORKER)
READY_FOR_AUDIT          → AUDIT        (INDEPENDENT_AUDITOR)
DISPOSITION_REQUIRED     → DISPOSE      (MANAGER)
READY_FOR_REGENERATE     → ★REGENERATE  (CODING_WORKER)
READY_FOR_UPPER_REVIEW   → UPPER_REVIEW (CLAUDE_SENIOR)
JUDGE_REQUIRED           → UPPER_REVIEW (CLAUDE_SENIOR)
COMPLETE / BLOCKED       → 終端
```

```
★★＝ ★DW に 入った task の 道は ★1本しか 無い ―― ★PLAN → GENERATE → AUDIT → …
★★＝ ★『観測して 報告する』『調べて 答える』『判定する』で 完了する 状態が ★1つも 無い。
★★＝ ★COMPLETE へ 至る 唯一の 道は ★実装物を 作って 試験に 通すこと。
```

## 3. ★★★最終表（★ご指定の 形）

| 仕事種別 | 入口分類 | 実際の経路 | 正規の完了条件 | 非実装完了可能か | IMPLEMENT へ落ちる地点 | 根拠 |
|---|---|---|---|---|---|---|
| **OBSERVE** | `OBSERVE_CURRENT_STATE` | RUNTIME_INSPECTION → **★DW task 作成** | 観測は その場で EGL へ ingest される（★完了の 状態語は 無い） | **★否**（★task が 残り DW を 進む） | **★`submit.py:659` `W.create_task(_obs_task, …)`** | `submit.py:601-663` ／ `dispatch.py:29` |
| **INVESTIGATE** | ★無い（OBSERVE に 吸収） | ★OBSERVE と 同じ | ― | **★否** | ★同上 | `request_type.py:44` 逐語 |
| **DECIDE** | `DECIDE` | EGL_RESEARCH → **★task を 作らない** | ★知識取得（★逐語「no DW task」） | **★可**（★但し ★判断も 作業も 出ない） | ★落ちない（★代わりに ★何も 起きない） | `submit.py:762-768` |
| **DESIGN** | ★無い | ★語が 無い ∴ ★他の 語へ 寄る | ― | **★否** | ★分類の 時点 | `request_type.py:17` |
| **IMPLEMENT** | `BUILD_CAPABILITY` / `MODIFY_EXISTING` | DW_IMPLEMENTATION → DW task | ★試験に 通って COMPLETE | ― | ― | `submit.py:693-696` ／ `dispatch.py:30-33` |
| **VERIFY** | ★無い | ★語が 無い | ― | **★否** | ★分類の 時点 | `request_type.py:17` |
| **REPORT** | ★無い | ★語が 無い | ― | **★否** | ★分類の 時点 | `request_type.py:17` |

## 4. ★★Q6 への 回答（★なぜ 両方 起きるか）

```
★『DECIDE → EGL_RESEARCH → task_id=null』
   = ★`else:` 節（:762）＝ ★DECIDE と OTHER は ★DW へ 渡さない と ★明示的に 書かれている。
★『調査要求 → DW_IMPLEMENTATION』
   = ★入口が ★BUILD_CAPABILITY と 判定した とき。★私の 実測では
     「◯◯を 作って ほしい」と 書くと ★BUILD_CAPABILITY、
     「調べて ほしい」と 書くと ★OBSERVE_CURRENT_STATE に なった。
★★＝ ★同じ 中身でも ★動詞で 経路が 変わる。
★★＝ ★そして ★OBSERVE でも ★:659 で ★task が 作られる ∴ ★結局 DW の 1本道に 入る。
★★∴ ★『調査要求が IMPLEMENT に なる』のは ★分類の 誤りでは なく ★★DW に 非実装の 出口が 無い ため。
```

## 5. ★★Q7 への 回答 ―― **同一視されている**

```
★入口の 語（BUILD_CAPABILITY / MODIFY_EXISTING / OBSERVE_CURRENT_STATE …）は
  ★★『何を して ほしいか』と『どんな 形で 納めるか』を ★1語で 兼ねている。
★DW 側には ★納品形式の 語が ★1つしか 無い ―― ★『artifact ＋ 封印試験』。
★★∴ ★『依頼された 仕事』と『納品形式』は ★別概念として ★保持されていない。
★★∴ ★調査を 頼んでも ★納品形式が 実装物 しか 無い ので ★実装物が 出てくる。
   （★今夜 7回 ―― ★steps は 毎回 問いを 正しく 写していた。★出口だけが 1つしか 無かった）
```

## 6. ★★結論（★1つだけ）

```
★★★C ―― ★種類によって A と B が 混在する。
```

| 種別 | A/B | 理由 |
|---|---|---|
| **DECIDE** | **★A**（経路は 在る が 壊れている） | ★`EGL_RESEARCH` という ★非実装の 正規経路が ★実在する。★但し ★判断の 結果を 記録し 次へ 繋ぐ 出口が 無く、★知識取得で 終わる |
| **OBSERVE** | **★A**（経路は 在る が 接続が 壊れている） | ★観測は 実行され EGL へ ingest される（★正規経路 実在）。★但し ★:659 で ★同時に DW task も 作られ、★そちらが 1本道へ 入る |
| **INVESTIGATE** | **★B**（語が 無い） | ★入口に 独立した 語が 無く OBSERVE に 吸収 ∴ ★経路 自体が 無い |
| **DESIGN** | **★B** | ★語が 無い |
| **VERIFY** | **★B** | ★語が 無い |
| **REPORT** | **★B** | ★語が 無い |
| **IMPLEMENT** | ― | ★正常（★唯一 完了できる 種別） |

## 7. ★★最小の 一点（★原因の 特定のみ ―― ★直していません）

```
★★7回の 再現の 直接原因 = ★★`submit.py:659` ―― ★観測要求でも `W.create_task` を 呼ぶ。
   ＝ ★観測の 結果は ★既に EGL へ 入っている のに ★さらに ★DW task が 生まれ、
     ★その task は ★実装しか 出口が 無い 1本道に 入る。
★★根の 原因 = ★★DW に ★非実装の 完了状態が ★1つも 無い（`_MAP` 9行・★実測）。
★★∴ ★:659 を 塞ぐだけでは ★INVESTIGATE / DESIGN / VERIFY / REPORT は ★依然 行き先が 無い。
```

## 8. ★していないこと

```
★実装 0 ／ 修正 0 ／ 新規 TASK 投入 0 ／ sandbox 成果物 0
★新しい 欄・分類器・関数・台帳・配線 0 ／ 既存コード 変更 0
★DISPOSE 0 ／ 常駐 再開 0 ／ ★SELF_DEV_TOKEN 消費 0（★5/5）
★ITEM.acceptance 構造化案は ★保留（★追加設計していない）
★★名称検索だけで 判定していない ―― ★submit.py の 分岐 4本 と `_MAP` 9行を ★実物で 追った
```
