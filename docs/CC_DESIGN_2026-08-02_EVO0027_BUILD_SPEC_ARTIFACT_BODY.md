# 【BUILD SPEC】`EVO-0027` 受入(1) — **★成果物の本文を front door まで通す（★2箇所・足すだけ）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 06:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§7）** ／ **★3値 確認済（★§0）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0027` の `status_note`（逐語:「★受入の1件目は『artifact の本文を front door から取り出せること』」）
- **★書く前に測った**: `GET /api/claude_packet` `GET /api/resolve` を叩き、コードを逐語で読んだ。**★走行 0・★task 増 0・★commit 0**

---

## 0. ★3値（★受入(1) が実装可能か）

| 問い | 3値 | ★逐語の根拠 |
|---|---|---|
| 成果物の本文は front door から読めるか | **★無い** | `GET /api/claude_packet?task_id=TASK-2DER-DE042DE9` に在るのは `artifact_sha256=8d7044b2…` と `artifact_head=None` **だけ**。本文の欄が無い |
| 本文は生成時に手元に在るか | **★在る** | `generate_via_runner.py:151-155` が workspace の成果物を**読んでいる**／`:165` の正規化に `"artifact": artifact` を**載せている** |
| 捨てているのは欠陥か | **★★設計どおり** | 隔離（規律 第2章）＝ tempfile 配下で消える形。`generate()` の成功戻り（`:243`）は `{ok, run_id, artifact_sha256, reason, contract_source}` で、**本文を渡す口を最初から作っていない**。★★バグではない |

```
★★∴ ★「読む口を足すだけ」では ★★達成できない。★渡す口（★書き手）を ★2箇所 足す必要がある。
★★★ただし ★取りに行く必要は無い（★本文は既に `res` の中に在る）＝ ★★作らない・受け取って渡すだけ。
```

## 1. ★★MGR の等式は成り立たない（★測った）

裁定の逐語:「★これは cc_register.py の退役条件(front door から ART- の本文が返る)と同じ ∴ ★通れば あの借金も畳める」

```
★実測: ★`GET /api/resolve?id=ART-ae789b58f7` → ★`resolved: true` ／ 中身は
        ★`repo_name: twoder` / `relative_path: webui.py` / `absolute_path: /home/takasan/twoder/webui.py`
        ★`current_git_commit` / `git_blob_sha` / `content_hash`
★★∴ ★`ART-` は ★★repo 上の実ファイルの登記である（`artifact_registry.py:12` 逐語「ARTIFACT_ID is STABLE per conceptual file」）。
★★★本文は ★`absolute_path` に ★在り続ける（★消えない）。
★★★★worker 成果物は ★tempfile に出て ★消える。★★★★別物である。
```

| | `ART-` の本文 | worker 成果物の本文 |
|---|---|---|
| 実体 | ★repo のファイル（★在る） | ★tempfile（★消えた） |
| front door に足す物 | ★path を読んで返す口 | ★★生成時に本文を**通す**口 |
| 難度 | ★小 | ★中（★書き手2箇所） |

```
★★★★∴ ★本件が通っても ★cc_register は ★★畳めない（★★裁定の「同じ」は ★誤り）。
★★★★★規律9 により ★(1-B)=ART- は ★★今回 入れない（★1件のために2件 増やさない）。★別件として残す。
```

## 2. やること（★2箇所・★足すだけ）

### 2-1. `twoder/generate_via_runner.py:243`（★成功の戻り）
```python
    return {"ok": True, "run_id": run_id, "artifact_sha256": artifact_sha256, "reason": "",
            "contract_source": contract_source, ★"artifact": artifact}
```
```
★`artifact` は ★`:234` で ★既に取り出されている（★分岐の前）∴ ★取りに行かない・★1行も増やさない
```

### 2-2. `twoder/webui.py`（★`wr["test_result"]` の組み立て）
```python
                              "artifact_head": gr.get("artifact_head"),
                              ★"artifact": gr.get("artifact")},      # ← ★既存の artifact_head と同じ流儀
```
```
★読む口は ★★既存（`/api/state` と `/api/claude_packet` の `test_result` に そのまま載る）
★★★新しいエンドポイント・状態語・台帳を ★作らない。★戻し方＝★足した2行を消す。★可逆
```

## 3. ★★先に言う：これは測れない（★feasibility）

```
★`TASK-2DER-DE042DE9`（★COMPLETE・7本 全通・sha256=8d7044b2）の ★★本文は ★★既に消えている。
★★台帳は追記なので、★直しても ★★遡っては出ない（★★本日 既に1度 踏んだ形と同型）。
★★★∴ ★受入は ★★「直した後に走らせた ★新しい走行」でしか測れない。
★★★★その走行には ★人が封入した契約つきの依頼が要る ＝ ★★手番は MGR/Taka。★実装は ★機構だけ作る。
```

## 4. 受入

```
★(1) ★直した後の走行で ★`GET /api/state` の `test_result.artifact` に ★★本文が在る
     ★逐語で ★先頭3行 と ★末尾3行 を持ち帰る
★(2) ★★捏造でないことを ★決定論で確かめる: ★本文の sha256 を計算し ★`artifact_sha256` と ★一致
★(3) ★通っていない走行で壊れない（★`artifact` が `None` でも ★従来どおり動く）
★(4) ★走らせる試験は ★★名指しの2本だけ: ★`test_generate_via_runner_spec.py` ／ ★`test_contract_read_spec.py`
     ★★61本は走らせない。★走らせた名前を書く
★(5) ★★応答が太る量を測る: ★`/api/state` の字数を ★直す前 と ★直した後で ★両方 書く
★(6) ★戻せる（★2行を消したら元に戻る）——★戻して確かめ、★また足す
★★★★★予告を投入前に書く: ★変更行数 ／ ★どの task で測るか
```

## 5. ★受入(2)(3) は ★今回 書かない（★理由）

```
★(2)=画面5点 と (3)=「2DER が作った物であること」は ★★(1) が通って ★本文が出てから でないと ★測れない。
★★★∴ ★順番の問題であって ★降りたのではない。★(1) が通り次第 ★私が続きの SPEC を書く。
```

## 6. ★★裁定に1つ 書けない値が在る（★訂正が要る）

```
★裁定の逐語:「★その監査結果は ITEM の status_note に書く(★actor=DESIGN stage=VERIFY)」
★★実測（`twoder/progress_seal.py:20-21` 逐語）:
   ★ACTORS = {"2DER", "Claude", "MGR", "Taka", "External", "UNKNOWN"}   ← ★★"DESIGN" は無い
   ★STAGES = {DETECT, PLAN, IMPLEMENT, EXECUTE, VERIFY, ADJUDICATE, RECORD, RESPOND} ← ★"DESIGN" は無い
★★`:44-45` 逐語: ★`raise ValueError("progress actor not allowed: %r")` ＝ ★★投入すれば ★弾かれる。
★★★∴ ★私は ★★`actor=Claude stage=VERIFY` で書く（★書ける値で運用する）。
★★★★`ACTORS` に1語 足すのは ★★増やすこと ∴ ★★MGR の裁定を待つ。★私は増やさない。
```

## 7. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/state` の `test_result.artifact`（★受入(1)）
2 読めるなら書けるか＝★本件は「書く口を足す」側そのもの
3 理由を捨てない＝★★本件は「本文を捨てている」を直すもの
4 作っていないのでは＝★★本文は既に `res` に在る（★`:151-165` 逐語）∴ ★取りに行かない
5 走ったか＝★実装が webui 再起動を確かめる
6 名前＝★`artifact`（★`generate_via_runner` の既存の欄名と ★同じ・改名しない）
7 依頼と試験の矛盾＝★本件は機構 ∴ 該当なし
8 計器が自分を数えないか＝★★受入(2) で sha256 を突き合わせる＝★自己申告でない
★9 増える代わりに廃止＝★★「2DER が作った物を ★sha256 でしか確認できない」運用を畳む。
   ★★★★ただし ★MGR が挙げた「生JSONを人が読む運用」の廃止は ★★(2) が通るまで ★畳めない（★嘘を書かない）
```

## 8. 禁止
```
★`artifact_sha256` を消す・改名する ／ ★本文を要約・切り詰めて記録する（★全文か None か）
★`ART-` 側（cc_register 退役条件）を ★同じ変更に混ぜる ／ ★新しい台帳・エンドポイント・状態語を作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
