# 【BUILD SPEC】`(i)` — **★測れる形を 先に作る（★核0・★値は もう 1箇所に 揃っている）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-07 15:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝MGR 裁定(3) の (i)
- **★★核0 ／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限6行**

---

## 1. ★★核が 0 である 理由（★作らない物を 先に 書く）

```
★MGR が 出したい3つ = ★`completion_blockers` / `last_test_passed` / `rework_count`
★★実測 = ★★この3つは ★既に ★1つの関数が ★まとめて 返している（★逐語 `dw/upper_review_gate.py:20-35`）:
      return {"invariants": inv, "trivially_clean": all(inv.values()),
              "blockers": blockers, "n_findings": len(findings), "rework_count": view.get("rework_count", 0)}
   ★`inv` の中身 = completion_blockers_empty / zero_audit_findings_ever /
                   last_test_passed / no_rework / no_open_dispositions
★★★∴ ★★組み立てる物が ありません。★worker に 書かせる物も ありません。
★★★★∴ ★★核を でっち上げない（★本日の 私の失敗の 逆をやる）。★これは ★配線だけの 1件です。
★★★★★本日 同じ形が ★3回 在りました = ★(A)(B) ／ ★C ／ ★本件 ―― ★★値は在り、露出だけが無い。
```

## 2. ★★配線（★上限6行・★範囲では 予告しません＝規律 v1.16）

```
★`GET /api/state?task_id=` の 戻りに ★1欄 足す:
      "upper_review_readiness": <upper_review_gate.evidence(task_id) の 戻り そのまま>
★★整形しない・要約しない・切り詰めない（★`etrace_view` と 同じ作法＝★逐語
  『resolve_run の戻りはそのまま載せる(整形・要約・切り詰めをしない)』）。
★★★読めなければ ★`null` を置く（★★`{}` にしない ―― ★『空』と『引けなかった』を 同じ欄で 混ぜない。
   ★規律 v1.17／★`receipt_view` が 既に この作法です＝逐語『0 は「受けていない」、None は「引けなかった」』）。
★★★★既存の23欄は ★1つも 変えない（★追加のみ）。
```

## 3. ★★受入（★口・欄・★★id を 載せる物として 書く）

```
★(1) ★口 = `GET /api/state?task_id=` ／ ★欄 = `upper_review_readiness.invariants.no_rework`
     ★id = ★★`TASK-2DER-D28FF7E4`（★JUDGE_REQUIRED の実物・★本 SPEC に 名前で 書く）
     ★読める物 = ★true か false の どちらか（★★`null` でない＝★引けている）
★(2) ★口 = 同上 ／ ★欄 = `upper_review_readiness.rework_count` ／ ★id = 同上
     ★読める物 = ★整数
★(3) ★★別の状態の task で ★値が 変わること（★陰性・★★これが無いと『いつも同じ』を 見抜けません）
     ★id = ★`TASK-2DER-9A96D0D5`（★READY_FOR_UPPER_REVIEW の実物）
     ★読める物 = ★(1) と ★同じ欄が ★読め、★★13件側と ★同じ値とは限らないこと
★(4) ★既存の23欄が ★1つも 減らない（★`dw_state` / `upper_reviews` を 名前で 確かめる）
★(5) ★Claude の配線行数（★上限6行）／ ★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit しない
★★★(9) ★★報告に ★測った task の id を ★載せる（★本日 私は id 無しの報告から 対象を 特定できず
        ★21回 問い合わせました）
```

## 4. ★★これが 出たら 何が 決まるか（★MGR の (ii) の 準備）

```
★★13件を 1件ずつ 引けば ★★①が 何かを 動かすかが ★作る前に 決まります:
   ★`no_rework` が ★13件とも false → ★★①は ★この13件を 動かしません
      ―― ★その時 書くのは ★『動かさない』であり、★対象を 選び直します（★MGR 裁定(3)）。
   ★1件でも true が 在る → ★そこが ★最初の 実験対象です。
★★★私は ★予告しません（★どちらに なるかを 書きません）。
★★★★標本にしない（★MGR の逐語どおり ★13件 全部・★★本日 私は 標本18件で 母集団を語って 外しました）。
```

## 5. ★★私が 言っていないこと

```
★『これで ①が 動く』―― ★★本件は ★測れるようにするだけ です。
★『3つの値が 正しい』―― ★★出すだけ です。★正しさは ★既存の関数の 責任です。
★『既存を 畳む』―― ★★MGR 裁定(1) のとおり ★残します（★枝が 排他なので 重なりません）。
★『13件が 動く／動かない』―― ★★測る前に 書きません。
```
