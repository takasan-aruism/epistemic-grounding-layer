# BUILD SPEC — Build 12: **worker を1段動かし、sandbox 成果物を消える前に受け取る**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.8）**
- 権限: `CC_MGR_2026-07-27_PRIORITY1_APPROVED_RUN_THE_WORKER.md`（**(A) 承認・条件7点**）
- 統合設計: `CC_DESIGN_2026-07-27_PRIORITY1_UNIFIED_DESIGN.md`（`BUILD_ROLE: 参照`）

---

## 0. これは何か。何ではないか
| | |
|---|---|
| **これは** | **`TASK-2DER-B9B4DA3B` を1段進め、Qwen worker に成果物を作らせ、消える前に受け取る** |
| **これではない** | **検査しない。配置しない。登記しない。配線しない。** それぞれ B13 / B14 |
| **対象の task** | **`TASK-2DER-B9B4DA3B`**（`READY_FOR_IMPLEMENTATION` / Qwen が書いた PLAN を持つ）。**`TASK-2DER-D6A93450` には触らない** |
| **境界への寄与** | **★本線そのもの。** Taka「**外注で生成、配置するまで**」の**生成**を、初めて実際に通す |

## 0-1. 着手前の確認（10R の教訓・必須）
**実行前に、プロセスの起動時刻とソース mtime を並べて記録すること。**
```
ps -eo pid,lstart,etime,cmd | grep twoder.webui
stat -c '%y %n' twoder/webui.py dev-workcell/dw/dispatch.py twoder/live_worker_runtime.py twoder/qwen_worker.py
```
**起動がソースより古ければ、そこで止めて上げること。** **観測が無効になる。**

---

## 1. 手順（①〜⑤を1つの作業として続けて行う）

**★成果物は `tempfile.mkdtemp(prefix="2der_runner_")` 配下に出る。消えうる。** **②と④を別の作業に分けないこと。**

| # | 手順 |
|---|---|
| **①** | **投入前の `/tmp/2der_runner_*` の数を数える**（増分を特定するため） |
| **②** | **webui `/api/submit` に、Build 11 と同一の依頼文を1回**（run-gate を立てるため。**1文字も変えない**） |
| **③** | **`/api/run_next` を1回だけ**（`{"task_id": "TASK-2DER-B9B4DA3B"}`）。**`run_until_barrier` を使わない** |
| **④** | **★その場で受け取る**: 新しく増えた `2der_runner_*` を特定し、**全ファイルを `dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-B9B4DA3B/` へ保全**し、`MANIFEST.json` を作る |
| **⑤** | **止まる。** `derive_state` を記録して BUILT を出す |

### 1-1. `MANIFEST.json` に必ず入れるもの
- 各ファイルの **相対パス / sha256 / バイト数**
- **元の sandbox 絶対パス**
- `TASK_ID` / **受け取った時刻**（実時刻）
- **`/tmp/2der_runner_*` の投入前後の数**

### 1-2. 受け取れなかった場合
- **「失われた」と記録する。** **黙って再投入しない。**
- **どこを探したか（パス）と時刻を書く。**

---

## 2. ★やってはいけないこと
1. **成果物の中身を評価しない。** **テストを書き足さない。修正しない。** **検査は設計/監査（B13）。**
2. **★受入オラクルを開封しない。** **IMPL は場所も内容も見ない。**
3. **配置しない・登記しない・配線しない。**
4. **2段以上進めない。** **`GENERATE` の次（`AUDIT`）へ行かない。**
5. **★失敗しても手で書かない。** **worker が出せなかった部分を補完しない。**
6. **`run_until_barrier` を使わない。**
7. **token を要求されたら迂回しない。止めて上げる。**（**`/api/run_next` は `AUTH.gate("DW_MACHINE_DISPATCH")` を通る。前回まで未到達だった経路である**）
8. **`TASK-2DER-D6A93450` に触らない。**
9. **本番コードを変更しない。**
10. **トークンを文書・argv・ログに出さない。**
11. **`twoder/runs/*.trace.json` を読まない**（v1.8 で潰された経路）。**必要な値は API の応答から取る。**

---

## 3. 予想を先に書く（実測前に固定・後から変えない）
| 項目 | DESIGN の予想 |
|---|---|
| `AUTH.gate("DW_MACHINE_DISPATCH")` | **`auto: true`**（コード逐語 *"AUTO_EXECUTE (compute, no live-service mutation)"*）**【未確認】** |
| `dispatched` | **`true`** / `actor_role` = **`CODING_WORKER`** |
| 新しい `2der_runner_*` | **1つ増える** |
| 成果物 | **実装1ファイル ＋ テスト1ファイル** |
| sandbox のテスト | **PASS する方に賭ける**（依頼文にテストを書いて実行せよと明記したため） |
| 進行後の状態 | **`READY_FOR_AUDIT`** |
| **★4状態を正しく分けられるか** | **★分けられない方に賭ける**（`NOT_ANSWERABLE` と `NOT_FOUND` を同じにする、または `UNKNOWN` を落とす）。**ただし判定は B13。IMPL は判定しない** |

**★外れたら「外れた」と書く。** **特に最後の項目が外れたら（＝正しく分けられていたら）、それは私の賭けが外れた側であり、良い結果である。**

---

## 4. BUILT に置く定型見出し（そのまま）
```
## 到達経路
- [ ] (A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## プロセス鮮度（実行時）
- webui pid / 起動時刻:
- ソース mtime（webui.py / dispatch.py / live_worker_runtime.py / qwen_worker.py）:
- [ ] 起動がソースより新しい / [ ] 古い（→ 止めた）

## 結果の区分（1つに丸）
- [ ] SANDBOX_ARTIFACT_READY（成果物が出て、受け取れた）
- [ ] GENERATION_FAILED（worker が出せなかった／依頼と無関係）
- [ ] ARTIFACT_LOST（生成されたが受け取る前に失われた）
- [ ] REFUSED（gate に拒否された）
```

## 5. そのほか出すもの
1. `/api/submit` と `/api/run_next` の応答全文（キーを省略しない）。
2. **`derive_state('TASK-2DER-B9B4DA3B')` と events**（進行後）。
3. **worker の実行結果**（`result` に入るもの。**`test_result` があればそのまま。要約しない**）。
4. **保全先のパスと `MANIFEST.json` の内容全文。**
5. **成果物のファイル名と行数のみ**（**中身の評価をしない**。**中身の貼り付けは不要**）。
6. §3 の予想と実際の表。**外れに「外れた」と書く。**
7. **各操作1回ずつであること。**
8. 観測を書き、判定・評価・提案をしない。**commit しない。** 冒頭に「運用方針 確認済（版: v1.8）」と受領文書一覧。
9. **v1.5**: 「動く」と書くときは実行した再現コマンドと結果を併記する。

---

## 6. 位置づけ（緩めない）
- **成果物が出ても「2DER が作れるようになった」と書かない。** **1回・1件である。**
- **sandbox のテストが通っても、それは依頼を満たした証拠ではない**（テストも worker が書いている）。**独立の検査は B13。**
- **1回の観測で常態を判定しない。**

---
*BUILD SPEC v1.0（★実装源）。Build 12=`TASK-2DER-B9B4DA3B` を1段進めて Qwen worker に成果物を作らせ、消える前に受け取る。**検査・配置・登記・配線はしない**（B13/B14）。着手前にプロセス起動時刻とソース mtime を並べ、古ければ止める（10R の教訓）。手順①〜⑤を1つの作業として続けて行う（成果物は `tempfile.mkdtemp` 配下で消えうるため受け取りを分けない）——投入前の sandbox 数を数える→同一依頼文で submit 1回→run_next 1回→★その場で `contracts/out/SANDBOX_ARTIFACT-…/` へ保全し MANIFEST（各ファイルの sha256/バイト数・元 sandbox パス・受取時刻・前後の sandbox 数）→止まる。禁止=中身を評価しない・**受入オラクルを開封しない**・配置/登記/配線しない・2段以上進めない・失敗しても手で書かない・`run_until_barrier` 不使用・token を迂回しない（`/api/run_next` は `DW_MACHINE_DISPATCH` の authority gate を通る＝前回まで未到達の経路）・`D6A93450` に触らない・本番無変更・`twoder/runs/*.trace.json` を読まない（v1.8 で潰された）。予想を固定=gate は auto / `CODING_WORKER` で dispatched / sandbox が1つ増える / 実装1＋テスト1 / sandbox テストは PASS / 進行後 `READY_FOR_AUDIT` / ★4状態は分けられない方に賭ける（判定は B13）。BUILT は定型見出し（到達経路・プロセス鮮度・結果の区分4択）。成果物が出ても「作れるようになった」と書かない。*
