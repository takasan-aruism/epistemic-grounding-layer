# 【BUILD SPEC】`EVO-0058` — **★S11 に記録を1本（★受け渡しではない）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-05 06:0x / TYPE=BUILD_SPEC
- **★条件付き**: ★MGR が ★S11 の指名（★台帳 03:2x の note）を ★採った場合の実装源。**★採らないなら ★破棄してよい**
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は無い・★2DER 工程 0**（★emit 1本 と ★定数2欄。★判断が無い）
- **★私の予告**: ★Claude **6〜10行**（★emit 1本）＋ ★L0 の ★1行の2欄 ／ ★worker **0件** ／ ★走行 **1回**（MGR）
- **★新台帳0・★新計器0・★新エンドポイント0・★行を増やさない**

---

## 1. ★形（★受け渡しの対にしない・★理由）

```
★`(b)` の詰まり = ★run-gate が ★refused を返した走行。★★これは ★hand-off ではない:
   ★refuse は ★`webui.py:817-822` の ★同一プロセス内の判定で、★渡す物は ★`task_id` だけ
   ∴ ★★指紋を比べる相手が ★いない。★2行の呼び出しに ★送り手/受け手の2 event を作るのは ★形の押し付け。
★★∴ ★S11 に要るのは ★★`emit` 1本だけ。★`handoff` / `receipt` は ★None のまま。
★★★L0 の2種類の欄は ★目的が違う（★ここで確定させる）:
   ★`component`/`function` = ★段3 が使う = ★『その区間を ★通ったか』
   ★`handoff`/`receipt`   = ★reconcile が使う = ★『渡した物と受け取った物が ★同じか』
```

## 2. 変更①（★`twoder/webui.py` の ★refuse 分岐・★`return` の直前）

```python
                    if not _d["allow"]:
                        try:                                 # S11: 拒否を記録に残す(★応答だけに出て記録に残らなかった)
                            from ds import etrace as _ET
                            _ET.emit("RUNGATE", "refuse", {"task_id": tid},
                                     {"cause": _d["cause"], "blocked": gate["blocked"],
                                      "runnable": gate["runnable"], "gate_task_id": gate["task_id"]},
                                     "REFUSED", task_id=tid, fail_open=True)
                        except Exception:
                            pass
                        return self._send({...})             # ★応答は ★1文字も変えない
```
```
★`webui.py:813` で ★`set_run_id` 済 ∴ ★同じ run に繋がる（★新たに run を作らない）
★`fail_open=True` ＝ ★記録で本処理を止めない ／ ★応答の中身は ★1欄も変えない（★EVO-0053 の cause を ★そのまま載せるだけ）
```

## 3. 変更②（★`twoder/route_table.py` の ★S11 の行だけ）

```python
 {"id": "S11", ..., "component": "RUNGATE", "function": "refuse", "phase": None,
  "handoff": None, "receipt": None},          # ★受け渡しではない ∴ ★2欄は None のまま
```
```
★★段3 が変わらないことを ★私が先に測った（★実測・下の §4）
```

## 4. ★★私が先に測った（★1つは ★予告が外れた）

```
★(1) ★S11 を埋めても ★既存の結果は ★変わらない:
     TASK-2DER-51E58279 → ★LOCATED/S14（★前後で `==`）／ 98D5F072 → ★BOUNDED/None（★同）
★(2) ★refuse の記録が ★1件だけ在る走行を ★合成して当てた:
     → ★`verdict=LOCATED` / ★`segment=S11` / ★`last_observed=S11` / ★`actor=Claude`
★★★(3) ★★私の予告は ★外れた ―― ★私は ★`actor_confirmed=False`（★L0）だから ★`actor_known=False` と ★予告した。
     ★実測は ★★`actor_known=True`。
★★★★原因 = ★★段3 の契約は ★`LOCATED` なら ★無条件で `actor_known=True` を返す（★依頼文の逐語）
     ∴ ★★L0 の `actor_confirmed` を ★見ていない。
★★★★★∴ ★★S11 は ★記録から主体を確かめていないのに ★『確認済み』と ★言ってしまう。
     ★★これは ★段3 の契約の穴である（★本件では ★直さない・★§6 に ★名指しで残す）
```

## 5. 受入

```
★(1) ★★再現手順を ★先に固定してから走らせる（★`_LAST` は ★`webui.py:32` の ★プロセス内 dict
     ∴ ★webui を再起動すると ★再現しない）。★手順を ★逐語で書く
★(2) ★1回 refuse させ、★`RUNGATE/refuse` が ★`GET /api/etrace?run_id=…` に ★出る
     ★★`task_id` では ★引けない（★既知の穴）∴ ★★どの `run_id` から取ったかを ★逐語で書く
★(3) ★`outputs` に ★`cause` が ★逐語で入っている（★`NOT_RUNNABLE` 等）
★(4) ★★`locate_failure` を ★その走行に当て、★`LOCATED` / `segment="S11"` が ★出る（★§4(2) の予告）
★(5) ★★`actor_known` が ★`True` と出ることを ★★そのまま書く ―― ★★『主体を確かめた』とは ★書かない
     （★§4(3)・★L0 は `actor_confirmed=False` である）
★(6) ★応答の中身が ★1欄も変わっていない（★`refused`/`reason`/`cause`/`task_id`）
★(7) ★Claude の行数（★emit / L0 を分けて）／★(8) ★戻せる ／★(9) ★61本を走らせない ／★(10) ★commit しない
★★★(11) ★出せなかったら『出せなかった』と書いて止まる
★★★★★予告を投入前に書く: ★行数 ／ ★(4) の verdict と segment
```

## 6. ★★名指しで残す（★本件では直さない）

```
★★段3 の `actor_known` が ★L0 の `actor_confirmed` を ★見ていない（★§4(3)）
   ＝ ★未確認の主体を ★『確認済み』と ★言う。★★本日 我々が ★何度も戒めてきた形そのもの。
★★★戻る条件 = ★本件が通り、★S11 が ★実データで ★1回 名指しされた直後
★★★★いま足りないもの = ★段3 の契約に ★『actor_known は route の `actor_confirmed` を ★そのまま返す』の1行
   ＝ ★新しい機構ではない（★既に在る欄を ★読むだけ）。★但し ★契約を変えるので ★別の1件にする
```

## 7. 禁止

```
★S11 を ★hand-off の対にする（★§1）／ ★`handoff`/`receipt` に ★値を入れる
★応答の欄を ★足す・変える（★記録だけ）／ ★`fail_open` を外す
★段3 の契約を ★本件で直す（★§6）／ ★L0 の他の17行を ★触る
★★『主体を確かめた』『経路表が埋まった』と書く
★捏造した refuse を作る（★再現できなければ ★『再現できなかった』と書いて止まる）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
