# 宛: Taka ―― **恒久的な 自己修復ルート: ★既存構造で どこまで 作れるか（★調査・★実装 0）**

**2026-08-20 06:2x ／ ★実装 0 ／ ★bootstrap 未実行 ／ ★guard 変更 0 ／ ★failure memory 変更 0**
**★SELF_DEV_TOKEN = ★5/5 ／ ★HEAD = `24c649a`（不変）／ ★常駐 停止のまま**

---

## 1. ★★self-block 判定 ―― **★既存記録で ★半分しか 取れない**

**★BLOCK 応答が 実際に 残す 欄（★実測・★同じ 依頼を 投げて 確認）:**

| 問い | 既存で 取れるか | 実物 |
|---|---|---|
| その 依頼を BLOCK した component は 何か | **★取れる** | ★`actor_role = "GUARD"` ／ `guard_block[0].failure_id = "DEAD-afe-detector"` ／ `note`（CLOSED-NEGATIVE 全文） |
| task 生成前の BLOCK か、生成後の 停止か | **★取れる** | ★`task_id = null` ／ `dw_task_create_result = null` ／ `blocked = true` |
| 同じ failure が 修理依頼にも 再発しているか | **★取れる** | ★`failure_memory_match[].failure_id` を 比べれば よい |
| **修理対象の component は 何か** | **★★取れない** | ★`target` / `component` / `subject` / `scope` / `repo` / `file` を 含む 欄 = ★★0件（★応答21欄を 走査） |
| **`target_component == blocking_component`** | **★★取れない** | ★左辺が 無い ∴ ★比較できない |

```
★★＝ ★『誰が 止めたか』『いつ 止まったか』『再発か』は ★既存で 機械的に 取れる。
★★＝ ★『何を 直そうと していたか』だけが ★どこにも 無い（★依頼文の 散文の 中だけ）。
★★∴ ★self-block の 自動判定は ★★『対象の 記録』が 1つ 足りない ため 成立しない。
   （★新しい 判定器 以前に ★材料が 欠けている）
```

## 2. ★bootstrap の 可否 ―― **★条件は 実証されている**

**★Taka が 定めた 条件（逐語）:**
> 「target_component == blocking_component 等により、通常入口自身が修理依頼を
>  task化前に拒否していることが実証された場合のみ」

**★実証（★機械的に 取れた もの・★2回）:**

```
★① ★task 化前の 拒否 = ★`task_id = null` ／ `dw_task_create_result = null`（★2回とも）
★② ★止めた のは ★GUARD（`actor_role = "GUARD"`）
★③ ★止めた 根拠 = ★`DEAD-afe-detector` の ★部分文字列一致
   （★実測: `safety` の 中の `afe` ／ `deliverable` の 中の `live`）
★④ ★修理対象 = ★その ★同じ 一致規則（★依頼文で 名指し ／ ★但し ★欄では ない ―― §1）
★★∴ ★①②③ は ★機械の 記録で 実証済み。★④だけ ★散文（★人が 読む 形）。
```

```
★★＝ ★『通常入口 自身が 修理依頼を task 化前に 拒否している』は ★★実証されている。
★★＝ ★但し ★『対象＝阻害者』の ★機械的な 同一判定は ★§1 の 欠落の ため ★できない。
★★∴ ★bootstrap の 発動条件を ★どこまで 厳密に 求めるかは ★Taka の 裁定（★私は 決めない）。
```

## 3. ★★Front Door より 後段の 既存 task 生成口（★実在）

```
★`dw.workcell.create_task(task_id, project_id, goal, knowledge_packet, ts,
                          manager_identity, contract=None)`
   ＝ ★front door（`submit.py:659` / `:696 付近`）が ★呼んでいる のと ★同じ 関数。
★★＝ ★『後段の 既存正規 task 生成口』は ★★実在する（★新しい 口を 作る 必要は 無い）。
```

**★★但し ―― ★bootstrap には ★満たすべき 条件が 在る（★実測）:**

```
★`twoder/dispatch_provenance.py`:
   REQUIRED_RESOLVABLE = ★('dw_task_id', 'ds_input_id', 'rri_request_id', 'rri_intent_id')
   REQUIRED_PRESENT    = ★('trace_id',)
★`build_planner.validate_plan` は ★`verify_provenance=True` で これを 検査する
   ∴ ★provenance が 揃わない と ★PLAN が 記録されない（★fail-closed）。
★★＝ ★bootstrap で task を 作る 場合も ★この 4つの id を ★正規に 用意する 必要が ある。
★★＝ ★『適当な 値を 入れて 通す』は ★捏造 ∴ ★できない（★やりません）。
```

## 4. ★★恒久ルートの 各段が 既存で 埋まるか（★一覧）

| 段 | 既存で 在るか | 実物 / 不足 |
|---|---|---|
| control-plane fault の 検知 | **★部分的** | ★`guard_block` / `actor_role=GUARD` / `blocked` は 在る ／ ★『どの component の 障害か』の 欄は 無い |
| self-block / self-reference 検知 | **★不可** | ★§1 の とおり ★対象の 記録が 無い |
| limited maintenance entry | **★素材は 在る** | ★`W.create_task`（★front door と 同じ 関数）／ ★provenance 4件が 要る（§3） |
| 2DER が 修理 | **★在る** | ★通常の PLAN / GENERATE / TEST / AUDIT |
| rollback 確認 | **★在る** | ★`patch_bridge` / `bridge_reconciler` / `rollback_outcome`（★今夜 実走で 確認済み） |
| 通常 Front Door で 再実走 | **★在る** | ★`/api/submit` |
| 正常化の 確認 | **★在る** | ★同じ 依頼が ★BLOCK されない ことを 見る |
| maintenance 終了 | **★語が 無い** | ★`CONTROL_PLANE_BOOTSTRAP` に 相当する 記録語は ★存在しない |

## 5. ★★最小の 不足（★2つ・★これ以上 増やさない）

```
★★① ★『この 依頼は 何を 直そうと しているか』を 記録する 欄が 無い
   ＝ ★self-block の 機械判定が ★原理的に できない（★比較の 左辺が 無い）
★★② ★`CONTROL_PLANE_BOOTSTRAP` を ★記録する 語が 無い
   ＝ ★例外を 使った ことを ★後から 数えられない（★『裏口』に なる 危険）
★（★③ provenance 4件は ★不足では なく ★★満たすべき 条件 ―― ★既存の 口が 在る）
```

## 6. ★★私の 判断（★実行していない ／ ★裁定を 仰ぐ）

```
★Taka の 条件は ★①②③ の 範囲で ★実証されている（§2）。
★★∴ ★bootstrap を ★1件 使う 資格は ★満たしている と 読める。
★★但し ―― ★§5 ② の とおり ★『bootstrap を 使った』ことを 記録する 語が 無い。
   ＝ ★いま 実行すると ★★記録に 残らない 例外に なる（★Taka の 制約
     「bootstrap自体は記録する」を ★満たせない）。
★★∴ ★★私は ★まだ 実行していません。
```

## 7. ★★上申（★2つ・★私は 案を 出しません）

```
★★(1) ★bootstrap を ★記録する 語が 無い（§5②）。
      ★『記録する』を どう 満たすか ―― ★既存の どれかで 代用するか、
      ★1語だけ 足すか、★別の 形か。★裁定が 要る。
★★(2) ★self-block の 機械判定は ★対象の 記録が 無い ため ★成立しない（§1・§5①）。
      ★これを 先に 直すか、★今回は ★人が 読む 実証（§2④）で 進めるか。★裁定が 要る。
```

## 8. ★していないこと

```
★実装 0 ／ 修正 0 ／ ★bootstrap 未実行 ／ ★task 生成 0
★guard 変更 0 ／ failure memory 変更 0 ／ BLOCK 解除 0 ／ 迂回 0 ／ 再投入 0
★新しい 権限 0 ／ 新しい 台帳 0 ／ 新しい 判定器 0
★実 repo 書き込み 0 ／ DISPOSE 0 ／ 常駐 再開 0 ／ SELF_DEV_TOKEN = ★5/5
★★2件（GUARD / CURRENT）を ★1つに まとめていない
```
