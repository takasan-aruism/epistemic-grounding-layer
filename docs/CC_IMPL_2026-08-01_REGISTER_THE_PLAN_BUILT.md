# 【BUILT】計画7件を front door から台帳へ登記した — **★受入①〜④ すべて ○**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 03:0x / TYPE=BUILT
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **実装源**: `CC_DESIGN_2026-08-01_REGISTER_ITEM_EXISTS_AND_PLAN_B_CANNOT_WORK.md`
- **`:8005` は 2DER が内部で呼んだ**（★私は直接 叩いていない）

---

# 1. ★書いた行数
```
★今回: ★+14行 / -2行（★実質 +12行）
   twoder/progress_seal.py  +2行（★`OPTIONAL = ("phase","title","note")` の注記のみ。★抽出の本体は不変）
   twoder/submit.py        +12/-2（★既に在る progress ブロックの★中だけ。★位置は動かしていない）
★★C-1 全体で私が書いた累計: ★75行（★63 + 12）
★禁止の確認（diff 内の出現）: `register_amendment` 0件 ／ `_MAP` 0件 ／ `contract_seal` 0件
★`register_item` に検査を足していない ／ 新しいマーカー・入口・台帳・状態語を作っていない
```

---

# 2. ★受入（①〜④）

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **①** | front door から登記できる | **★○** | 7件すべて `progress_write: {"ok": true, …, "reason": null}` |
| **②** | **`GET /api/roadmap` の★フェーズ配下の一覧に出る**（counts だけでは判定しない） | **★○** | **★7/7 が一覧に出た**（下表） |
| **③** | 1件で終わらせない（C-2/C-3/C-4/S-1/S-2/S-3 も同じ口で） | **★○** | **★7件すべて同じ口で登記**（`POST /api/submit` × 7回） |
| **④** | 主体（`actor`/`stage`）が残る | **★○** | 例: `ITEM-2DER-EVO-0027` の `status_note = "actor=Claude stage=RECORD via=front_door note=計画を台帳へ移す"` |

## 2-1. ★登記した7件（★一覧に出た実測）
| item | phase | status | title |
|---|---|---|---|
| `ITEM-2DER-EVO-0021` | `PHASE-2DER-EVO-11` | **DONE** | C-1 進捗の書き込み口（front door -> set_status） |
| `ITEM-2DER-EVO-0022` | `PHASE-2DER-EVO-11` | PROPOSED | C-2 申請書=依頼テンプレを 2DER 自身が作る（止まった理由の表示を含む） |
| `ITEM-2DER-EVO-0023` | `PHASE-2DER-EVO-11` | PROPOSED | C-3 外の道を塞ぐ（front door 以外の経路を閉じる） |
| `ITEM-2DER-EVO-0024` | `PHASE-2DER-EVO-05` | PROPOSED | C-4 「いまどこか」の正典を絞る |
| `ITEM-2DER-EVO-0025` | `PHASE-2DER-EVO-11` | PROPOSED | S-1 棚卸し ＋ roadmap と control の食い違いの原因確定 |
| `ITEM-2DER-EVO-0026` | `PHASE-2DER-EVO-11` | **DROPPED** | S-2 gate の最小パッチ（取り下げ済） |
| `ITEM-2DER-EVO-0027` | `PHASE-2DER-EVO-11` | **IN_PROGRESS** | S-3 人間用UIの4つを 2DER に作らせる（DISPOSE で停止中） |

**counts**: `{"DONE":65,"PLANNED":3,"IN_PROGRESS":4,"PROPOSED":6}` → **`{"DONE":66,"PLANNED":3,"IN_PROGRESS":5,"PROPOSED":10,"DROPPED":1}`** ／ **item 総数 78 → 85**

---

# 3. ★予告の当否

| 予告（投入前に固定） | 結果 |
|---|---|
| 既存の最大 = `ITEM-2DER-EVO-0020` → 次は `0021` から連番 | **★当たり**（EVO 連番 20件・item 総数 78 を front door で数えた） |
| 1件目 = `0021` / `PHASE-2DER-EVO-11` | **★当たり** |
| 1件目 投入後: **DONE 65→66 のみ動く** / item 78→79 | **★当たり（4つの数すべて一致）** |
| 7件後: DONE 66 / PROPOSED 6→12 / item 85 | **★★半分 外れ**（★下記のとおり★私が予告を修正したため） |

## 3-1. ★★予告を1回 修正した（★投入前に書いた・★理由は文書）
```
★当初の予告: 「残り6件は ★すべて PROPOSED」（★私が進捗を判断しないため）
★★修正: ★2件だけ外した。★根拠が文書に在るため:
   S-2 → DROPPED     逐語の出所: `CC_MGR_2026-08-01_D195`「★S-2（gate パッチ）を★取り下げる」
   S-3 → IN_PROGRESS 逐語の出所: `CC_MGR_2026-08-01_D200` の表「ACTIVE = S-3」＋★実際に走行中
★★★これは ★私の進捗判断ではなく ★文書の転記である。★PROPOSED と書けば ★嘘になる。
★★★★修正後の予想（★投入前に固定）: DONE 66 / PLANNED 3 / IN_PROGRESS 5 / PROPOSED 10 / DROPPED 1 / item 85
   ★実測: ★★完全に一致した。
```

---

# 4. ★投入の回数と理由
```
★`POST /api/submit` ★7回（★1件につき1回。★gate による再投入は ★0回・`run_next` は ★1回も押していない）
★★依頼文を打ち直して分類を変えにいくことは ★していない（★全7回とも `MODIFY_EXISTING` に分類された）
```

# 5. ★`progress_write` の値（★区別して書く）
```
★`ok: true`  ★7件（★今回の全部）
★`ok: false` ★0件 ／ ★`null` ★0件
★★∴ ★「未知 id には title と phase が要る」「phase が実在しない」の2つの fail-closed 枝は
   ★今回 ★一度も踏んでいない（★実装したが ★実行では確かめていない）
```

---

# 6. ★戻し方（★可逆・`D-193` §3 の作法）
```
★台帳は追記のみ ∴ ★行は消せない。★戻すのは ★同じ front door から ★`status: DROPPED` を書く:

<<<2DER:PROGRESS>>>
item: ITEM-2DER-EVO-0021      ← ★戻したい item を1件ずつ
status: DROPPED
actor: Claude
stage: RECORD
note: 登記を取り消す
<<<2DER:END>>>

★`DROPPED` は ★`STATUSES` に既に在る（`roadmap_registry.py:27`）∴ ★新しい状態語を作らない。
★★7件すべて戻すなら ★7回 投入する（★1件1回）。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。**計画7件（C-1〜C-4 / S-1〜S-3）を front door から台帳へ登記した。受入①〜④ すべて ○**——7件とも `progress_write.ok = true`、**7/7 がフェーズ配下の一覧に出た**（counts だけで判定していない）、同じ口で7件、`status_note` に `actor=Claude stage=RECORD via=front_door` が残った。counts は `{"DONE":65,"PLANNED":3,"IN_PROGRESS":4,"PROPOSED":6}` → `{"DONE":66,"PLANNED":3,"IN_PROGRESS":5,"PROPOSED":10,"DROPPED":1}`、item 総数 78→85。**書いた行数は今回 +14/-2（実質+12。`progress_seal.py` は注記2行のみで抽出本体は不変、`submit.py` は既存 progress ブロックの中だけで位置は動かしていない）、C-1 累計 75行。`register_amendment`・`_MAP`・`contract_seal` は diff 内0件で、`register_item` に検査を足さず新しいマーカー・入口・台帳・状態語も作っていない。** **予告は1件目が4つの数すべて一致。★残り6件については投入前に予告を1回 修正した——S-2 を `DROPPED`、S-3 を `IN_PROGRESS` にしたのは私の進捗判断ではなく `D-195`/`D-200` の転記であり、`PROPOSED` と書けば嘘になるため。修正後の予想は実測と完全に一致した。** 投入は7回・gate 再投入0回・`run_next` 0回で、依頼文を書き換えて分類を変えにいっていない。**`ok:false` と `null` は0件 ∴ 実装した2つの fail-closed 枝（title/phase 欠落・phase 不在）は今回 一度も踏んでおらず、実行では確かめていない。** 戻し方は同じ front door から `status: DROPPED` を1件ずつ書く（`DROPPED` は既存の状態語）。*
