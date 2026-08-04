# 【BUILD SPEC】`EVO-0058` 段2 — **★S14 に観測を1つ足す。★1区間・1変更**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 18:2x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は無い。★この単位の 2DER 工程は 0**（★観測を1つ足す配線であり、★値→値の判定が無い）
- **★私の予告**: ★Claude の配線 **6〜10行**／★新しい台帳 0／★新しい計器 0（★既存 `etrace.emit` を呼ぶだけ）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★S14 とは（★段1 の表から）

```
★S14 = ★generate → ★runner(run_minimal_slice)→worker ／ ★渡す=packet ／ ★返る=impl.py
★★本日3回 ここで落ちた（★GENERATE 0字 ／ ★空 artifact ×2）が、★★観測が1件も無い
★★★∴ ★『生成が切れた』のか『何も返さなかった』のかを ★区別できない
```

## 2. やること（★1箇所・★emit を1つ）

**★呼び出しの直後**（`generate_via_runner.py:133-134` の `res = _REAL_RUNNER(...)` の次）:

```python
    try:                                                     # S14: 区間の観測(★既存 etrace を呼ぶだけ)
        from ds import etrace as _ET
        _art = res.get("artifact")
        _ET.emit("RUNNER", "run_minimal_slice",
                 {"target_file": task_packet.get("target_file"),
                  "skeleton_len": len(task_packet.get("skeleton") or ""),
                  "tests_len": len(task_packet.get("test_body") or "")},
                 {"status": res.get("status"), "classification": res.get("classification"),
                  "artifact_len": (len(_art) if isinstance(_art, str) else None),
                  "workspace": bool(res.get("workspace"))},
                 "OK" if res.get("ok") else "FAILED",
                 task_id=task_packet.get("task_id"), fail_open=True)
    except Exception:
        pass
```

```
★★`fail_open=True` ＝ ★DW の既存の呼び方と ★同じ（`workcell.py:97-98` 逐語）。★worker 実行を止めない
★★★`artifact_len` が ★★本件の要=★`None`(ファイルが無い) と ★`0`(在るが空) と ★`935`(在る) を ★区別できる
★★★★★★中身は載せない（★`artifact` 本文は ★既に `test_result` に載る経路が在る＝★二重に持たない）
```

## 3. 受入

```
★(1) ★1回 走らせ、★`GET /api/etrace?run_id=…` に ★`component: "RUNNER"` が ★出る
★(2) ★★`artifact_len` が ★逐語で読める（★成功時＝正の数）
★(3) ★★空で落ちた時に ★`artifact_len` が ★`0` か ★`None` かで ★区別できる
     ★★★★空を再現できなければ ★『再現できなかった』と書いて ★止まる（★捏造した失敗を作らない）
★(4) ★`result` が ★`OK`/`FAILED` で入る（★止めた主体は ★component=RUNNER＝2DER 側と分かる）
★(5) ★Claude の配線行数（★2DER の実績に数えない＝★この単位は 2DER 工程0と宣言済）
★(6) ★戻せる（★足した try ブロックを消す）／★(7) ★61本を走らせない
★★★★★予告を投入前に書く: ★行数 ／ ★(1) で出ると思う `artifact_len`
```

## 4. ★★これで分からないこと（★先に言う）

```
★★『生成が途中で切れた』ことは ★★これでも分からない ―― ★`artifact_len` は ★結果の長さであって
   ★★worker の raw 出力ではない。★★切れたなら ★短い artifact が残るはずだが、★本日は ★0字 だった。
★★★∴ ★本件で分かるのは ★★『ファイルが無い / 在るが空 / 在る』の3値まで。
★★★★★worker の raw を残すのは ★★別の区間（★S14 の中）＝ ★次に選ぶなら そこ。★本件では ★作らない（規律9）
```

## 5. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/etrace`（★受入(1)）／2 書く口＝★既存 `emit`。★足さない
3 理由を捨てない＝★`status` と `classification` を ★そのまま載せる（★丸めない）
4 作っていないのでは＝★`res` の値は ★既に手元に在る。★取りに行かない
5 走ったか＝★受入(1) は ★実走行で測る／6 名前＝★`RUNNER`（★新しい component だが ★状態語でも台帳でもない）
7 依頼と試験の矛盾＝★成果物を作らない ∴ 該当なし
8 計器が自分を数えないか＝★`fail_open=True` ∴ ★観測の失敗が ★worker の結果を変えない
★9 増える代わりに廃止＝★★「GENERATE の中で何が起きたかを ★人が推測する」運用を畳む。
   ★★但し ★§4 のとおり ★『切れた』は ★まだ分からない ∴ ★「見えるようになった」と ★書きすぎない
```

## 6. 禁止
```
★S11 / S15 を同時に触る（★1区間=1変更・裁定の逐語）／ ★新しい台帳・計器を作る
★`artifact` の本文を ★emit に載せる（★二重に持たない）／ ★`fail_open` を外す（★worker を止めない）
★空の失敗を ★捏造して再現する ／ ★『切れたことが見えるようになった』と書く
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
