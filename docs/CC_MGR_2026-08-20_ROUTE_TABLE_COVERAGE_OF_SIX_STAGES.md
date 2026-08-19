# 宛: Taka ―― **経路表は 6段を ★表現しきれない ―― ★不足した 表現だけを 特定（★実装 0）**

**2026-08-20 07:2x ／ ★`contract_from_plan` の 個別修正は ★先行させていない（★ご指示どおり）**
**★実装 0 ／ ★実 repo 書き込み 0 ／ ★SELF_DEV_TOKEN = ★5/5**

---

## 1. ★経路表 `ROUTE` の 実体（★実測）

```
★行数 = ★18（★S01〜S18）
★1行の 欄（★14個）= id / from / to / ★sends / ★returns / component / function / phase /
                     ★require_nonnull / ★fails_as / handoff / receipt / actor / ★actor_confirmed
★★＝ ★『入力』『出力』『制約』『次段』『接続されているか』は ★★欄と して 在る。
```

## 2. ★★6段の 被覆（★機械の 突き合わせ・★実測）

| 段 | ROUTE に 在るか | 実測 |
|---|---|---|
| **GENERATE** | **★在る** | `S13` DW `_append_event` → `generate_via_runner.generate` |
| **contract_from_plan** | **★★無い** | ★文字列一致 = ★False（★18行の どこにも 出ない） |
| **runner** | **★在る** | `S14` RUNNER `run_minimal_slice` ／ `S15` `run_test` |
| **artifact** | **★在る**（★語として） | `S13.returns = ["artifact"]` |
| **diff** | **★語は 在る** | ★但し ★段としては 無い（★下記 §3） |
| **patch / energize** | **★★無い** | `patch_bridge` `energize` `apply_cycle` `bridge_minter` = ★★すべて False |

```
★★＝ ★6段の うち ★★3段（contract_from_plan ／ diff ／ patch・energize）が
   ★経路表に ★存在しない。
★★＝ ★今回の 障害（`target_file="impl.py"` 固定）は ★★経路表に 載っていない 段で 起きた。
★★∴ ★機械が 事前に 認識する ことは ★★できなかった（★私が コードを 直読して 初めて 判った）。
```

## 3. ★★載っている 段でも 表現が 足りない（★実例）

**★`S13` / `S14` の 実物（★逐語）:**

```
S13 sends=["contract"] returns=["artifact"] require_nonnull=[] fails_as=["結果だけ残り中が残らない"]
S14 sends=["packet"]   returns=★["impl.py"] require_nonnull=["artifact_len"]
    fails_as=["artifact_len=0/None","result=FAILED","生成が空"]
```

```
★★`S14.returns` に ★`"impl.py"` と ★書いて ある ―― ★★今回の 制約は ★表に 出ていた。
★★但し ―― ★それは ★『返り値の 名前』と して 書かれている だけで、
   ★★『★他の file は 返せない』という ★制約と しては ★書かれていない。
★★∴ ★読めば 気づける が ★★機械が 『制約』と して 引ける 形では ない。
★★＝ ★今回の 型「★在る ／ 引けない」。
```

## 4. ★★不足している 表現（★4つ・★これ以上 増やさない）

```
★★① ★段が 無い ―― `contract_from_plan` ／ `diff` ／ `patch`・`energize` の 3段
   （★`allowed_files` `target_file` も ★1文字も 出ない）
★★② ★『対象範囲』の 欄が 無い
   ―― ★どの file / どの repo を 触れるかを ★表す 欄が ★14欄の 中に ★無い。
   （★`returns` に file 名が 紛れている のが ★現状 ―― ★§3）
★★③ ★『制約』が ★`fails_as`（★失敗の 現れ方）しか 無い
   ―― ★『何を 受け付けないか』（★事前条件）を ★表す 欄が 無い。
   （★`require_nonnull` は ★『空で ない こと』のみ ＝ ★値の 許可集合は 表せない）
★★④ ★『接続されているか』が ★`actor_confirmed`（★真偽）だけ
   ―― ★`S13` `S14` とも ★`true` だが ★★実際には ★`patch`・`energize` へは ★繋がっていない
     （★`mint_real_energize` の 呼び手 = ★回帰試験 のみ ＝ ★2026-08-20 実測）。
   ★★＝ ★`actor_confirmed=true` は ★『その 段の 役が 居る』こと であって
     ★『次段へ 繋がっている』ことでは ない。
```

## 5. ★★機能表について（★実測）

```
★`/api/control` の 欄 = completion / forecast / generated_from / include / interventions /
   offramp_flags / read_only / recent_chg / recent_de / resolvable / roadmap
★★＝ ★『機能の 一覧』（★能力・入力・出力・制約・次段）を ★持つ 欄は ★★無い。
★★＝ ★機能表は ★現時点では ★存在しない（★経路表 18行が ★それに 最も 近い）。
```

## 6. ★★結論（★ご指示の 二択に 対して）

```
★ご指示 =「表現できるなら 機能表へ 機械的に 反映 ／ できないなら 不足した 表現だけを 特定」
★★→ ★★表現できない。
★★∴ ★§4 の ★4つが ★今回 不足した 表現。
★★∴ ★`contract_from_plan` の 個別修正は ★先行させない（★ご指示どおり ★していません）。
```

## 7. ★★次回 同型を 事前に 認識する ために 要る もの（★定義のみ・★実装 0）

```
★★『対象範囲』と『事前条件』を ★段の 欄と して 持つ こと。
   ―― ★今回の 制約は ★『`contract_from_plan` の 事前条件 = target_file ∈ {impl.py}』
     と ★1行で 書ける（★書ければ ★PLAN 前に 機械が 引ける）。
★★『接続されているか』を ★役の 有無では なく ★呼び手の 有無で 持つ こと。
   ―― ★今回 `patch`・`energize` は ★呼び手 0 だった が ★表には 出ていなかった。
★★＝ ★増やす 欄は ★2つ（★対象範囲 ／ 事前条件）＋ ★1つの 意味の 直し（★接続）。
★★但し ―― ★経路表 自体を 変えるのは ★設計判断 ∴ ★私は していません。
```

## 8. ★していないこと

```
★`contract_from_plan` 未変更 ／ `generate_via_runner` 未変更 ／ `build_planner` 未変更
★経路表 未変更 ／ 機能表 未作成 ／ 許可リスト 未作成 ／ 投入 0 ／ 実装 0
★実 repo 書き込み 0（★`twoder` HEAD `24c649a` 不変）／ ★常駐 停止のまま
★★外部 diff の 本番生成 ★未実施 ／ ★`D7977C1A` は ★`CREATED` の まま
★SELF_DEV_TOKEN = ★5/5
```
