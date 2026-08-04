# 【BUILD SPEC】`EVO-0058` — **★観測が無い7区間に ★記録を1本ずつ**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 07:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035` ／ 依頼: MGR 07:3x（★監視の指摘を受けた順序）
- **★v1.8 の宣言**: **★核は無い・★2DER 工程 0**（★emit 7本 と ★定数7行。★判断が無い）
- **★私の予告**: ★Claude **7区間 × 6〜9行 ＝ 45〜65行** ／ ★worker **0件** ／ ★走行 **1〜2回**
- **★私が撤回した規則**: 「★1区間=1変更（裁定の逐語）」は ★★出典が無く ★私が作った ―― ★本書は ★7区間を ★まとめて配線する
  （★Taka 裁定の逐語＝「★急ぐが吉」「★即やること＝★18区間を埋めさせる」）
- **★新台帳0・★新計器0・★新エンドポイント0・★行を増やさない**

---

## 1. ★★先に言う: ★これは「終わった」の記録であって「始まった」ではない

```
★Taka の依頼（逐語）= 「★A が処理を始めた／終わった、★B が受け取った／終わった」＝ ★1区間あたり ★4行
★★本書が置くのは ★★1区間 ★1行 ―― ★呼び出しが ★返った後に置く ∴ ★これは ★★『終わった』の記録である。
★★★『始まった』が要るのは ★★★返って来ない時（★止まって固まった時）を捉えるため。
   ∴ ★★次の1件（★戻る条件＝★本書が通り、★★『どこで止まったか』が ★1件でも言えた直後）
★★★★★『4行 揃った』とは ★書かない。★★『7区間で ★通ったことが残るようになった』だけ。
★★★★★★`span`（`ds/ds/etrace.py:190`）は ★正常終了に emit しない上に ★★呼び手が0件（★実測）
   ∴ ★『span を直せば終わりが残る』は ★誤り。★本書は ★span を使わない。
```

## 2. ★★置く場所（★逐語で実測した7箇所）

| 区間 | ファイル:行 | 置く直後の呼び出し | component / function |
|---|---|---|---|
| **S03** | `twoder/submit.py:171` | `phase1.reconstruct_snapshot(...)` | `DS` / `phase1` |
| **S04** | `twoder/submit.py:213` | `RT.classify_request_type(...)` | `RRI` / `request_type` |
| **S05** | `twoder/submit.py:290` | `PG.detect(raw_input, ...)` | `RRI` / `preflight_gate` |
| **S08** | `twoder/submit.py:539` | `contract_seal.extract_contract(...)` | `SEAL` / `extract_contract` |
| **S10** | `twoder/webui.py:832` | `D.next_legal_operation(tid)` | `DISPATCH` / `next_legal_operation` |
| **S11** | `twoder/webui.py:819-822` | `_gd(gate, tid)` の ★not allow 分岐 | `RUNGATE` / `refuse` |
| **S15** | `twoder/live_worker_runtime.py:169` | `_run_test(ws, ...)` | `RUNNER` / `run_test` |

```
★★S10 の注意 = ★`next_legal_operation` は ★webui の中で ★4箇所 呼ばれる（★:122 :227 :443 :832）。
   ★置くのは ★★`:832`（★run_next の中）★だけ ―― ★他の3箇所は ★画面の描画で ★毎回 呼ばれる（★記録が溢れる）
★★S11 は ★`return` の ★直前（★応答の中身は ★1欄も変えない）
```

## 3. ★★書く中身（★7本 共通の形・★本文は入れない）

```python
    try:                                                     # EVO-0058: 区間の記録(★既存 etrace を呼ぶだけ)
        from ds import etrace as _ET
        _ET.emit("<component>", "<function>", {<★入口の小さな値>}, {<★出口の小さな値>},
                 "OK", task_id=<★在れば>, fail_open=True)
    except Exception:
        pass
```

**★区間ごとの `inputs` / `outputs` / `result`（★小さい値だけ・★本文は入れない）**

```
★S03 in {"utterances": len(all_utts)}            out {"threads": len(threads or [])}
★S04 in {"raw_len": len(raw_input)}              out {"request_type": rt.get("request_type")}
★S05 in {"raw_len": len(raw_input)}              out {"decision": pg.get("decision"),
                                                      "triggered": pg.get("triggered")}
★S08 in {"raw_len": len(raw_input)}              out {"sealed": bool(_contract),
                                                      "skeleton_len": len((_contract or {}).get("skeleton") or ""),
                                                      "tests_len": len((_contract or {}).get("immutable_tests") or "")}
★S10 in {"task_id": tid}                         out {"operation": <★上の呼び出しの戻りの operation>}
★S11 in {"task_id": tid}                         out {"cause": _d["cause"], "blocked": gate["blocked"],
                                                      "runnable": gate["runnable"]}   ★result="REFUSED"
★S15 in {"test_command": result.get("test_command")}
                                                 out {"passed": test.get("passed"), "exit": test.get("exit")}
                                                 ★result = "OK" if test.get("passed") else "FAILED"
★★★S11 以外の result は ★"OK"（★S15 は上のとおり分岐）
★★★★★`raw_input` / `transcript` / 契約本文 は ★1文字も入れない（★長さだけ）
```

## 4. ★L0 を7行 埋める（★`twoder/route_table.py`・★行は増やさない）

```python
 S03 → "component": "DS",       "function": "phase1"
 S04 → "component": "RRI",      "function": "request_type"
 S05 → "component": "RRI",      "function": "preflight_gate"
 S08 → "component": "SEAL",     "function": "extract_contract"
 S10 → "component": "DISPATCH", "function": "next_legal_operation"
 S11 → "component": "RUNGATE",  "function": "refuse"
 S15 → "component": "RUNNER",   "function": "run_test"
 ★7行とも "phase": None / "handoff": None / "receipt": None（★受け渡しではない）
```
```
★★段3 の契約は ★1文字も変えない（★未知の欄も ★新しい語も ★足していない）
```

## 5. 受入

```
★(1) ★1回 投入し、★`GET /api/etrace?run_id=…` に ★★S03 S04 S05 S08 が ★出る（★submit 経路）
★(2) ★1回 run_next を通し、★★S10 が出る／★1回 拒否させ ★★S11 が出る
     ★★拒否を再現できなければ ★『再現できなかった』と書いて ★その1件だけ ★保留（★他は進める）
★(3) ★1回 GENERATE まで進め、★★S15 が出る（★`passed` と `exit` が ★逐語で読める）
★(4) ★★`locate_failure` を ★その走行に当て、★`last_observed` が ★★S03 より後ろへ ★進むことを ★逐語で示す
     ★★★出た区間の一覧を ★そのまま書く（★★『18区間 埋まった』とは ★書かない）
★(5) ★出なかった区間は ★★『出なかった』と書く ＝ ★それが ★次に見る場所
★(6) ★Claude の行数（★区間ごとに分けて）／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★(10) ★応答・成果物・DW の状態が ★1つも変わっていないこと（★記録を足しただけ）
★★★★★予告を投入前に書く: ★行数 ／ ★(1)〜(3) で ★出ると思う区間
```

## 6. ★★これで分からないこと（★先に言う）

```
★★『始まった』は ★残らない（★§1）∴ ★★『★返って来ないまま固まった』区間は ★★依然 見えない
★★★『誰が持っているか』は ★L0 の `actor` から引くだけ ―― ★★`actor_confirmed=False` の区間は
   ★記録から確かめていない。★段3 は ★LOCATED なら ★無条件で `actor_known=True` を返す（★既知の穴）
   ∴ ★★『主体を確かめた』とは ★書かない
★★★★S03/S04/S05 は ★submit の中で ★必ず走る ∴ ★出るのは ★当たり前である ―― ★★それでも要る:
   ★『走ったはずだが記録が無い』と ★『そもそも走っていない』を ★分けるのは ★この1行だけである
```

## 7. 禁止

```
★7区間 以外を触る ／ ★`span` を使う ／ ★`next_legal_operation` を ★:832 以外に置く（★§2）
★`raw_input` / 契約本文 / 応答本文 を ★記録に入れる（★長さと分類だけ）
★応答・DW の状態を ★1つでも変える ／ ★`fail_open` を外す
★新しい状態語を作る（★`decision` / `cause` / `operation` は ★既存の値を ★そのまま載せる）
★★『18区間 埋まった』『どこで止まるか分かるようになった』と書く（★§6）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
