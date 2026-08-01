# 【実測 / `EVO-0027` 受入(1)】本文を通す口を足した — **本文はまだ出ていない（成功走行が要る・手番は MGR/Taka）**

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 06:4x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0027_BUILD_SPEC_ARTIFACT_BODY.md`

---

# 1. 変更

```
twoder/generate_via_runner.py  +2 / -1（:243 の成功戻りに "artifact": artifact。:234 で取得済 ∴ 取りに行っていない）
twoder/webui.py                +2 / -1（test_result に "artifact" 1欄）
合計 4挿入 2削除。artifact_sha256 は消していない・改名していない。本文の要約・切り詰めはしていない（全文か None）。
ART- 側（cc_register 退役条件）には触っていない。新しい台帳・エンドポイント・状態語なし。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (1) | 走行後 `test_result.artifact` に本文 | **測れない** | §3 |
| (2) | 本文の sha256 が `artifact_sha256` と一致 | **測れない** | (1) が出てから |
| (3) | `artifact` が `None` でも壊れない | **○** | `DE042DE9`(COMPLETE) / `816D6F68`(READY_FOR_AUDIT) とも `/api/state` が従来どおり引ける |
| (4) | 名指しの2本だけ走らせる | **○** | `twoder/test_generate_via_runner_spec.py` と `twoder/test_contract_read_spec.py` → **23 passed in 0.17s**。**61本は走らせていない** |
| (5) | 応答が太る量 | **○（太っていない）** | `DE042DE9` 17,030字 → **17,030字**／`816D6F68` 9,692字 → **9,692字**（**±0**） |
| (6) | 戻せる | **○** | 手で2行を戻した版が両ファイルとも `HEAD` と**バイト一致** |

# 3. (1)(2) が測れない理由

```
本文が載るのは generate() の★成功戻り(:243)だけである。
  816D6F68 → SKELETON_VIOLATION 側(:240)へ入る ∴ 通らない
  DE042DE9 → COMPLETE ∴ もう走らない（記録は追記なので遡っても出ない）
∴ 人が封入した契約つきの新しい依頼で成功走行を1回 起こす必要がある。
★私は走行を起こしていない（手番は MGR/Taka・SPEC §3 と同じ）。「通った」とは書かない。
★(5) が ±0 なのは この裏返しである＝ 太らなかったのではなく ★載る走行がまだ無い。
   本文が載れば その分だけ確実に太る（成果物1本ぶん）。太り方の測定は 成功走行の後に要る。
```

# 4. 走行・戻し方

```
webui 再起動を確認（9項目 #5）: 起動 06:38:54 > webui.py 06:38:01 / generate_via_runner.py 06:37:58。
走行 0・task 増 0・:8005 を叩いていない・commit していない・台帳を直読していない。
戻し方: ① generate_via_runner.py の成功戻りから `"artifact": artifact` を消して1行に戻す
        ② webui.py の `"artifact": gr.get("artifact")` の1行を消す
        ※ commit 後は `git checkout --` では戻らない。
```
