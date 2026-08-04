# 【BUILD SPEC】`EVO-0058` (A') — **★1区間だけ配線する（S14・★worker 0・★純関数 0）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-05 01:2x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035` ／ 基本設計: `CC_DESIGN_2026-08-05_EVO0058_BASIC_DESIGN_HANDOFF_RECORD.md`
- 裁定: `CC_MGR_2026-08-05_EVO0058_WIRING_IS_THE_DESIGN_NOT_THE_PATCH.md` §8「★(A') Claude が配線だけ置く」
- **★v1.8 の宣言**: **★核は無い・★2DER 工程 0**（★裁定の逐語＝★worker 走行 0 / 純関数 0）
- **★対象区間の数 = ★1**（**S14**。★18区間を一度に触らない）
- **★私の予告**: ★Claude **12〜18行**（★送り手 / ★受け手 / ★packet 1キー）／★worker **0件**／★走行 **1回**
- **★新台帳0・★新計器0・★新エンドポイント0**（★既存 `etrace.emit` の ★引数を使うだけ）

---

## 1. ★なぜ S14 だけで足りるか（★受入(a)＝GENERATE が0字）

```
★★受入(a) の詰まりは ★S14 で起きている（★段2 の観測が ★実際に捉えた＝`result=FAILED` / `artifact_len` 1）
★★★そして ★S14 は ★★引数が通っている ―― ★`task_packet` が ★送り手から ★worker まで ★そのまま届く
   （`generate_via_runner.py:110-122` が組み、`qwen_worker.py:70 run(self, task_packet, workspace)` が受ける）
★★★★∴ ★送り手の `event_id` を ★packet に1キー載せれば ★受け手が ★引用できる ＝ ★★他の区間より先に ★成立する
★他の17区間は ★本件で ★触らない（★引数が通っているかは ★区間ごとに ★別途 実測）
```

## 2. ★★私が手で先にやった（★機械が出すべき値を ★先に固定する）

```
★★『何を渡したか』を ★私が ★手で再構成して ★測った（★実測・下の §5 が ★機械で同じ値を出すこと）:
   requirement = `generate_via_runner.py:116-120` の ★固定テンプレ + ★骨格 + ★immutable_tests
   ★段3 v5 で = ★骨格 34字 + 試験 7343字 → ★★requirement = ★7520字
   ★worker の固定包み(`qwen_worker.py:74-76`)を足して → ★★送信 prompt = ★7656字
   ★素朴な token 推定（非ASCII 1字=1tok / ASCII 3.5字=1tok）= ★2505
   ★★実測 `prompt_tokens` = ★2621（9回とも同一）★★→ ★一致する（★誤差 5%）
★★★∴ ★★これが ★モデルが実際に受け取った文である。★MGR の 1678字の再構成は ★別の文だった（★§6 で訂正）
```

## 3. 送り手（★`generate_via_runner.run_runner`・★`_REAL_RUNNER` を呼ぶ ★直前）

```python
    _hid = None
    try:                                                     # (A') S14 の送り: 何を渡したか の指紋
        from ds import etrace as _ET
        from twoder.route_table import ROUTE as _R          # ★L0 から引くだけ(送り手は判断しない)
        _to = next((r["to"] for r in _R if r["id"] == "S14"), None)
        _req = task_packet.get("requirement") or ""
        _hid = _ET.emit("RUNNER", "hand_to_worker", {"segment": "S14"},
                        {"handoff_len": len(_req),
                         "handoff_sha256": hashlib.sha256(_req.encode("utf-8")).hexdigest()},
                        "OK", handed_to=_to, task_id=task_packet.get("task_id"), fail_open=True)
    except Exception:
        _hid = None
    task_packet["handoff_event_id"] = _hid                   # ★受け手が引用するための1キー
```

## 4. 受け手（★`qwen_worker.QwenWorker.run`・★prompt を組んだ ★直後）

```python
        try:                                                 # (A') S14 の受け: 送り手の id を引用する
            from ds import etrace as _ET
            import hashlib as _h
            _req = tp.get("requirement") or ""
            _ET.emit("WORKER", "received_from_runner",
                     {"segment": "S14", "received_event_id": tp.get("handoff_event_id")},
                     {"handoff_len": len(_req),
                      "handoff_sha256": _h.sha256(_req.encode("utf-8")).hexdigest(),
                      "prompt_len": len(prompt)},
                     "OK", task_id=tp.get("task_id"), fail_open=True)
        except Exception:
            pass
```

```
★本文は ★1文字も入れない（★指紋と長さだけ）。★既存の欄を ★1つも改名しない・消さない。
★`fail_open=True` ＝ ★記録で本処理を止めない（`workcell.py:84` と ★同じ方針）
★★`WORKER` は ★★新しい component 名である ―― ★これは ★『新しい計器』ではなく ★★既存 etrace の ★1行である。
   ★★但し ★L0 に ★S14 の受け側が ★無い ∴ ★★突合(C')の時に ★L0 を ★1行 直す必要が在る（★本件では ★直さない・★先に言う）
```

## 5. 受入

```
★(1) ★1走行で ★両側が出る = `GET /api/etrace?task_id=…` に ★`RUNNER/hand_to_worker` と ★`WORKER/received_from_runner`
★(2) ★★`received_event_id` が ★送り手の `event_id` と ★一致する（★逐語で両方を書く）
★(3) ★★両者の `handoff_sha256` が ★一致する（★一致しなければ ★★ALTERED＝★本日の385字事故の型）
★(4) ★★`handoff_len` が ★★7520（★§2 の私の手計算）と ★一致するか ★逐語で書く
     ★★一致しなければ ★『一致しなかった』と書く ＝ ★★その差が ★★次に調べるもの（★合わせに行かない）
★(5) ★Claude の行数（★送り手 / 受け手 / packet を ★分けて）／★worker 0件・★純関数 0 であること
★(6) ★戻せる ／★(7) ★61本を走らせない ／★(8) ★commit しない
★★★(9) ★出せなかったら ★『出せなかった』と書いて ★止まる
★★★★★予告を投入前に書く: ★行数 ／ ★(4) で出ると思う `handoff_len`
```

## 6. ★★これで分からないこと・★私の訂正（★先に言う）

```
★★★私の 2026-08-04 の指摘(B)「★worker は skeleton を受け取らない」は ★★結論が誤りだった。
   ★`qwen_worker.py` に `skeleton` の出現が0件なのは ★事実だが、★骨格は ★★`requirement` の中に ★入っている
   （`generate_via_runner.py:116-120`）∴ ★『見せられていない物を保存しろ』は ★★成り立たない。★取り消す。
★★★★但し ★別の破綻が ★実物に在る（★逐語）= requirement は 「★<<<FILL>>> マーカー部分だけを実装し」と ★命じるが、
   ★段3 の骨格 `def locate_failure(route, events):` には ★★FILL マーカーが ★無い。
   ★`request_template.py:58` 逐語 =「★示さないと ★骨格 全文が ★変更禁止になります」
   ∴ ★★『変更禁止の全文のうち ★存在しない部分だけを実装せよ』＝ ★★言われた通りには ★満たせない。
★★★★★但し ★★これ単独が原因とは ★言えない = ★FILL 無しで ★通った例が在る（★EVO-0053・★7本 全通）
   ∴ ★『FILL が無いから0字になる』とは ★書かない。★★本件では ★直さない（★1つずつ・★裁定の順序）。
★★★★★★本件で分かるのは ★★『渡した物と受け取った物が同じか』だけ。★『なぜ0字か』は ★分からない。
```

## 7. 禁止

```
★S14 以外の区間を ★同時に配線する ／ ★L0 を ★本件で書き換える（★§4 の但し書き）
★`requirement` の ★本文を ★記録に入れる（★指紋だけ）／ ★`fail_open` を外す
★`<<<FILL>>>` を ★本件で足す（★別の1件・★同時に振らない）
★受入(4) が一致しない時に ★契約や配線を ★合わせに行く（★差が ★次の材料である）
★『渡した記録ができた＝経路表が埋まった』と書く ／ ★新しい台帳・計器・エンドポイントを作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
