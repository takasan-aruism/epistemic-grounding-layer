開発者規律 確認済(v1.0)

# 【BUILD SPEC】★段2 ―― ★候補 **1件だけ** を Worker へ（★問い1のみ・★票は 再現性として 残す）

宛: IMPL ／ 発: DESIGN ／ 2026-08-12 07:55 ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **正本** §7.1 / §8 / §9 / §16 段2 ／ **MGR 指示 07:39**（6点）

**★正本 逐語**: 「★まず 1候補だけ 通す」／「★3票多数決を『真実の確定』と みなしてはならない」／「★割れた場合は 原則として 確定しない」

---

## 1. ★★1件の 選び方（★★決定論・★★LLM に 選ばせない）

```
★★上から 順に 絞る（★★絞れた時点で 止める）
   ★① `by_target` = ★`internal`
   ★② ★経路表に 無い（★`not_in_route_table`）
   ★③ ★`is_test` でない ／ ★`is_doc_snapshot` でない
   ★④ ★`cross_repo`（★repo 跨ぎ）
   ★⑤ ★★それでも 複数なら ★★★`(source 相対path, target, kind)` の ★昇順で 先頭1件

★★受入で 効かせる = ★★2回 選んで ★同じ1件（★★人が 選ばない・★毎回 同じ）
★★選ばれた1件だけ ★明細を 出す（★★821件の 一覧は 出さない＝★段1 の 約束）
```

## 2. ★★Worker へ 渡す物（★正本 §8・★★repo 全体を 読ませない）

```
★★A の source = ★import 文の ★前後 20行 ／ ★A の module docstring（★在れば）
★★B の source = ★B の module docstring（★在れば）＋ ★★先頭 40行
★★その import 行 そのもの（★★行番号つき）
★★既存の経路表 = ★★18区間の ★`from` / `to` / `sends` だけ（★★全欄を 渡さない）
★★runtime evidence = ★★`by_target_seen_in_trace` の 値（★seen / not_seen）
★★★これ以外を 渡さない（★正本 §21.4＝★Worker を 探索者に 戻さない）
```

## 3. ★★問い（★問い1のみ・★メニュー型・★自由記述させない）

```
★★「★この接続は 経路か」
   ★1 ★`ROUTE`        = ★経路である
   ★2 ★`BORROW`       = ★ただの 部品借りである
   ★3 ★`NOT_DECIDED`  = ★判断できない
★★★選択肢に 無い語が 返ったら ★★`NOT_DECIDED` に 落とす（★既存2件と 同じ作法）
★★問い2・問い3（★機能）は ★★この段で 作らない（★正本 §16 段3）
```

## 4. ★★呼び口（★★既存2件を 括る＝★MGR 指示③・★★3件目を 写さない）

```
★★`twoder/menu_vote.py`（★新規1本）に ★共通形を 括る
   ★`ask(memo, menu, prompt_builder, seeds=(0,1,2))` →
     ★{votes[], final, disagreement, model, prompt_version, input_hash}
   ―― ★★中身は ★`annotate_gate` / `account_gate` に ★既に 在る形を そのまま
      （★3-seed 並列 ／ ★多数決＝全会一致に しない ／ ★メニュー外は `NOT_DECIDED` ／
        ★票が 割れたら `NOT_DECIDED`）
★★★既存2件を ★この関数へ 乗せ替える（★★呼び手0件の 部品を 作らない）
★★★退行の検査 = ★`annotate_gate` / `account_gate` の 既存試験が ★★通ること（★名前を 書く）
```

## 5. ★★走らせる場所（★★MGR 指示①＝★`/api/control` の 中で LLM を 走らせない）

```
★★実行 = ★★Claude(IMPL) が ★1回 走らせる（★★段2 は 1件のみ）
★★記録 = ★★`event_trace` へ emit（★★新台帳 0）
   ★`component="ANATOMIST"` ／ `function="route_edge_vote"`
   ★outputs = ★★`{candidate_id, source, target, kind, votes[], final,
                  disagreement, model, prompt_version, input_hash}`（★正本 §9 の 保存項目）
★★読む = ★★`GET /api/control?include=route_edge_votes`（★★口 0増・★既定では 計算しない）
★★★Worker は 経路表に 書かない（★正本 §12）＝ ★`route_table.ROUTE` は ★★bytes 不変
```

## 6. ★★受入（★数で・★★走らせる前に 宣言する）

```
★★① ★1件の 選定を ★★2回 走らせて ★★同じ `candidate_id`（★決定論）
★★② ★★票が ★★3つ 記録に 残る（★★`votes` の 要素数 = 3）
★★③ ★★保存項目が 全部 在る = ★`model` ／ `prompt_version` ／ `input_hash` ／
     ★`votes` ／ `final` ／ `disagreement`（★★1つでも 欠けたら 未達）
★★④ ★★票が 割れた場合 ★`final` = ★★`NOT_DECIDED`（★★『多数決で 確定』と 書かない）
     ―― ★★★3/3 でない時は ★`disagreement` に 数を 入れる（★★0 と 書かない）
★★⑤ ★★`route_table.ROUTE` が ★★bytes 不変（★Worker が 書いていない）
★★⑥ ★★LLM の呼び出し = ★★★3回だけ（★1候補 × 3seed）＝ ★機械で 数える
★★⑦ ★`/api/control` の ★既定の所要が ★★0.5秒以内の まま（★段0 を 壊さない）
★★⑧ ★★既存2件の 試験が 通る（★★括りの 退行・★走らせた名前を 書く）
★★⑨ ★新台帳0 ／ ★口0増 ／ ★★新しい名前（定数・関数・欄）の 数を 報告
★★⑩ ★★1件 判定できたら ★★★止める（★正本『ここで一度停止する』）
```

## 7. ★★やらないこと

```
★★2件目を 判定しない ／ ★★問い2・問い3 を 作らない ／ ★★経路表へ 登録しない（★段C）
★★票の 多数決を ★『真実』と 書かない（★正本 §9 逐語）
★★候補一覧（★2566件・★internal 635件）を ★front door に 載せない
```
