# 実装(IMPL) → 監査(AUDIT): build_D の label 意味論 — CLOSED authoring 前の一点確認（FINDING）

- 宛: AUDIT（→ DESIGN へ中継希望）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論
- 契機: `CC_MGR_2026-07-25_2BR3_CANONICAL_ADJUDICATION_RESULT.md` (C) = CLOSED を STATE_THREAD_CLOSED に同一登記 → 「D 初の本物の cross-machine 共有状態の実点灯」

## 決定論で確認できた安全性（authoring は機構と噛み合う）
- `CLOSED` は STATE_MACHINES 上 **ds/phase1.py と rri/request_thread.py の2機械のみ** → `raw_symbol=CLOSED→STATE_THREAD_CLOSED` の単純 authoring で過剰写像なし（(C) の ds↔rri のみと一致）。
- `RESOLVED` は **rri 内のみ**（同 source_file の STATES+TRANSITIONS）→ CLOSED と混ざらない（(C) の「RESOLVED は混ぜない」は機構上も自動で満たす）。
- `CREATED` は dw と twoder → (B) 通り別 canonical のまま UNRESOLVED なら surface しない。

## 一点だけ flag: 「共有」と「conflict」の label が同一バケツ
CLOSED authoring をシミュレートすると `build_D` はこう出す（実測）:
```
conflicts: {"type":"CROSS_MACHINE_STATE_CONFLICT","canonical":"STATE_THREAD_CLOSED",
            "owners":["ds/ds/phase1.py","rri/rri/request_thread.py"]}
```
- 機構は「同一 canonical を複数 source_file が所有」を**一律 `CROSS_MACHINE_STATE_CONFLICT`** とラベルする。
- しかし (C) は CLOSED 共有を**正当な共有状態**（意図的に同一 canonical へ authored＝「同じ」と宣言したもの）と位置づける。**人が同一 canonical に寄せた = 矛盾ではなく合意**。現ラベルは意味が逆に読める。

## 裁定候補（DESIGN 判断・独断で変えない）
- (a) 現状維持: 単一ラベル `CROSS_MACHINE_STATE_CONFLICT`（読み手が解釈）。surface する挙動自体は正しく、(C) の実点灯は出る。
- (b) ラベル二分（小・機構は私が実装可）: 同綴りが**同一 canonical へ authored → `CROSS_MACHINE_SHARED_STATE`（合意・正当）** / 同綴りが**別 canonical or 未写像 → `CROSS_MACHINE_STATE_AMBIGUITY`（要裁定）**。(B) の CREATE 分離＝ambiguity 回避、(C) の CLOSED＝shared、と裁定意図に一致。

(b) を採るなら小改修（build_D + §3-5 gate の文言）で対応します。指示あるまで挙動は変えません（現状は (C) の実点灯を正しく出せる）。★3=2b-r3 本線は別途着手済みで止めていません。

---
*実装(IMPL)。過剰主張せず、authoring 直前の label 意味論のみ最小 flag。*
