# 宛: Taka ―― GENERATE 本線への契約配線（1箇所）＋ **★受入#1 が塞がっていた理由**

**2026-08-19 ／ commit `323ddad`（`[Claude実装]`・足場のみ・★判断ロジック 0行）**
**★Claude が書いた契約 0 ／ skeleton 0 ／ immutable_tests 0 ／ test_body 0 ／ run_next 0 ／ 状態変更 0**

---

## 1. ★配線前の確認（★Taka 指示どおり 正規面で1回だけ）

`domain_dw.contract_with_precheck`（★G→D の 既存4入口の1つ）に
`TASK-2DER-7D461717` の **記録済み Qwen PLAN** をそのまま渡した結果:

```
★precheck verdict = ★GO
★reason           = None
★skeleton         = ★854バイト
★immutable_tests  = ★1906バイト ／ ★test_body と ★完全一致(True)
```

**★precheck 自身が 自分の限界を 骨格の説明文へ 書き込んだ（★機械が書いた・★逐語）:**

> 「★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない
> (`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない」

＝ **2DER が「この検査は今回効いていない」と自分で残しています。**（★私は1文字も書いていません）

## 2. ★配線した中身 ―― `twoder/webui.py:542`（GENERATE actor `cw`）

```python
ip = plan["payload"].get("implementation_packet") if plan else create["payload"].get("knowledge_packet")
if ip and not create["payload"].get("contract") \
        and ip.get("skeleton") is None and ip.get("immutable_tests") is None:
    from twoder.domain_dw import contract_with_precheck as _CWP
    _c = _CWP(ip)
    if _c.get("skeleton") and _c.get("immutable_tests"):
        ip = {**ip, "skeleton": _c["skeleton"], "immutable_tests": _c["immutable_tests"]}
```

```
★足場が すること = ★既存入口を 呼び ★返りの 2欄を ★そのまま 載せる。★それだけ。
★★封印契約(CREATE payload["contract"])を 持つ task は ★1バイトも 触らない
   =★ledger 経路(★SHA 検査つき)を そのまま 温存（★`generate_via_runner` 未変更）。
★★STOP / 作れない ときは ★何も 足さない=★fail-closed の まま（★補完しない＝Taka 逐語）。
★失敗は 握り潰さず stderr へ（★`DONE_INDEX` の NameError 前例）。
```

**★変更禁止だった物は すべて未変更**:
`contract_from_plan` の判断 ／ `validate_plan` ／ `generate_via_runner` ／ `test_body` ／
skeleton 生成規則 ／ `_MAP` ／ `authority`。

## 3. ★★受入 #1（主対象 7D461717 を再度 GENERATE まで）が **機械的に塞がっていた**

```
★state = JUDGE_REQUIRED ／ 次の操作 = UPPER_REVIEW
★should_call_senior(★2DER が 書いた 部品) = {"call": ★false,
    "reason": ★"no_progress_since_last_review",
    "last_review_ordinal": 3737, "latest_input_ordinal": 3736}
```

```
★★guard の 判断は ★正しい ―― 前回の 上級監査 以降、★記録に 新しい 入力が 1つも 無い。
★★『コードを 配線した』は ★記録の 序数に 現れない ∴ guard からは ★何も 変わっていない。
→ UPPER_REVIEW が 呼ばれない → 状態が 動かない → REGENERATE に 到達しない
→ ★★`cw` を 通る 機会が 来ない。
★動かすには ★状態変更が 要る ∴ ★★許可の 範囲外 ―― ★実行していません。
```

## 4. 代わりに取った手（★許された4つの行為の1つ＝goal 投入）

```
★TASK-2DER-EAACCE21 ／ blocked=False ／ guard_block=None ／ next=★PLAN
★内容 = 同じ能力(unified diff を 作る 純関数)を ★goal の文だけで 投入
★★Claude が 書いた物 = ★goal の文 だけ（契約 0 ／ skeleton 0 ／ test_body 0）
★progress_write ok=true（ITEM-2DER-EVO-0019 / actor=MGR / stage=IMPLEMENT）
★待ち行列の 先頭へ（★他の task には 触っていない）
```

**★受入 #2〜#7 は この1件で測れます。★#1 の文言（7D461717 で）だけは満たせません。**

## 5. 結果（★追記予定）

```
（★観測中 ―― CREATED → PLAN(Qwen) → GENERATE の 3件目の 記録を 待っています）
```
