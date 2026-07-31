# 【BUILT / C-1】**★front door から進捗が書けた。★roadmap で読めた** — ★受入①② ○／★③は部分的

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 01:0x / TYPE=BUILT
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **実装源**: `CC_DESIGN_2026-08-01_C1_MY_SPEC_PUT_IT_IN_THE_WRONG_BRANCH.md`
- **`:8005` は 2DER が内部で呼んだ**（★私は直接 叩いていない）

---

# 1. ★書いた行数
```
★今回: ★新規に書いた行 ★0 ／ ★移動した行 ★8（★分岐の中 → `_rec("RRI_REQUEST_TYPE", rt)` の直後）
        ★インデントを 8桁 → 4桁 に直した以外は ★1文字も変えていない
★★累計（C-1 全体で私が書いた分）: ★63行
   ★新規 twoder/progress_seal.py 54行 ／ submit.py +8行 ／ webui.py +1行
★変更していない: ★`progress_seal.py`（54行のまま）／`webui.py` の +1行 ／ `contract_seal` の呼び出し位置
★触っていない: STRUCTURED_KEYS / EXECUTABLE_KEYS / validate_plan / _MAP（★diff 内 各0件）
```

---

# 2. ★受入（①②③）

| # | 受入 | 判定 | 実測（逐語） |
|---|---|---|---|
| **①** | front door から1件 書けた | **★○** | `progress_write: {"ok": true, "item": "ITEM-2DER-IMPL-PLATFORM-VLLM-RUNTIME-PROFILER", "status": "PLANNED", "actor": "Claude", "stage": "VERIFY", "reason": null}` |
| **②** | `GET /api/roadmap` で読める（counts か status が変わる） | **★○** | **counts**: `{"DONE":65,"PLANNED":3,"IN_PROGRESS":4,"PROPOSED":6}` → **`{"DONE":65,"PLANNED":4,"IN_PROGRESS":4,"PROPOSED":5}`**／**item の status**: `PROPOSED` → **`PLANNED`**／**`status_note`**: `actor=Claude stage=VERIFY via=front_door note=front door から書けるかの確認（進捗の主張ではない）` |
| **③** | .md を1本も増やさずに「いまどこか」が言える | **★部分的（★○とは書かない）** | **★1件については言えた**（front door で書き、front door で読めた）。**★しかし「いまどこか」の全部が言えるかは、★この1件では示していない**——★現に本報告は .md である |

## 2-1. ★`progress_write` の値（★区別して書く・SPEC §6-5）
```
★1回目（前 SPEC の位置）: ★`null`   ＝ ★呼ばれていない
★2回目（今回・移動後）  : ★`ok: true` ＝ ★呼ばれて、書けた
★3回目（戻し）          : ★`ok: true`
★★`ok: false` は ★一度も出ていない（★`set_status` が None を返した事例は無い）
```

---

# 3. ★予告の当否（★投入前に固定・`c1_pre2.txt`）

| 予告 | 結果 |
|---|---|
| 選んだ item = `ITEM-2DER-IMPL-PLATFORM-VLLM-RUNTIME-PROFILER`（実在・DONE でない） | **★当たり** |
| 変更前 `PROPOSED` → 変更後 `PLANNED` | **★当たり** |
| counts の差 = `PROPOSED 6→5` / `PLANNED 3→4` / `DONE`・`IN_PROGRESS` 不変 | **★当たり（★4つとも一致）** |
| **迷い1**: 例の `actor: 2DER` を **`actor: Claude` に変えた** | **★そのとおり実行した。**★書かせているのは私である ∴ `2DER` と書けば主体を偽る |
| **迷い2**: 試験で動かした値を **戻す** | **★戻した**（§4 に回数と理由） |

---

# 4. ★投入の回数と理由（★再投入ではない・全件）
| # | 時刻 | 目的 | `request_type` | 結果 |
|---|---|---|---|---|
| 1 | 00:47:42 | ★前 SPEC の位置での確認 | `OBSERVE_CURRENT_STATE` | `progress_write: null`（★呼ばれず） |
| 2 | 00:54:40 | ★移動後の確認（本番） | **`MODIFY_EXISTING`** | **`ok: true`** ／ counts が変わった |
| 3 | 00:55:19 | **★試験で動かした値を元へ戻す** | `MODIFY_EXISTING` | `ok: true` ／ counts が元に戻った |

```
★gate による再投入は ★0回（★`run_next` を1回も押していない。★C-1 の受入に不要）
★★依頼文を打ち直して分類を変えにいくことは ★していない。★2回目と3回目で分類が `MODIFY_EXISTING` に
   なったのは ★私が操作した結果ではない（★1回目と本文の形は同じで、★変えたのは item と status と note のみ）
★★★台帳は append-only ∴ ★PLANNED の記録も ★PROPOSED へ戻した記録も ★両方 残っている
```

---

# 5. ★見つけたことを1件だけ書く（★掘らない・★今回の対象に足さない）
> ### **★`registered_at` に実時刻が入っていない。**
```
逐語: registered_at = "2026-07-11T08:00:00"   ← ★`submit()` の★既定 ts（`submit.py:94`）
★★∴ ★front door から書いた進捗は「★いつ書かれたか」が★記録に残らない。
★★★これは ★設計が既に登記した `G-84`（受理時刻 ts が既定値に落ちる）と ★同型である。
★★★★私は直していない。★今回の対象に足していない。
```

---

# 6. ★同時に廃止するもの（★SPEC §5・★通ったので書く）
```
★本件は通った ∴ ★SPEC §5 の①②は ★廃止の条件を満たしたと ★私は読む。★ただし ★廃止は私が決めない。
   ①「進捗を .md に書く運用」 → ★front door から書けることが示された
   ②「人が set する自己申告値（状況表の A）」 → ★`GET /api/roadmap` から機械で出せることが示された
★★★★ただし ★③が部分的である（★本報告自体が .md である）∴ ★「.md を全部 廃止できる」とは書かない。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。C-1（訂正版）。**今回 新規に書いた行は 0、移動した行は 8**（分岐の中 → `_rec("RRI_REQUEST_TYPE", rt)` の直後・インデント 8→4 桁以外は1文字も変えず。C-1 全体で私が書いた累計は 63行）。**受入①② は ○——`progress_write: {"ok": true, …, "actor": "Claude", "stage": "VERIFY", "reason": null}` が返り、`GET /api/roadmap` の counts が `PROPOSED 6→5 / PLANNED 3→4` に変わり、item の status も `PROPOSED → PLANNED`、`status_note` に `actor=Claude stage=VERIFY via=front_door …` が残った。③は部分的——1件については front door で書き front door で読めたが、「いまどこか」の全部が言えるかは示しておらず、現に本報告は .md である。** **`progress_write` は 1回目 `null`（呼ばれず）／2・3回目 `ok:true` で、`ok:false` は一度も出ていない。** 予告は4つとも当たり（item・前後の status・counts の差）。**迷い1 のとおり `actor` は例の `2DER` ではなく `Claude` にした（書かせているのは私であり `2DER` と書けば主体を偽る）。迷い2 のとおり試験で動かした値は同じ front door から戻した（3回目・append-only なので両方の記録が残る）。** 投入は計3回で gate による再投入は0回、`run_next` は押していない。**見つけたことを1件だけ: `registered_at` が `2026-07-11T08:00:00`＝`submit()` の既定 ts で、front door から書いた進捗は「いつ書かれたか」が残らない（既登記の `G-84` と同型）——直していない・今回の対象に足していない。** SPEC §5 の廃止条件は満たしたと読むが、**廃止は私が決めない**。*
