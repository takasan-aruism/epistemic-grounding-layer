# BUILD SPEC — Build 14: **`GENERATE` を1段だけ進め、成果物を消える前に受け取る**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-27_BUILD13_RECEIVED_GO_GENERATE.md`
- 前段: `CC_DESIGN_2026-07-27_BUILD13_AUDIT.md`（契約は `CREATE` payload に封印済）

## 0. これは何か
| | |
|---|---|
| **対象** | **`TASK-2DER-21F64D9D`**（`READY_FOR_IMPLEMENTATION` / 契約つき） |
| **これは** | **`GENERATE` を1段だけ。成果物を sandbox から消える前に受け取る** |
| **これではない** | **検査しない・配置しない・登記しない・配線しない**（検査は設計/監査） |
| **触らない task** | **`TASK-2DER-B9B4DA3B`**（契約なしで `READY_FOR_AUDIT` に居る） / **`TASK-2DER-D6A93450`** |

## 0-1. 資料で確認した（MGR §1-4 の義務）
`2DER_EXECUTION_ARCHITECTURE.md`: `C-QWEN-WORKER`=`LIVE` / `SM-DW` の `READY_FOR_IMPLEMENTATION → GENERATE / CODING_WORKER / claude_barrier=False` / 成果物は `tempfile.mkdtemp(prefix="2der_runner_")` 配下（**消えうる**）。

---

## 1. 手順（①〜⑤を1つの作業として続けて行う）
| # | 手順 |
|---|---|
| **①** | **鮮度確認**: webui の pid/起動時刻 と `webui.py` / `dispatch.py` / `generate_via_runner.py` / `qwen_worker.py` の mtime。**起動が古ければ止めて上げる** |
| **②** | **投入前の `/tmp/2der_runner_*` の数を数える** |
| **③** | **`/api/submit` に Build 13 と同一の依頼文を1回**（run-gate を立てるため。**1文字も変えない。機械抽出でよい**） |
| **④** | **`/api/run_next` を1回だけ**（`{"task_id":"TASK-2DER-21F64D9D"}`）。**`run_until_barrier` を使わない** |
| **⑤** | **★その場で受け取る**: 増えた `2der_runner_*` を特定し、**全ファイルを `dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D/` へ保全**、`MANIFEST.json` を作る。**そして止まる** |

**`MANIFEST.json`**: 各ファイルの**相対パス / sha256 / バイト数**、**元の sandbox 絶対パス**、`TASK_ID`、**受け取った時刻**、`/tmp/2der_runner_*` の前後の数。

**受け取れなかったら**: 「失われた」と記録。**どこを探したか（パス）と時刻を書く。黙って再投入しない。**

---

## 2. ★出すもの（判定はしない）
1. `/api/run_next` の応答全文（`planner_outcome` の有無を含む）。
2. **`derive_state('TASK-2DER-21F64D9D')` と events。**
3. **★`generate_runs` の payload を逐語で全文**——特に **`test_result`（`status` / `ok` / `reason`）**、**`problems`**、**`artifact_sha256`**、**`contract_source`**。**要約しない。**
4. **保全先パスと `MANIFEST.json` 全文。**
5. **成果物のファイル名と行数のみ**（**中身を貼らない・評価しない**）。
6. §3 の予想と実際の表。**外れに「外れた」と書く。**
7. 各操作1回ずつ・本番無変更・**commit しない**。

---

## 3. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| `dispatched` / `actor_role` | **`true` / `CODING_WORKER`** |
| 新しい `2der_runner_*` | **1つ増える** |
| `contract_source` | **`ledger`**（packet に inline されず CREATE から引く） |
| `verify_skeleton_preserved` | **通る**（骨格は署名＋docstring のみで短い） |
| **供給した T1〜T8** | **★通る方に賭ける** |
| **held-out（`[]` `""` `0` `False` の falsy 群 / `known_prefixes` 空）** | **★少なくとも1つ落ちる方に賭ける** |
| 進行後の状態 | **`READY_FOR_AUDIT`** |

### 3-1. ★賭けを変えた理由（隠さない）
**Build 12 まで私は「worker は4状態を分けられない」に賭けていた。**
**依頼文が変わった**——**受入テストを同梱したので、通らなければ `PASSED` にならない。**
**∴ 供給分は通る方に賭け直す。** **代わりに held-out で「渡した試験に通っただけか」を測る。**
**★外れを隠すための変更ではない。** **同じ賭けを別の場所に置き直しただけである。**

---

## 4. やってはいけないこと
1. **成果物の中身を評価しない。テストを足さない。修正しない。**
2. **★受入オラクルを開封しない。** **場所も内容も見ない。**
3. **配置しない・登記しない・配線しない。**
4. **2段以上進めない**（`AUDIT` へ行かない）。
5. **失敗しても手で書かない。** **`problems` を逐語で記録して上げる。**
6. **`run_until_barrier` を使わない。token を迂回しない。**
7. **`B9B4DA3B` / `D6A93450` に触らない。**
8. **本番コードを変更しない。**
9. **トークンを文書・argv・ログに出さない。**
10. **`twoder/runs/*.trace.json` を読まない**（v1.8 で潰した経路）。
11. **★台帳（`CC_REGISTER.jsonl`）に試験行を書かない。** **試験が要るなら一時ファイルで行う**（本日2回混入した）。

## 5. BUILT に置く定型見出し（そのまま）
```
## 到達経路
- [ ] (A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て届いた。

## プロセス鮮度（実行時）
- webui pid / 起動時刻:
- ソース mtime（webui.py / dispatch.py / generate_via_runner.py / qwen_worker.py）:
- [ ] 起動がソースより新しい / [ ] 古い（→ 止めた）

## 結果の区分（1つに丸）
- [ ] SANDBOX_ARTIFACT_READY（成果物が出て、受け取れた）
- [ ] GENERATION_FAILED（worker が出せなかった／テストが通らなかった）
- [ ] SKELETON_VIOLATION（骨格の固定区間が保存されなかった）
- [ ] ARTIFACT_LOST（生成されたが受け取る前に失われた）
- [ ] REFUSED（gate に拒否された）
```

## 6. 位置づけ（緩めない）
- **成果物が出ても「2DER が作れるようになった」と書かない。** **1回・1件である。**
- **sandbox のテストが通っても、依頼を満たした証拠ではない**——**テストは我々が渡したものであり、渡していない検査が別に在る。**
- **1回の観測で常態を判定しない。**

---
*BUILD SPEC v1.0（★実装源）。Build 14=`TASK-2DER-21F64D9D`(契約つき)を `GENERATE` で1段だけ進め、成果物を消える前に受け取る。検査・配置・登記・配線はしない。手順①〜⑤を続けて行う（鮮度確認→sandbox 数を数える→同一依頼文で submit 1回→run_next 1回→★その場で `contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D/` へ保全し MANIFEST に sha256）。出すもの=run_next 応答全文／derive_state と events／★`generate_runs` の payload を逐語全文(`test_result`/`problems`/`artifact_sha256`/`contract_source`)／MANIFEST 全文／ファイル名と行数のみ(中身は貼らない)。★予想を固定=dispatched true・sandbox が1つ増える・`contract_source=ledger`・骨格保存は通る・**供給した T1〜T8 は通る方に賭ける**・**held-out(falsy 群/known_prefixes 空)は少なくとも1つ落ちる方に賭ける**・進行後 `READY_FOR_AUDIT`。★賭けを変えた理由を明記（受入テストを同梱したので通らなければ PASSED にならない∴供給分は通る方に賭け直し、held-out で「渡した試験に通っただけか」を測る。外れを隠すためでなく同じ賭けを別の場所に置き直した）。禁止=中身を評価しない・オラクル非開封・配置/登記/配線しない・2段以上進めない・手で書かない・gate 迂回なし・他 task に触らない・TRACE 横読み禁止・★台帳に試験行を書かない(本日2回混入)。区分5択。*
