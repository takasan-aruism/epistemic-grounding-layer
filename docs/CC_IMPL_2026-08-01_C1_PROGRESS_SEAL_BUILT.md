# 【BUILT / C-1】配線は書いた。**★呼ばれなかった** — ★指定の呼び出し位置が DW 分岐の中で、★依頼が観測経路に分類された

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 00:5x / TYPE=BUILT
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **実装源**: `CC_DESIGN_2026-08-01_C1_BUILD_SPEC_AND_S3_CANNOT_BE_INGESTED.md`
- **★止めて設計へ聞く**（SPEC §7「1箇所・最小差分で収まらないと分かった → 止めて設計へ聞く」に当たると読んだ）

---

# 1. ★書いた行数（★私が書く例外なので必ず数える）
```
★新規 twoder/progress_seal.py            ★54行（★全部 私が書いた）
★既存 twoder/submit.py                    ★+8行（★契約封印の隣＝SPEC §2-② の指定位置）
★既存 twoder/webui.py                     ★+1行（★submit 応答に progress_write を追加・既存キー不変）
★★合計 ★63行。★私（Claude/IMPL）が書いた。★2DER の実績ではない
★触っていない: STRUCTURED_KEYS / EXECUTABLE_KEYS / validate_plan / _MAP（★diff 内 各0件）
★新しい台帳・新しい状態語・set_status への検査追加: ★していない
```

---

# 2. ★受入（①②③）

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **①** | front door から1件 書けた（`progress_write.ok = true`） | **★×** | **`progress_write: null`**＝**★そもそも呼ばれていない**（`ok:false` ではない） |
| **②** | `GET /api/roadmap` で読める（counts か status が変わる） | **★×** | counts 前後とも `{"DONE":65,"PLANNED":3,"IN_PROGRESS":4,"PROPOSED":6}`／`ITEM-2DER-EVO-0011` は `DONE → DONE`／`status_note: None`・`registered_at: 2026-07-22T04:00:00+09:00`（★更新されていない） |
| **③** | .md を増やさずに現在地が言える | **★×** | ★①②が立たないので到達しない |

## 2-1. ★`set_status` が `None` を返したか（★SPEC §7-5）
```
★★返していない。★呼ばれていない。
★「測って0」と「測れない」を分ける: ★これは ★「呼ばれなかった」であって ★「呼んだが None だった」ではない。
★根拠: 応答の `progress_write` が ★null（★`_rec("PROGRESS_WRITE", …)` が1度も走っていない）
```

---

# 3. ★原因（★1つ・逐語で示せる）

```
★依頼の分類: ★request_type = "OBSERVE_CURRENT_STATE" ／ acquisition_method = "RUNTIME_INSPECTION"
★私が置いた呼び出し位置: ★SPEC §2-② の指定どおり「契約封印の隣」＝ ★submit.py の ★DW 分岐の中
★★∴ ★観測経路に分類された投入は ★その行に到達しない ∴ ★1行も書かれない
```
**★これは SPEC §7 の「1箇所・最小差分で収まらないと分かった」に当たると読んだ ∴ 止めた。**
**★私は呼び出し位置を勝手に動かさない**（★どこで進捗を受けるかは配線の設計判断である）。

---

# 4. ★予告の当否（★投入前に固定・`c1_pre.txt`）

| 予告 | 結果 |
|---|---|
| 選んだ item = `ITEM-2DER-EVO-0011`（実在・新規作成しない） | **★当たり** |
| 変更前 status = `DONE` | **★当たり** |
| 変更後 status = `DONE`（同じ値） | **★書かれていないので該当なし** |
| **counts の差 = 0** | **★当たり。★ただし理由が違う** — ★予告の理由は「同じ値を書くから」、★実際は「★書き込みが起きなかったから」。**★当たっても理由が違うので、これを「予想が合っていた」と扱わない** |
| **★迷い2**「DW 経路に分類されなければ1行も書かれない見込み」 | **★★当たった。★これが起きたことである** |
| 予告 task_id `TASK-2DER-FE316EF3` | **★当たり**（163字 / sha1 `fe316ef3…`） |

**★迷い1（受入②は示せない見込み）は、★検証に至らなかった**（★書き込み自体が起きていないため）。

---

# 5. ★再投入した回数と理由
```
★0回。★gate は関係していない（★`run_next` を1回も押していない）
★★`POST /api/submit` は ★1回だけ（00:47:42。receipt `last_recv_at=00:47:42.825394`）
★★★依頼文を打ち直して分類を変えにいくことは ★していない（★通りやすくする書き換えに当たるため）
```

---

# 6. ★単体で確かめたこと（★:8005 を呼ばない・★本番に書かない）
```
extract_progress('ふつうの文')                  → None（★マーカー無しは書き込み無し・contract_seal と同じ規約）
extract_progress(正常なマーカー)                → {'item','status','actor','stage','note','sealed_by':'progress_seal'}
note_of(...)                                    → "actor=2DER stage=EXECUTE via=front_door note=…"
END 欠落                                        → ValueError: Missing END for progress
actor 欠落                                      → ValueError: progress missing required field(s): actor
actor 不正 ('Qwen')                             → ValueError: progress actor not allowed: 'Qwen'
stage 不正 ('SOMETHING')                        → ValueError: progress stage not allowed: 'SOMETHING'
★★`set_status` の実呼び出しは ★end-to-end で1度も走っていない ∴ ★「書ける」ことは示せていない
```

---

# 7. ★設計へ聞きたいこと（★1件だけ）
> **★呼び出し位置を、★分岐の前（★全ての投入が通る場所）へ移してよいか。**
> **★理由**: ★進捗のマーカーは ★決定論で判定できる（LLM 非経由）∴ ★分類より前で判定できる。
> **★ただし**: ★どこで受けるかは配線の設計であり、★`submit.py` の入口近くに副作用を置くことになる。**★私は決めない。**
> **★却下される場合の代案（★私は選ばない）**: ★進捗を運ぶ依頼文の側を DW 経路に載る形にする——**★ただしそれは「通りやすくする書き換え」であり、★分類を人が操作することになる。**

---
*IMPL → 設計/監査（写: MGR / Taka）。C-1＝進捗の書き込み口。**私が書いた行数は 63行**（新規 `twoder/progress_seal.py` 54行＋`submit.py` 8行＋`webui.py` 1行。`STRUCTURED_KEYS`/`EXECUTABLE_KEYS`/`validate_plan`/`_MAP` は diff 内 0件、新しい台帳も状態語も作らず `set_status` に検査も足していない）。**受入①②③はすべて ×——`progress_write` が `null`＝そもそも呼ばれておらず（`ok:false` ではない）、roadmap の counts も `ITEM-2DER-EVO-0011` の status も `status_note`/`registered_at` も一切 変わっていない。`set_status` は「None を返した」のではなく「呼ばれていない」。** **原因は1つ: 依頼が `OBSERVE_CURRENT_STATE` / `RUNTIME_INSPECTION` に分類され、SPEC §2-② が指定した呼び出し位置（契約封印の隣＝DW 分岐の中）に到達しなかったこと。** これは §7「1箇所・最小差分で収まらないと分かった」に当たると読んで**止めた——呼び出し位置を勝手に動かさない**。**予告は投入前に固定してあり、counts 差0 は当たったが理由が違う（予告は「同じ値を書くから」、実際は「書き込みが起きなかったから」）ので「予想が合っていた」とは扱わない。迷い2「DW 経路でなければ1行も書かれない」が的中した。** 再投入0回・`submit` 1回・`run_next` 0回で、**依頼文を打ち直して分類を変えにいくことはしていない**。単体では `extract_progress` の fail-closed 7ケースを確認したが、**`set_status` の実呼び出しは end-to-end で一度も走っておらず「書ける」ことは示せていない**。**聞きたいのは1件——呼び出し位置を分岐の前へ移してよいか（決定論で判定できるので分類より前で判定可能だが、どこで受けるかは配線の設計であり私は決めない）。***
