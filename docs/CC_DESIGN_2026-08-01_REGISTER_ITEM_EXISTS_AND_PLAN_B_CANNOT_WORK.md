# 【BUILD SPEC】**★`register_item` は既に在る** — ★案B は受入②を満たせない（★理由つきで落とす）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 02:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **裁定**: `D-203` §4（新規 ITEM の登記口・ACTIVE）
- **この .md がまだ .md である理由**: **★本件が通るまで、★計画そのものを登記できない**（`D-203` §3）
- **★増える管理対象 0**（★新しい入口も台帳もマーカーも増やさない）／ **★私はコードを1行も変えていない**

---

# 1. ★調べた結果（★作らない前提。★全数・打ち切り無し）

```
★★MGR の見立て（`D-203` §4）:「★`register_amendment` が既に在る ∴ 繋ぐだけで済む見込み【未確認】」
★★★叩いた結果: ★★見立ての「在る」は当たり。★★ただし ★使う関数が★違う。
```

| 関数 | 逐語の場所 | 作る行の `kind` | **`GET /api/roadmap` に出るか** |
|---|---|---|---|
| `register_amendment` | `roadmap_registry.py:49` | **`AMENDMENT`** | **★出ない** |
| **`register_item`** | **`roadmap_registry.py:71`** | **`ITEM`** | **★出る** |

```
★根拠（逐語）: `roadmap_registry.py:111`
   `if e["kind"] == "ITEM" and (roadmap_id is None or …) and (phase_id is None or …)`
   ＝ ★`items()` は ★`kind == "ITEM"` しか拾わない ∴ ★`AMENDMENT` 行は ★一覧にも counts にも出ない。
★★★★∴ ★`D-203` §4 の ★★案B（`register_amendment` を呼び分ける）は ★★受入② を★構造的に満たせない。
   ★落とす。★理由はここに書いた。★MGR の抜けではなく、★関数名が近いことによる。
```

## 1-1. ★もう1つ、★書いても見えなくなる罠が在る（★先に潰す）
```
★`roadmap_view`（`webui.py:230-236`）は ★★フェーズを回してから ★そのフェーズの items を出す。
∴ ★`phase_id` が ★実在するフェーズでないと ★★一覧に★現れない（★counts には出る）。
★★★＝ ★「書けたのに見えない」が起きる。★C-1 で ★既に一度 通った形である（★`DONE→DONE` の件）。
★★★★∴ ★登記には ★`phase` を★必須にする。★実在するフェーズ（★下記11件）以外は ★弾く。
★実在するフェーズ（★`GET /api/roadmap` 実測・全11件）:
   PHASE-2DER-EVO-01 … 11（★`EVO-11` は「Interface transfer / Claude-Code off-ramp」＝★本件の親に適う）
```

---

# 2. ★やること（★案A のみ。★1箇所）

> ### **★`<<<2DER:PROGRESS>>>` に ★`title:` と ★`phase:` を許す。★未知 id なら ★`register_item` してから ★`set_status`。**

```
<<<2DER:PROGRESS>>>
item: ITEM-2DER-EVO-0101
phase: PHASE-2DER-EVO-11
title: C-1 進捗の書き込み口（front door → set_status）
status: DONE
actor: Claude
stage: RECORD
note: 計画を台帳へ移す1件目
<<<2DER:END>>>
```

## 2-1. ★配線（★`submit.py` の ★既に在る呼び出しの中だけ。★位置は動かさない）
```python
_prog = progress_seal.extract_progress(raw_input)
if _prog:
    if _RM.resolve(_prog["item"]) is None:            # ★未知 id のときだけ登記する
        if not _prog.get("title") or not _prog.get("phase"):
            _rec("PROGRESS_WRITE", {"ok": False, ..., "reason": "unknown item requires title and phase"})
        elif _RM.resolve(_prog["phase"]) is None:
            _rec("PROGRESS_WRITE", {"ok": False, ..., "reason": "phase does not exist"})
        else:
            _RM.register_item(_prog["item"], _prog["phase"], "ROADMAP-2DER-EVOLUTION-v0.1",
                              _prog["title"], _prog.get("note") or "", ts=ts)
    _wrote = _RM.set_status(...)                       # ★既存の行はそのまま
```
```
★★`register_item` に ★検査を足さない（★`status` の検査は ★既に在る＝`:72-73` 逐語 `raise ValueError`）
★★★`roadmap_id` は ★`ROADMAP-2DER-EVOLUTION-v0.1` に固定してよい（★マーカーに増やさない）
★★★★`progress_seal.py` の ★`extract_progress` に ★`title` / `phase` を★任意項目として足す
   （★既知 id のときは ★今までどおり ★無くてよい ＝ ★既存の動きを壊さない）
```

## 2-2. ★★戻し方（★可逆。★`D-203` §4「戻せる形」）
```
★★台帳は ★追記のみ ∴ ★行は消せない。★戻すのは ★`status: DROPPED` を ★同じ口から書く。
★★★`DROPPED` は ★`STATUSES` に ★既に在る（`roadmap_registry.py:27` 逐語）∴ ★新しい状態語を作らない。
★★★★★BUILT に ★戻し方を1行 書くこと（★`D-193` §3 の作法）。
```

---

# 3. ★受入（★`D-203` §4 のまま。★緩めない）
```
★① ★`ITEM-2DER-C1-PROGRESS-WRITE-PATH` 相当を ★front door から★登記できる
★② ★`GET /api/roadmap` に ★★現れる（★★counts だけでなく ★フェーズ配下の一覧に出ること）
★③ ★続けて ★C-2 / C-3 / C-4 / S-1 / S-2 / S-3 も ★同じ口で登記できる（★1件で終わらせない）
★④ ★登記の主体（`actor` / `stage`）が ★残る（★`status_note` に入る）
★★★★★投入前に ★予告を書く: ★item id / phase / 変更前 counts / 予想される counts の差
```

## 3-1. ★★id の付け方（★設計判断。★私が決めて書く）
```
★台帳の規約（`roadmap_registry.py` 冒頭 逐語）: `ITEM_ID  ITEM-<ROADMAP_SHORT>-<NNNN>`
★★MGR が試した `ITEM-2DER-C1-PROGRESS-WRITE-PATH` は ★この規約に合わない（★通っても不揃いになる）
★★★∴ ★★`ITEM-2DER-EVO-<NNNN>` に揃える。★番号は ★既存の最大 +1 から連番。
   ★★★★★投入前に ★`GET /api/roadmap` で ★既存の最大番号を数えて ★予告に書くこと。
★★`register_item` は ★id の形を検査していない ∴ ★これは ★我々の規律であって ★機構ではない。
   ★★★機構にするかは ★別件（★今回 足さない・規律9）。
```

---

# 4. ★手順 ／ 5. ★やってはいけないこと ／ 6. ★報告
```
【手順】① 既存の最大 item 番号と対象 phase を確かめ ★予告を書く → ② §2 の配線（★1箇所）
        → ③ webui 再起動 → ④ `POST /api/submit` 1回 → ⑤ `/api/roadmap` で ★一覧に出ることを確認
        → ⑥ ★受入③のため ★残り6件も ★同じ口で登記 → ⑦ ★戻し方を BUILT に書く
【禁止】★新しいマーカー・新しい入口・新しい台帳・新しい状態語を作る ／ ★`register_item` に検査を足す
        ★`_MAP` に触る（★別件）／ ★`contract_seal` の位置を動かす ／ ★S-3 の依頼文に触る ／ ★commit する
        ★★`register_amendment` を使う（★§1 のとおり ★受入②を満たせない）
【報告】1 ★書いた行数 ／ 2 ★受入①〜④ ／ 3 ★予告の当否 ／ 4 ★再投入の回数と理由
        5 ★`progress_write` の値（★`null` / `ok:false` / `ok:true` を★区別）／ 6 ★戻し方
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①MGR の「関数は既に在る」は当たりだが、使う関数が違う——`register_amendment`（`:49`）は `kind=AMENDMENT` を作り、`items()` は `kind=="ITEM"` しか拾わない（`:111` 逐語）ので `/api/roadmap` に出ない。∴ 案B は受入②を構造的に満たせないので落とす。正しいのは `register_item`（`:71`）である ②もう1つの罠を先に潰す——`roadmap_view` はフェーズを回してから配下の items を出すので、`phase_id` が実在しないと counts には出るが一覧に現れない。∴ `phase` を必須にし、実在する11フェーズ以外は弾く ③案A のみを出す。`<<<2DER:PROGRESS>>>` に `title` と `phase` を任意項目として許し、未知 id のときだけ `register_item` してから `set_status` する。既知 id のときの動きは変えない ④`register_item` に検査を足さない（status の検査は既に在る）。新しいマーカー・入口・台帳・状態語を作らない ⑤戻し方は `status: DROPPED` を同じ口から書くこと。`DROPPED` は既存の状態語なので新設しない ⑥id は台帳の規約 `ITEM-<ROADMAP_SHORT>-<NNNN>` に揃える。MGR が試した `ITEM-2DER-C1-PROGRESS-WRITE-PATH` は規約に合わず、通っても不揃いになる。`register_item` は id の形を検査していないので、これは我々の規律であって機構ではない——機構にするかは別件で今回は足さない ⑦受入は緩めず、②は「counts だけでなくフェーズ配下の一覧に出ること」まで見る。③は1件で終わらせず残り6件も登記する。**
