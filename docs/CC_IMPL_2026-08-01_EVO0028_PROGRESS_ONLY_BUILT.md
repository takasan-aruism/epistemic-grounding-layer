# 【BUILT / `EVO-0028`】進捗だけの投入で **★task を作らなくなった** — ★受入①〜④ すべて ○

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 07:5x / TYPE=BUILT
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0028_PROGRESS_ONLY_MAKES_NO_TASK.md`
- **`:8005` は 2DER が内部で呼んだ**（★私は直接 叩いていない）／ **commit していない**

---

# 1. ★書いた行数
```
★`twoder/submit.py` のみ ／ ★+33行 / -11行（★実質 +22行）
   内訳: ★判定（`_progress_only` の3条件）＋`_rec("PROGRESS_ONLY", …)` を ★:214 の進捗処理の直後に
          ★2つの `create_task`（観測経路 / DW 経路）を ★`if _progress_only:` で分けた（★既存の行はそのまま中へ）
★★手を入れていない: `progress_seal.py` ／ `roadmap_registry.py` ／ `contract_seal.py`（★いずれも変更0件）
★★★`set_status` / `register_item` / `_MAP` にも触っていない ／ 新しい台帳・マーカー・状態語も作っていない
```

## 1-1. ★`extract_contract` を2回 呼んだか → **★はい（★報告項目4）**
```
★:214 で ★1回（★判定のため）／ ★:470 の DW 分岐で ★1回（★従来からの封印）＝ ★計2回
★★:214 の呼び出しは ★try/except で包んだ: ★壊れた契約は ★例外を「契約あり」側に倒す
   ∴ ★観測経路の投入が ★従来より早く落ちることは無い（★安全側）
```

---

# 2. ★受入（①〜④）

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **①** | 投入の前後で `GET /api/tasks` が増えない | **★○** | **180 → 180** |
| **②** | 同じ投入で `progress_write.ok = true`（C-1 が後退していない） | **★○** | `{"ok": true, "item": "ITEM-2DER-EVO-0028", "status": "IN_PROGRESS", "actor": "Claude", "stage": "IMPLEMENT", "reason": null}` |
| **③** | `DW_TASK_ID` が `None` | **★○** | 応答の `task_id` が **`null`**（★空文字ではない） |
| **④** | **本文つきの投入では従来どおり task が作られる**（安全側） | **★○** | `task_id = "TASK-2DER-17C8A5DA"` ／ **180 → 181** |

---

# 3. ★予告の当否（★投入前に固定・`e28_pre.txt`）

| 予告 | 結果 |
|---|---|
| 前の task 件数 = 180 | **★当たり** |
| ③ 進捗だけ → 件数 180→180 / `DW_TASK_ID` = None / `progress_write.ok` = true | **★当たり（3つとも）** |
| ④ 本文つき → 件数 +1 / `task_id` は None でない | **★当たり** |
| **`ITEM-2DER-EVO-0028` は実在しないので title と phase をつけて登記される** | **★★外れた。** **★既に登記されていた**（`description` に「実測=MGR の進捗書き込み4回…」と★他者が書いた文が入っていた）∴ **★私の title / phase は使われず、`set_status` だけが動いた** |

---

# 4. ★滞留の件数（★報告項目5）
```
★滞留6件は ★すべて `CREATED` のまま（`24EF3F6E` `786DC614` `5483F350` `322B1B62` `1F4C8C42` `587AFD37`）
★★★進捗だけの投入では ★1件も増えなかった（★これが今回の成果である）
★★★★ただし ★受入④のために ★本文つきの投入を1回 行った ∴ ★`TASK-2DER-17C8A5DA`（`CREATED`）が★1件 増えた。
   ★これは ★受入④が求めたものであり、★予告にも書いた。★隠さない。★∴ ★滞留は ★6件 → ★7件 である。
```

---

# 5. ★`EVO-0028` の note（★報告項目6）— **★1回 上書きしてしまい、書き直した**
```
★1回目（07:49）: note に ★畳む条件と足りないものを書いた（stage=IMPLEMENT）
★★2回目（07:5x）: ★受入④の投入が ★同じ item に ★別の note を書き、★★1回目を上書きした（stage=VERIFY）
★★★3回目（07:5x）: ★書き直した。★現在の値（実読・逐語）:
   status_note = "actor=Claude stage=RECORD via=front_door note=畳む条件=BLOCK を書く口ができること／
                  足りないもの=その口(record_block に当たるもの)。滞留6件は消さず CREATED のまま残す"
★★★★★見つけたこと（★掘らない）: ★`set_status` の `note` は ★1つしか持てない ∴ ★同じ item に2回 書くと
   ★前の note が消える。★★履歴は追記で残るが、★★front door から読める最新値は ★上書きされる。
```

---

# 6. ★投入の回数と理由（★全件）
| # | 目的 | `task_id` | 件数 |
|---|---|---|---|
| 1 | 進捗だけ（受入①②③） | **null** | 180→180 |
| 2 | 本文つき（受入④） | `TASK-2DER-17C8A5DA` | 180→181 |
| 3 | **note の書き直し**（★2回目が上書きしたため） | **null** | 181→181 |

**★`run_next` は1回も押していない。★gate による再投入は0回。**

---
*IMPL → 設計/監査（写: MGR / Taka）。`EVO-0028`＝進捗だけの投入で task を作らない配線。**書いたのは `twoder/submit.py` のみで +33/-11（実質+22）——`:214` に決定論の3条件（`extract_progress` が dict／`extract_contract` が None／マーカーを除いた残りが空白のみ）で `_progress_only` を立て `PROGRESS_ONLY` を記録し、観測経路と DW 経路の2つの `create_task` を `if _progress_only:` で分けた。`progress_seal.py`/`roadmap_registry.py`/`contract_seal.py` は変更0件、`set_status`/`register_item`/`_MAP` にも触っていない。** **`extract_contract` は2回 呼んでいる（`:214` の判定用と `:470` の封印）。`:214` 側は try/except で包み、壊れた契約は「契約あり」側に倒して安全側にした。** **受入は①〜④ すべて ○——進捗だけの投入で `tasks` は 180→180、`progress_write.ok = true`、`task_id` は `null`（空文字でない）、本文つきでは `TASK-2DER-17C8A5DA` が作られ 180→181。** 予告は件数・③・④が当たり、**★1つ外れた——`ITEM-2DER-EVO-0028` は既に登記されており（description に他者が書いた実測文が入っていた）、私の title/phase は使われず `set_status` だけが動いた**。**滞留は6件とも `CREATED` のままで進捗投入では1件も増えなかったが、受入④のために1件 増えたので現在は7件である（予告に書いたとおり・隠さない）。** **`EVO-0028` の note は1回目に書いた畳む条件を受入④の投入が上書きしたため3回目で書き直した——`set_status` の `note` は1つしか持てず、同じ item に2回 書くと front door から読める最新値が上書きされる（見つけただけ・掘っていない）。** 投入は計3回、`run_next` は0回、gate 再投入0回、commit していない。*
