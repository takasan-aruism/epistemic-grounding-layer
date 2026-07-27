# BUILD SPEC — Build 18: **`REGENERATE` を1段。修理後の初回生成**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-28_GO_REGENERATE.md`
- 対象: **`TASK-2DER-21F64D9D`**（`READY_FOR_REGENERATE`）。**`D6A93450` / `B9B4DA3B` に触らない**

## 0. ここで何が初めて起きうるか
**契約（Build 13）・権限の語彙（Build 15）・段の道順（Build 17）を越えた。**
> **∴ `run_runner` に到達しうる。** **本日ここまで、到達した観測は1件も無い。**

## 0-1. 経路の当たり（★思い込みを先に潰す）【監査:CC-α・コード構造】
`webui` の `cw` アダプタは、`REGENERATE` かつ `_last_defect_class(view) == "EXECUTION_DEFECT"` のとき **同じコードを再実行し、新規生成をしない**（DE-0324）。
```
本件は DISPOSE を経ていない（AUDIT から直行）。
∴ dispose payload が無い ∴ _tf_defect_class は None ∴ EXECUTION_DEFECT ではない
∴ 通常の生成経路（generate_via_runner.generate）に入る、と読む
```
- **【未確認】** **`_last_defect_class` が dispose 以外から値を取る可能性を私は確かめていない。**
- **★もし「同じコードを再実行」に入った場合、再実行するコードが存在しない**（`diff: null`）。**その場合は失敗するはずである。**
- **∴ どちらの経路に入ったかを、必ず観測して書くこと**（§2-3）。

---

## 1. 手順（①〜⑤を1つの作業として続けて行う）
| # | 手順 |
|---|---|
| **①** | **鮮度確認**: webui の pid / 起動時刻 と `authority.py` / `generate_via_runner.py` / `qwen_worker.py` の mtime。**起動が古ければ止めて上げる** |
| **②** | **`derive_state('TASK-2DER-21F64D9D')` が `READY_FOR_REGENERATE` であることを確認**（違えば止めて上げる） |
| **③** | **run-gate を立てる**: 同一依頼文を1回投入し、**`task_id` が同一であることを確認**（§5.3-2 の常設手順） |
| **④** | **投入前の `/tmp/2der_runner_*` を数える → `/api/run_next` を1回だけ** |
| **⑤** | **★その場で受け取る**: 増えた sandbox を特定し、**全ファイルを `dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/` へ保全**（**既存を上書きしない**）＋ `MANIFEST.json`（各ファイルの相対パス / sha256 / バイト数、元の sandbox 絶対パス、`TASK_ID`、受取時刻、前後の sandbox 数）。**そして止まる** |

---

## 2. ★出すもの（判定はしない）
1. `/api/run_next` の応答全文。
2. `derive_state` と events（実行前後）。
3. **★`regenerate` の run payload を逐語で全文**——**`test_result`（`status`/`ok`/`reason`）・`problems`・`artifact_sha256`・`diff` の有無・`contract_source`**。**要約しない・切り詰めない。**
4. **★どちらの経路に入ったか**（§0-1）: **新規生成か、同じコードの再実行か。** **判断材料（`backend` / `run_id` / `reason` の文言など）をそのまま貼る。**
5. **保全先パスと `MANIFEST.json` 全文。**
6. **成果物のファイル名と行数のみ**（**中身を貼らない・評価しない**）。
7. **投入回数**（通算・今回の理由）。
8. §3 の予想と実際。**外れに「外れた」と書く。**
9. 本番無変更・**commit しない**・冒頭に「運用方針 確認済（版: v1.9）」・定型見出し。

---

## 3. 予想を先に書く（実測前に固定・★当てに行かない）
| 項目 | DESIGN の予想 |
|---|---|
| `dispatched` / actor | **`true` / `CODING_WORKER`** |
| 経路 | **通常の生成**（`EXECUTION_DEFECT` ではないため） |
| **`run_runner` への到達** | **★到達する方に賭ける**（token gate を直したため） |
| **sandbox にファイルが出るか** | **★出る方に賭ける**（テストが落ちても生成物は書かれると読む） |
| **`test_result.status`** | **★`PASSED` にならない方に賭ける** |
| **held-out** | **判定不能の可能性が高い**（`PASSED` でなければ検査以前） |

### 3-1. 「`PASSED` にならない」に賭ける理由（当てに行かない側）
- **骨格の固定区間の決定論検査（`verify_skeleton_preserved`）と、`immutable_tests` 8本を、1回の生成で全部満たす必要がある。**
- **本日 planner は揺れている**（9C は barrier / 10・11 は成功）。**worker が1回で揃える確度を高く見積もる根拠を、私は持っていない。**
- **★これは悲観ではなく、根拠の無い楽観を避けるためである。** **外れたら「外れた」と書く。** **外れる方が良い結果である。**

---

## 4. やってはいけないこと
1. **成果物の中身を評価しない。テストを足さない。修正しない。**
2. **★受入オラクルを開封しない**（held-out は設計/監査が保持）。
3. **配置・登記・配線をしない。**
4. **2段以上進めない。**
5. **★失敗しても手で書かない。** **`problems` / `reason` を逐語で。**
6. **`run_until_barrier` を使わない。token を迂回しない。**
7. **他の2 task に触らない。新しい task を作らない。**
8. **本番コードを変更しない。**
9. **`/tmp` を消さない**（`G-17`・調査中）。
10. **`CC_REGISTER.jsonl` に試験行を書かない。**
11. **`twoder/runs/*.trace.json` を読まない。**
12. **既存の保全ディレクトリを上書きしない。**

## 5. 定型見出し（そのまま）
```
## 到達経路
- [ ] (A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て届いた。

## プロセス鮮度（実行時）
- webui pid / 起動時刻 / ソース mtime:
- [ ] 起動がソースより新しい / [ ] 古い（→ 止めた）

## 投入回数
- 本 task への通算投入回数: ___ 回 / 今回の理由: ____

## 経路（★どちらに入ったか）
- [ ] 通常の生成 / [ ] 同じコードの再実行（EXECUTION_DEFECT） / [ ] 判定材料が不足

## 結果の区分（1つに丸）
- [ ] SANDBOX_ARTIFACT_READY（成果物が出て、受け取れた）
- [ ] GENERATION_FAILED（出せなかった／テストが通らなかった）
- [ ] SKELETON_VIOLATION（骨格の固定区間が保存されなかった）
- [ ] TOKEN_GATE_BLOCKED（token gate で止まった）
- [ ] ARTIFACT_LOST（生成されたが受け取る前に失われた）
```

## 6. 位置づけ（緩めない）
- **★成果物が出ても「2DER が作れるようになった」と書かない。** **1回・1件である。**
- **供給したテストが通っても、依頼を満たした証拠ではない**（**渡していない検査が別に在る**）。
- **1回の観測で常態を判定しない。**

---
*BUILD SPEC v1.0（★実装源）。Build 18=`REGENERATE` を1段。契約・権限の語彙・段の道順を越えたので `run_runner` に到達しうる（本日ここまで到達0件）。★経路の思い込みを先に潰す=`cw` アダプタは `EXECUTION_DEFECT` のとき同じコードを再実行し新規生成しないが、本件は DISPOSE を経ていないので dispose payload が無く `EXECUTION_DEFECT` にならない、と読む【未確認】——もし再実行経路に入れば再実行するコードが存在しない（diff: null）ので失敗するはず。∴ どちらに入ったかを必ず観測して書く。手順=鮮度確認→`READY_FOR_REGENERATE` を確認→同一文の再投入で run-gate を立て `task_id` 同一を確認→sandbox 数を数えて `run_next` 1回→★その場で保全（`-regen` 別ディレクトリ・既存を上書きしない）＋MANIFEST→止まる。出すもの=応答全文／前後の derive_state／★regenerate の run payload を逐語全文（test_result/problems/artifact_sha256/diff の有無/contract_source）／★どちらの経路か／MANIFEST 全文／ファイル名と行数のみ／投入回数。★予想=到達する・sandbox にファイルは出る・**`PASSED` にならない方に賭ける**（骨格保存の決定論検査と immutable_tests 8本を1回で全部満たす確度を高く見積もる根拠が無い。悲観でなく根拠の無い楽観を避けるため。外れる方が良い結果）。禁止12項目。成果物が出ても「作れるようになった」と書かない。*
