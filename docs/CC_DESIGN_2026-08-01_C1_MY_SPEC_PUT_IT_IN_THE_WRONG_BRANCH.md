# 【監査＋SPEC 訂正 / C-1】**★誤りは私の SPEC にある** — ★呼び出し位置を分岐の中に指定した

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 02:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **受領**: `CC_IMPL_2026-08-01_C1_PROGRESS_SEAL_BUILT.md`
- **★新しい名前で置いた**（★前 SPEC `CC_DESIGN_2026-08-01_C1_BUILD_SPEC_...` を★同名で差し替えない）
- **この .md がまだ .md である理由**: **★C-1 そのもの。★本件が通ったら廃止する**

---

# 1. ★★誤りは私にある（★先に書く）

```
★私の SPEC §2-② 逐語:「★`submit.py` で ★契約封印の★直後に1回 呼び…
   （★`submit.py:470` の `_contract = contract_seal.extract_contract(raw_input)` の★隣）」
★★★`submit.py:470` は ★`elif rt.get("request_type") in ("BUILD_CAPABILITY","MODIFY_EXISTING"):`
   （★`:430` 開始）の ★★中である。
★★∴ ★進捗だけの依頼は ★`OBSERVE_CURRENT_STATE`（`:368`）に分類されるので ★その行に★到達しない。
★★★★私は ★「契約と同じ場所に置けばよい」と考えたが、★契約は ★DW task を作る依頼にしか要らない。
   ★★進捗は ★★分類に関係なく書けなければならない。★★性質が違うのに ★同じ場所を指定した。
★★★★★★IMPL は ★指定どおりに書き、★受入①②③ を ★×と正しく判定し、★SPEC §7 に従って止めた。
   ★★★実装側に ★誤りは無い。★止めた判断は ★正しい。
```

## 1-1. ★独立に確認した（★報告を読む前に測った）
```
★diff: ★`submit.py` +8 ／ `webui.py` +1 ／ `progress_seal.py` 新規（★合計 63行・IMPL 申告と一致）
★`STRUCTURED_KEYS` / `EXECUTABLE_KEYS` / `validate_plan` / `_MAP` の出現: ★diff 内 0件 ✓
★★呼び出し位置が `:430` の分岐内であること: ★`grep -n "^    elif rt.get"` で ★430 と 490 の間に在ると確認 ✓
★★★「呼ばれなかった」と「呼んで None だった」を分けて書いた IMPL の判定は ★正しい（★規律6）
```

---

# 2. ★★訂正した設計（★1箇所。★分岐の★外へ出す）

> ### **★呼び出しを ★分類分岐より★前へ移す。★`submit.py:214` の直後。**

```
★`submit.py:213` 逐語: `rt = RT.classify_request_type(raw_input, …)`
★`submit.py:214` 逐語: `_rec("RRI_REQUEST_TYPE", rt)`
★★★★この直後に置く。★理由:
   ★① ★`raw_input` も `ts` も ★既に使える（`:87` 引数・`:94` 既定値）
   ★② ★どの `request_type` でも ★必ず通る（★分岐は `:368` から始まる）
   ★③ ★分類の★後なので、★`_rec("RRI_REQUEST_TYPE", rt)` と ★並んで記録が残る
★★★★★★契約（`contract_seal`）は ★動かさない。★あれは ★DW 分岐の中で正しい。★★進捗だけを外へ出す。
```

## 2-1. ★移すもの（★書き足さない。★8行を★そのまま移動する）
```python
        # C-1: 進捗も同じマーカー方式で運ぶ(新しい入口・新しい台帳を作らない)。既存の set_status をそのまま呼ぶ。
        from twoder import progress_seal, roadmap_registry as _RM
        _prog = progress_seal.extract_progress(raw_input)
        if _prog:
            _wrote = _RM.set_status(_prog["item"], _prog["status"], ts=ts, note=progress_seal.note_of(_prog))
            _rec("PROGRESS_WRITE", {"ok": bool(_wrote), "item": _prog["item"], "status": _prog["status"],
                                    "actor": _prog["actor"], "stage": _prog["stage"],
                                    "reason": None if _wrote else "set_status returned None (unknown id or status not in STATUSES)"})
```
```
★★インデントを ★分岐の中（8桁）から ★関数直下（4桁）へ ★直すこと。★それ以外は1文字も変えない。
★★★`progress_seal.py` は ★変更しない（★54行のまま）。★`webui.py` の +1行も ★そのまま。
★★★★∴ ★今回の変更は ★★移動のみ。★★新しく書く行は ★0 の見込み。★実際の数を報告すること。
```

---

# 3. ★受入（★前 SPEC と同じ。★緩めない）
```
★① `POST /api/submit` の応答に ★`progress_write.ok = true`
★② ★`GET /api/roadmap` で ★該当 item の `status` か `status_counts` が ★変わる
★③ ★.md を1本も増やさずに「いまどこか」が言える
★★★★★前回の実測を「前」として使ってよい（★同じ口・同じ item なら比較になる）:
   ★`status_counts` = {"DONE":65,"PLANNED":3,"IN_PROGRESS":4,"PROPOSED":6}
   ★`ITEM-2DER-EVO-0011` = `DONE` ／ `status_note: None` ／ `registered_at: 2026-07-22T04:00:00+09:00`
★★★★★★★★対象 item は ★`DONE` 以外へ動かせるものを選ぶこと。
   ★`DONE → DONE` では ★「書けたか」が★見分けられない（★前回それを選んで判定できなかった）。
   ★★例: ★`IN_PROGRESS` の item を1つ選び ★`DONE` にする。★または ★`PROPOSED` → `PLANNED`。
   ★★★★選んだ item・変更前・変更後・予想される counts の差を ★投入前に書く。
```

# 4. ★手順（★変えない）
```
① ★`GET /api/roadmap` で ★対象 item と現在 status を確かめ ★予告を書く
② ★§2 の移動 → ★webui 再起動 → ③ `POST /api/submit` 1回 → ④ receipt → ⑤ `/api/roadmap` で確認
★★gate が閉じたら ★同一依頼文の再投入（★第1章）。★回数と理由を書く
★★★`progress_write` が ★`null` なら ★また呼ばれていない ∴ ★止めて設計へ聞く（★同じ穴を2度 掘らない）
```

# 5. ★やってはいけないこと
```
★`contract_seal` の呼び出し位置を動かす（★あれは正しい位置に在る）
★`progress_seal.py` に手を入れる ／ ★`set_status` に検査を足す ／ ★`_MAP` に触る
★新しい台帳・新しい状態語を作る ／ ★S-3 の依頼文に触る ／ ★commit する
★★対象 item を ★`DONE → DONE` にする（★見分けられない）
```

# 6. ★報告
```
1 ★書いた行数（★移動のみなら「新規0・移動8」と書く）／ 2 ★受入①②③ ／ 3 ★予告の当否
4 ★再投入の回数と理由 ／ 5 ★`progress_write` の値（★`null` か `ok:false` か `ok:true` かを★区別して書く）
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①誤りは私の SPEC にある——「契約封印の隣」と指定した `submit.py:470` は `BUILD_CAPABILITY/MODIFY_EXISTING` 分岐（`:430` 開始）の中で、進捗だけの依頼は `OBSERVE_CURRENT_STATE`（`:368`）に分類されるので到達しない。契約は DW task を作る依頼にしか要らないが、進捗は分類に関係なく書けなければならない——性質が違うのに同じ場所を指定した ②IMPL は指定どおりに書き、受入を×と正しく判定し、SPEC §7 に従って止めた。実装側に誤りは無い ③独立に確認した——diff は 63行で申告と一致し、触ってはいけない4つは diff 内0件、「呼ばれなかった」と「呼んで None だった」の区別も正しい ④訂正は呼び出しを分類分岐の外（`submit.py:214` の直後）へ移すこと。`raw_input` も `ts` も使え、どの request_type でも必ず通り、分類の記録と並ぶ ⑤契約の呼び出し位置は動かさない。進捗だけを外へ出す ⑥変更は移動のみで新規行は0の見込み。インデントを8桁から4桁へ直す以外は1文字も変えない ⑦受入は緩めない。ただし対象 item は `DONE → DONE` を選ばないこと——前回それを選んで「書けたか」を見分けられなかった ⑧`progress_write` がまた `null` なら止めて設計へ聞く。同じ穴を2度 掘らない。**
