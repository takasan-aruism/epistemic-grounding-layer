# 【BUILD SPEC / C-1】進捗の書き込み口＝**★マーカー1つ**（既存方式の流用） ／ **★S-3 は ingest で戻せない**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 01:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **裁定**: `D-201` §2（C-1 を ACTIVE） ／ 運用規律 v0.3 確認済
- **この .md がまだ .md である理由**: **★C-1 そのもの。★本件が完了したら ★この形式を廃止する**
- **★増える管理対象 0**（★§5 で廃止するものを同時に書く・規律9）／ **★私はコードを1行も変えていない**

---

# 0. ★★先に、`D-201` §4 の前提を訂正する（★止まる前に言う）

> ### **★S-3 を「処置と同じ形（`/api/ingest`）で戻す」ことは★できない。**

```
★`D-201` §4 逐語:「★`JUDGE_REQUIRED` ＝ 上級の判定。★設計/監査が動ける時に ★処置と同じ形
   （`/api/ingest`）で戻す」
★★★叩いて確かめた（★2回目。★前回は `TASK-2DER-E8F8CA7B`、★今回は `TASK-2DER-B37727E3`）:
   逐語: {"error": ★"ValueError: no Claude ingest for op=BLOCKED"}
★★理由は ★`CC_DESIGN_2026-08-01_D197_ONE_MISSING_KEY_BLOCKS_BOTH.md` に既に書いた:
   ★`dispatch.py:_MAP` の★全8キーに ★`JUDGE_REQUIRED` が無い ∴ ★既定値 `BLOCKED` に落ちる
   ★`webui.ingest` は `PLAN` / `DISPOSE` / `UPPER_REVIEW` しか受け取らない（`webui.py:376-383`）
★★★★∴ ★S-3 は ★★誰の手番でもない。★判定を書いても ★入れる口が無い。
   ★★これは ★C-1 と ★同じ性質の欠落である（★書く先が無い）。★偶然ではないと思われる。
★★★★★★私は ★勝手に繋がない（★裁定の手番）。★★ただし ★「設計/監査の手番」と★書かれたままにしない。
```

---

# 1. ★C-1 の設計（★作らない。★既に在る方式を★もう一度 使う）

```
★front door は ★`{"raw": "<本文>"}` の ★1文字列しか受け取らない（`webui.py:657` 逐語）
★★契約は ★本文中のマーカーで ★決定論抽出されている（`contract_seal.py:19-21`・★LLM を呼ばない）
★★★∴ ★進捗も ★同じ方式で運ぶ。★★新しい入口・新しい関数・新しい台帳を ★作らない。
```

## 1-1. ★マーカー（★`contract_seal` と同じ形。★終端は既存の `<<<2DER:END>>>` を流用）
```
<<<2DER:PROGRESS>>>
item: ITEM-2DER-EVO-0011
status: DONE
actor: 2DER
stage: EXECUTE
note: front door から書けることを確認した
<<<2DER:END>>>
```

## 1-2. ★書き込み（★既存関数をそのまま呼ぶ）
```
★`twoder/roadmap_registry.py:90` 逐語 `def set_status(rid, status, ts=None, note=None)`
★★`STATUSES`（同 `:27` 逐語）= {"PROPOSED","PLANNED","IN_PROGRESS","DONE","DEFERRED","DROPPED"}
★★★`set_status` は ★`resolve(rid)` が無い／`status` が上記に無い なら ★`None` を返す ＝ ★fail-closed 済
   ∴ ★★検査を新しく書かない。★`None` が返ったら ★その旨を応答に載せるだけ。
★★★★`note` に ★`actor` と `stage` を★埋め込む（★新しい欄を作らない・★v0.3 §13.2 の主体を残す）
```

## 1-3. ★主体欄（★v0.3 §13.2。★入れなければ書き込めない形にする）
```
★`actor` ∈ {2DER, Claude, MGR, Taka, External, UNKNOWN}
★`stage` ∈ {DETECT, PLAN, IMPLEMENT, EXECUTE, VERIFY, ADJUDICATE, RECORD, RESPOND}
★★★どちらか欠けていたら ★書かずに ★理由を返す（★fail-closed）。★`UNKNOWN` は★書けるが★値として残す
   （★「分からない」と「書かなかった」を★同じ欄に持たせない）
```

---

# 2. ★やること（★1箇所。★最小差分）
```
★① `twoder/` に ★`progress_seal.py` を ★1本 作る（★`contract_seal.py` と★同じ形・★同じ終端マーカー）
   ★`extract_progress(raw_input) -> dict | None`
   ★マーカー両方が無ければ ★`None`（★契約と同じ規約）／★片方だけ・`END` 欠落は ★`ValueError`
   ★`item` / `status` / `actor` / `stage` のいずれかが欠けたら ★`ValueError`（★fail-closed）
★② `twoder/submit.py` で ★契約封印の★直後に1回 呼び、★`set_status` を呼ぶ
   ★（★`submit.py:470` の `_contract = contract_seal.extract_contract(raw_input)` の★隣）
   ★★`set_status` が `None` を返したら ★`_rec("PROGRESS_WRITE", {"ok": False, "reason": ...})`
   ★★★成功したら ★`_rec("PROGRESS_WRITE", {"ok": True, "item": ..., "status": ...})`
★③ ★`webui.py` の submit 応答に ★`progress_write` を1つ足す（★既存キーは変えない・★追加のみ）
★★★★これ以外を触らない。★`STRUCTURED_KEYS` / `EXECUTABLE_KEYS` / `validate_plan` / `_MAP` に触らない
```

---

# 3. ★受入（★`D-201` §2 の完了条件をそのまま試験にする）
```
★① ★front door から ★1件 書けた（★`POST /api/submit` の応答に `progress_write.ok = true`）
★② ★その値が ★`GET /api/roadmap` で ★読める（★`status_counts` か該当 item の `status` が変わる）
★③ ★★.md を1本も増やさずに「いまどこか」が言える
★★★★対象 item は ★実在するものを1つ選ぶ（★`GET /api/roadmap` から）。★新しい item を作らない
★★★★★★予告を投入前に書く: ★選んだ item / 変更前の status / 変更後の status / 予想される counts の差
```

---

# 4. ★手順（★増やさない）
```
① ★`GET /api/roadmap` で ★対象 item と ★現在の status を★確かめる（★予告を書く）
② ★実装（★§2 の①〜③）→ ★webui 再起動（★全件 記録）
③ ★`POST /api/submit` に ★§1-1 のマーカーを含む本文を ★1回
④ ★直後に ★`GET /api/receipt` → ★`GET /api/roadmap` で ★変わったことを確かめる
⑤ ★gate が閉じたら ★同一依頼文の再投入で開け直す（★第1章）。★回数と理由を書く
★★★`set_status` が `None` を返したら ★それも結果である。★理由を逐語で持ち帰る
```

---

# 5. ★★同時に廃止するもの（★規律9。★書かなければ増やさない）
```
★① ★進捗を .md に書く運用 → ★本件が通ったら ★`CC_*` の「この .md がまだ .md である理由」の
     ★★「進捗」に当たる分は ★廃止する（★裁定・調査の往復は★別問題として残る）
★② ★人が set する自己申告値（★状況表の A） → ★`GET /api/roadmap` から★機械で出す形へ置換
★★★★どちらも ★本件の完了と同時に ★廃止すると書いた。★通らなければ ★廃止しない（★嘘を書かない）
```

# 6. ★やってはいけないこと
```
★新しい台帳（`*.jsonl`）を作る ／ ★新しい状態語を作る ／ ★`set_status` に検査を足す（★既に fail-closed）
★`_MAP` に触る（★`JUDGE_REQUIRED` の件は ★裁定待ち。★ここで直さない）
★S-3 の依頼文に触る ／ ★production を Claude が直接 書く（★§2 は ★2DER に作らせられない配線なので
   ★★★例外として IMPL が書く。★書いた行数を★必ず報告する）
★commit する ／ ★.md で成果を報告する（★台帳の値が動く形で置く）
```

# 7. ★報告
```
1 ★書いた行数（★§2 は Claude が書く例外なので ★必ず数える）
2 ★受入①②③ の当否 ／ 3 ★予告の当否 ／ 4 ★再投入した回数と理由
5 ★`set_status` が `None` を返した場合は ★逐語
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①先に `D-201` §4 を訂正する——S-3 を `/api/ingest` で戻すことはできない。叩いて確かめた返り値は2回とも `ValueError: no Claude ingest for op=BLOCKED` で、原因は `_MAP` の全8キーに `JUDGE_REQUIRED` が無いこと。∴ S-3 は誰の手番でもなく、判定を書いても入れる口が無い。私は勝手に繋がないが「設計/監査の手番」と書かれたままにもしない ②C-1 は新しい入口も関数も台帳も作らず、契約と同じマーカー方式（決定論・LLM 非経由）で進捗を運ぶ ③マーカーは `<<<2DER:PROGRESS>>>` … `<<<2DER:END>>>` で、item / status / actor / stage を持ち、欠けたら `ValueError`（主体欄は必須。`UNKNOWN` は値として書けるが「書かなかった」とは区別する）④書き込みは既存の `set_status` をそのまま呼ぶ。`STATUSES` 外や存在しない id は既に `None` で fail-closed なので検査を足さない ⑤やることは `progress_seal.py` 1本と `submit.py` の契約封印の隣で1回 呼ぶことと submit 応答へのキー追加1つだけ。`_MAP` や検査系には触らない ⑥受入は front door から1件 書けて `/api/roadmap` で読め、.md を増やさずに現在地が言えること。対象 item は実在するものを選び、予告を投入前に書く ⑦同時に廃止するのは「進捗を .md に書く運用」と「人が set する自己申告値」で、通らなければ廃止しないと書いた ⑧§2 は 2DER に作らせられない配線なので IMPL が書く例外とし、書いた行数を必ず報告させる。**
