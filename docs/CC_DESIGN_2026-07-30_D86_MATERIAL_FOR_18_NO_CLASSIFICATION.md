# 設計/監査 → MGR（写: Taka / IMPL）: **D-86 — 18件の材料（★分類していない）。★10項目のうち4項目は正式経路から取れない**

- `BUILD_ROLE: 参照`（**調査のみ。★実装していない・★投入していない・★台帳を直読していない・★実装ファイルを読んでいない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-30 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8`）** / **裁定**: `CC_MGR_2026-07-30_D82_WITHDRAWN_AND_EVIDENCE_ORDER.md` §3 ／ `CC_MGR_2026-07-30_D83_SCOPE_NARROWED_REGISTER_DONT_FIX.md` §2
- **取得経路（★正式経路のみ）**: `GET /api/tasks` ／ `GET /api/state?task_id=` ／ `GET /api/resolve?id=`

## 0. ★結論
> **① ★私は1件も分類していない。** **★「練習」「本物」「削除可能」と書いていない。**
> **② ★10項目のうち4項目は、正式経路から取れない**（§1）。**★埋めていない。★別経路を探しに行っていない。**
> **③ ★機械で確定できたのは2項目だけ**（§2）。**★残りは意味判断である ∴ 裁定候補**（§4）。
> **④ ★MGR の撤回済みの前提を、私も実測で確かめた: ★全155件で全文一致は0組。★本文に「練習」と在るものは0件。**

---

## 1. ★正式経路から取れない項目（★4つ。★埋めない）
| # | 項目 | 実測 |
|---|---|---|
| **3** | **作成元と作成時刻** | **★取れない**（`/api/state` にも `/api/resolve` にも欄が無い。★D-71 の実測と一致） |
| **4b** | **状態遷移** | **★取れない**（現在状態は取れる。★遷移の並びを返す欄が無い。`/api/resolve` は `events` の★件数だけ返す） |
| **7** | **成果物または完了記録** | **★取れない**（18件とも `JUDGE_REQUIRED` で完了しておらず、成果物を返す欄が無い） |
| **10** | **置換・廃棄・閉鎖を示す正式記録** | **★取れない**（そういう記録を返す経路が無い） |

> **★止まってよい場所①に当たった**（D-82 §3-2-1）。**★ただし D-83 §2 が「表示に要らない項目は取れなくてよい。取れないと書いて先へ進む」と定めたので、★止めずに先へ進む。**
> **★別経路を探しに行っていない。** **★台帳も実装ファイルも読んでいない。**

## 2. ★機械で確定できたもの（★2項目）
### 2-1. ★項目9 全文一致 — ★0組
```
再現（★正式経路・全155件・打ち切り無し）: GET /api/tasks → 155件、各 goal の sha256
★全155件で全文一致（ハッシュ一致）: ★0組
★18件が絡む組: ★無し
goal が取れなかった: ★0件
```
> **★「重複が何組もある」は成立しない。★18件内だけでなく、★全155件で0組である。**

### 2-2. ★項目8 明示記載 — ★本文に在る文字列だけを数えた（★推測しない）
```
再現（18件の goal を全文で走査・打ち切り無し）:
  テスト  11件 ／ test 4件 ／ ★使い捨て 3件 ／ probe 2件 ／ PROBE 2件 ／ 破棄 2件
  ★練習   ★0件      ← ★「練習と使い捨ての15件」は成立しない
  ★どの語も1つも当たらない: ★2件
```
> **★ここで言えるのは「★その文字列が本文に在る」だけである。**
> **★「だから練習である」「だから消してよい」は★意味判断である。★私は書かない。**
> **★特に「テスト」11件は、★『テストを走らせて』のような依頼にも当たる。★語の出現は用途を決めない。**

## 3. ★18件の材料（★1件ずつ・★依頼全文。★先頭N字にしていない）

### 1. `TASK-2DER-C12E4A3E`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-C12E4A3E` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `AUDIT` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **8件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `61124d077a08`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（208字・★そのまま）:**
```
一時workspace内に、JSONLファイルを読み込み、総レコード数、正常なJSON行数、不正な行数、トップレベルキーごとの出現回数をJSON形式で出力するPython CLIツールを作成してください。標準ライブラリだけを使用し、入力ファイルが存在しない場合と不正JSON行を含む場合のテストも作成して実行してください。本番repoや既存ledgerは変更せず、成果物、テスト結果、使用方法をDSへ返してください。
```

### 2. `TASK-2DER-53544250`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-53544250` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `AUDIT` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **9件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `43f3929baedc`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（201字・★そのまま）:**
```
一時作業領域に、JSONLファイルを読み込み総レコード数・正常JSON行数・不正行数・トップレベルキー出現回数をJSONで出力するPython CLIツールを作成してください（Runtime Supervisor Phase1 live再実行）。標準ライブラリのみ、ファイル不存在と不正JSON行のテストも作成・実行し、本番repoや既存ledgerは変更せず成果物・テスト結果・使用方法をDSへ返す。
```

### 3. `TASK-2DER-C003ACBD`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-C003ACBD` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `ad2fb934103b`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（70字・★そのまま）:**
```
JSONLの各行の文字数の平均をJSON出力するCLIを作成（標準ライブラリのみ、不存在/不正JSONのテスト付き, adj-live-a）
```

### 4. `TASK-2DER-CB6004D1`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-CB6004D1` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `37891cae8e77`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（65字・★そのまま）:**
```
CSVを読み列ごとの欠損数と型をJSON出力するCLIを作成（標準ライブラリのみ、不正CSVのテスト付き, adj-live-b）
```

### 5. `TASK-2DER-BE6F2D65`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-BE6F2D65` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **8件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `9a2941e27a27`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（62字・★そのまま）:**
```
テキストの上位N頻出単語をJSON出力するCLIを作成（標準ライブラリのみ、空ファイルのテスト付き, adj-live-c）
```

### 6. `TASK-2DER-08FB7C7D`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-08FB7C7D` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `861722e2004b`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（57字・★そのまま）:**
```
JSONLの各行の文字数の平均をJSON出力するCLI（標準ライブラリ, 空/不正JSONのテスト付き, n7a）
```

### 7. `TASK-2DER-3E7DD929`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-3E7DD929` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **10件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `a363e6d41fea`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（49字・★そのまま）:**
```
CSVの列ごと欠損数をJSON出力するCLI（標準ライブラリ, 不正CSVのテスト付き, n7b）
```

### 8. `TASK-2DER-F3919F3E`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-F3919F3E` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `abad35162129`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（51字・★そのまま）:**
```
テキストの上位N頻出単語をJSON出力するCLI（標準ライブラリ, 空ファイルのテスト付き, n7c）
```

### 9. `TASK-2DER-79ADDBBE`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-79ADDBBE` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `AUDIT` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **12件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `b8def858245d`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（129字・★そのまま）:**
```
一時作業領域にJSONLファイルを読み込み、総レコード数・正常JSON行数・不正行数・トップレベルキー出現回数をJSON出力するPython CLIツールを作成。標準ライブラリのみ、ファイル不存在と不正JSON行のテストも作成し実行。（adj-run j0）
```

### 10. `TASK-2DER-F7DA824D`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-F7DA824D` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `4eb3aed4d71b`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（142字・★そのまま）:**
```
一時作業領域にJSONLファイルを読み込み総レコード数と不正行数をJSON出力するPython CLIを作成。標準ライブラリのみ。特にファイルが存在しない場合に非ゼロ終了することを検証するテストと、不正JSON行のテストを作成し実行する。（missing-file live mf1）
```

### 11. `TASK-2DER-F00BBB50`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-F00BBB50` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `テスト` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `b534abc1b8b0`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（150字・★そのまま）:**
```
一時作業領域にJSONLファイルを読み込み総レコード数と不正行数をJSON出力するPython CLIを作成。標準ライブラリのみ。ファイルが存在しない場合に非ゼロ終了することを検証するテストと不正JSON行のテストを作成し実行する。（missing-file live activation mf2）
```

### 12. `TASK-2DER-FE81B124`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-FE81B124` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `AUDIT` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **12件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | **★どの語も無い** |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `042e7ce459ab`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（240字・★そのまま）:**
```
JSONLファイルを読み込み、指定キーの数値の平均を計算するPython CLIツール src/cli.py を作成してください。各行のJSONを検証し、壊れた行はstderrに'MALFORMED line N'として記録してスキップ、存在しないファイルが指定された場合はstderrに'ERROR: input file not found'を出力しexit 2で終了すること。[run-marker 2026-07-15 env-signal-active re-exec]
```

### 13. `TASK-2DER-CD0B5D9B`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-CD0B5D9B` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | **★どの語も無い** |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `e6329991446e`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（238字・★そのまま）:**
```
JSONLファイルを読み込み指定キーの数値の平均を計算するPython CLIツール src/cli.py を作成してください。各行のJSONを検証し壊れた行はstderrに'MALFORMED line N'として記録してスキップ、存在しないファイル指定時はstderrに'ERROR: input file not found'を出力しexit 2で終了。[worker-fixed-run 2026-07-15T3 fresh-taskid nested-target]
```

### 14. `TASK-2DER-45B39E5D`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-45B39E5D` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **8件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `test` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `3347f71cf6c9`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（3615字・★そのまま）:**
```
IMPLEMENT ITEM-2DER-OFFRAMP-BOUNDED-PATCH-BRIDGE (Evidence-Bound Patch Transfer and Application) as a SINGLE new standalone Python module (Python standard library ONLY), created as a brand-new file in a sandbox workspace. This is a NEW module (not a modification of any existing file), so it is producible under DE-0341 SANDBOX_ONLY.

AUTHORITY: moratorium DE-0344 is partially lifted by DE-0348 for EXACTLY these 7 gaps; non_goals are inviolable.

OBJECTIVE (DE-0342/0343 verbatim): Establish a path by which a change generated by a sandbox worker is bound to base commit / allowed files / patch fingerprint / authority token and applied in a limited way after validation, WITHOUT letting the worker write to the real repo directly.

TWO-PHASE STRUCTURE (required, from DE-0341 constraint that generation(sandbox) and application(host) cannot share a process):
  Phase-GEN (sandbox, worker권): record target base commit hash; produce the change as a unified diff (do NOT write the real repo); emit a diff artifact carrying {allowed_files, base_commit, fingerprint}.
  Phase-APPLY (host, separate authority, OUTSIDE worker권): receive diff artifact; verify base_commit match / allowed_files / fingerprint; dry-run apply on a working copy; run real test; present diff+test and WAIT for Taka approval (STOP here); on approval do limited apply + record an application execution event.

IMPLEMENT EXACTLY THESE 7 GAPS (and nothing else; do NOT re-implement existing assets authority-token-binding or git-commit-separation — reference them):
  g-a base commit/hash binding: bind the diff artifact to a base commit hash.
  g-b canonical unified diff artifact: a single fixed schema for the diff artifact.
  g-c patch fingerprint: a hash of the diff content (tamper detection).
  g-d dry-run apply: attempt apply on a working copy before real apply.
  g-e limited patch application: apply ONLY within allowed_files.
  g-f applied-patch rollback: revert an applied patch back to the base commit state.
  g-g application execution event: record the apply as a Runtime-Supervisor-style execution event.

NON_GOALS (INVIOLABLE — do NOT implement any of these): autonomous git; automatic commit; automatic push; unbounded repository write; worker direct repo write; Claude Code normal implementation substitution. The bridge stops at patch application; commit/push are OUT of scope (off-ramp: commit proposal only).

SCOPE: single module only. No new pipeline / state machine / ledger family / ID family / sidecar / parallel path. Application must be AFTER Taka approval; zero real-repo write before approval (dry-run on working copy only).

ACCEPTANCE TESTS (self-contained test file that IMPORTS the real module — NO self-stub written in setUp):
  T-1 allowed_files diff with matching base_commit + fingerprint passes dry-run -> real test -> apply.
  T-2 applied-patch rollback correctly returns to base-commit state.
  T-3 application execution event is recorded as a Runtime-Supervisor-style event.
  CF-1 a diff including a file OUTSIDE allowed_files -> explicit REJECT + finding (NOT silent skip).
  CF-2 base_commit mismatch (stale diff) -> REJECT.
  CF-3 fingerprint tamper (diff content != declared fingerprint) -> REJECT.
  CF-4 injection defense: detect a diff containing changes unrelated to the spec objective; minimal impl MAY use the allowed_files whitelist, but the PLAN must state WHERE diff-vs-spec agreement is checked.
  T-CANON tests run through the real module's canonical path; no self-referential stub generation in setUp.

DELIVERABLE: one new module file + one test file, stdlib only, sandbox workspace.
```

### 15. `TASK-2DER-B14D7ACA`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-B14D7ACA` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `test` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `cf74e82580b3`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（3168字・★そのまま）:**
```
IMPLEMENT a NEW standalone reusable Python module (create a brand-new file). Build the SINGLE standalone stdlib module `patch_bridge.py` (new file, sandbox, Python stdlib ONLY) + one test file `test_patch_bridge.py`. Prior attempts failed on real code defects; fix EXACTLY the enumerated defects. Authority: DE-0348 partial lift (7 gaps).

=== CODE: fix EXACTLY these defects (nothing else) ===
CD-1: apply/dry_run_apply MUST strip the unified-diff path prefixes 'a/' and 'b/' (a diff line '+++ b/file1.txt' targets file1.txt in working_dir, NOT working_dir/b/file1.txt). Prior code raised FileNotFoundError on b/file1.txt.
CD-2 (ALLOW-LIST): validate_artifact MUST reject a diff whose touched files are not ALL in allowed_files (whitelist). Parse the diff's target files; if any is outside allowed_files -> raise ValueError naming the offending file. Explicit reject, NOT silent skip. This same allow-list check IS the CF-4 injection defense.
CD-3: validate/apply MUST reject when the artifact base_commit != the expected base commit of the working copy -> raise ValueError mentioning base_commit.
CD-4: keep the existing fingerprint check (it correctly raises ValueError 'Fingerprint mismatch') UNCHANGED.

=== TEST: EXACT set, no invention (HARD constraint) ===
The test file MUST define EXACTLY these 8 test functions and NO OTHERS:
  test_t1, test_t2, test_t3, test_cf1, test_cf2, test_cf3, test_cf4, test_t_canon
DO NOT define test_missing_file_case, test_malformed_json_case, or ANY other function whose name starts with 'test_'. If any additional test_* function appears, the PLAN is INVALID. If you think more verification is needed, put it in unresolved_assumptions and DO NOT implement it.
- test_t_canon (T-CANON): import the real patch_bridge module (NO self-stub written in setUp).
- test_cf3 assertion MUST be: an exception is raised AND its message contains 'fingerprint' case-INSENSITIVELY (code raises 'Fingerprint mismatch').
- test_cf1: a diff touching a file outside allowed_files -> expect reject naming that file.
- test_cf2: base_commit mismatch -> expect reject mentioning base_commit.
- test_cf4: a diff also touching an unrelated file outside allowed_files -> expect reject (allow-list).

=== GAPS (the 7, do not exceed) ===
base-commit binding, unified diff artifact, patch fingerprint, dry-run apply, limited application (allow-list), applied-patch rollback, application execution event.

=== INVARIANTS ===
Single module + one test, stdlib ONLY, sandbox workspace, target_repositories=[]. NON_GOALS INVIOLABLE: no autonomous git / auto commit / auto push / unbounded repo write / worker direct repo write. Apply only after approval; dry-run on a working copy only.

=== PRIOR DIAGNOSTIC (verbatim) ===
CF-1 attack diff '+++ b/file2.txt' (file2.txt outside allowed=['file1.txt']) -> was NOT rejected [DEFECT to fix].
CF-2 base_commit='wrong_commit' -> was NOT rejected [DEFECT].
CF-3 fingerprint='tampered_hash' -> ValueError 'Fingerprint mismatch' [CORRECT; test assertion had wrong case].
CF-4 diff '+++ b/unrelated.txt' -> was NOT rejected [DEFECT].
T-1/2/3 -> FileNotFoundError '.../working/b/file1.txt' (prefix not stripped) [DEFECT].
```

### 16. `TASK-2DER-9BBB57AC`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-9BBB57AC` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `DISPOSE` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | **★空** |
| **6 実行履歴** | events **7件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 **★無し** |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `使い捨て` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `add9da5447fe`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（536字・★そのまま）:**
```
以下の仕様に従い、新規ファイル twoder/select_and_create.py を実装せよ（BUILD_CAPABILITY / 新規コード実装）。目的: 欠損辺①→②の producer 呼び手1本。既存2面 task_selector.select_next と dw.workcell.create_task を繋ぐ。5手: (1)使い捨て承認トークンを検証・消費し無ければ即終了 (2)task_selector.select_next で勝者ITEMを得る (3)execution_admissionを新規再計算 (4)封印フィールドを付与 (5)dw.workcell.create_taskを呼ぶ。不変条件: 1トークン=最大1CREATE、admit不合格はfail-closed(CREATEせず拒否理由をruns/へ)、sole writer規律不変(書くのはworkcell.pyのみ)、新台帳を起こさない。参照実装は twoder/submit.py:408 のcreate_task呼出。権限はauthority.POLICY AUTONOMOUS_TASK_CREATION=REQUIRES_APPROVAL。典拠 DE-0492。
```

### 17. `TASK-2DER-6E2C9F16`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-6E2C9F16` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `AUDIT` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | source_refs `["DE-0505"]` |
| **6 実行履歴** | events **12件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 `DW_IMPLEMENTATION` |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `使い捨て` / `probe` / `PROBE` / `test` / `破棄` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `7e59f1368d85`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（1112字・★そのまま）:**
```
PROBE-PIPE-01 — 経路実証用の使い捨てタスク(BUILD_CAPABILITY / 新規コード実装)。
実装対象: twoder/probe_pipe.py。probe_stamp() は実 clock から取得した時刻を含む dict を返す。時刻を自前生成してはならない(骨格の import に束縛)。
受入は同梱 IMMUTABLE_TESTS の全通過のみ。成果物は破棄してよい。

<<<2DER:SKELETON>>>
from twoder.failure_memory import _now as _REAL_CLOCK


def clock():
    return _REAL_CLOCK()


def probe_stamp():
    # <<<FILL:body>>>
    raise NotImplementedError
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
import datetime
import importlib

MOD = "twoder.probe_pipe"


def _is_iso8601(v):
    if not isinstance(v, str):
        return False
    try:
        datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def test_returns_ok():
    m = importlib.import_module(MOD)
    assert m.probe_stamp()["ok"] is True


def test_at_is_iso8601():
    m = importlib.import_module(MOD)
    assert _is_iso8601(m.probe_stamp()["at"])


def test_clock_binding_is_real():
    m = importlib.import_module(MOD)
    real = m.__dict__["_REAL_CLOCK"]
    assert getattr(real, "__module__", MOD) != MOD, "clock が自作定義"
<<<2DER:END>>>

```

### 18. `TASK-2DER-8ADC31CF`
| 項目 | 値 |
|---|---|
| **1 task_id** | `TASK-2DER-8ADC31CF` |
| **3 作成元/作成時刻** | **★取れない** |
| **4 現在状態** | `JUDGE_REQUIRED` ／ 直前の操作 `AUDIT` ／ **状態遷移は★取れない** |
| **5 EGL 記録** | source_refs `["DE-0505"]` |
| **6 実行履歴** | events **12件**（`/api/resolve`）／ `etrace_run_id` **★無し** ／ 取得方法 `DW_IMPLEMENTATION` |
| **7 成果物/完了記録** | **★取れない** |
| **8 明示記載** | `使い捨て` / `probe` / `PROBE` / `test` / `破棄` |
| **9 全文一致** | **★他の154件と一致なし**（sha256 `9f366636e095`） |
| **10 置換/廃棄/閉鎖の正式記録** | **★取れない** |

**2 依頼全文（1112字・★そのまま）:**
```
PROBE-PIPE-02 — 経路実証用の使い捨てタスク(BUILD_CAPABILITY / 新規コード実装)。
実装対象: twoder/probe_pipe.py。probe_stamp() は実 clock から取得した時刻を含む dict を返す。時刻を自前生成してはならない(骨格の import に束縛)。
受入は同梱 IMMUTABLE_TESTS の全通過のみ。成果物は破棄してよい。

<<<2DER:SKELETON>>>
from twoder.failure_memory import _now as _REAL_CLOCK


def clock():
    return _REAL_CLOCK()


def probe_stamp():
    # <<<FILL:body>>>
    raise NotImplementedError
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
import datetime
import importlib

MOD = "twoder.probe_pipe"


def _is_iso8601(v):
    if not isinstance(v, str):
        return False
    try:
        datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def test_returns_ok():
    m = importlib.import_module(MOD)
    assert m.probe_stamp()["ok"] is True


def test_at_is_iso8601():
    m = importlib.import_module(MOD)
    assert _is_iso8601(m.probe_stamp()["at"])


def test_clock_binding_is_real():
    m = importlib.import_module(MOD)
    real = m.__dict__["_REAL_CLOCK"]
    assert getattr(real, "__module__", MOD) != MOD, "clock が自作定義"
<<<2DER:END>>>

```

---

## 4. ★機械と意味の分離（★D-82 §3-1-4）
| ★機械で確定できる | ★意味判断が要る（＝裁定候補） |
|---|---|
| **本文に `使い捨て` という文字列が在る（3件）** | **★その依頼が使い捨てだったか** |
| **本文に `probe`/`PROBE` が在る（2件・重複あり）** | **★probe が「捨ててよい」を意味するか** |
| **本文に `テスト`/`test` が在る（11件/4件）** | **★それが「動作確認の依頼」か「テストを走らせる依頼」か** |
| **どの語も無い（2件）** | **★それが「本物」を意味するか** |
| **全155件で全文一致0組** | — |
| **18件とも `JUDGE_REQUIRED` で完了記録が無い** | **★止まっている理由**（`G-72`＝裁定役が割り当てられていない） |

> **★裁定候補として上げるのは、右の列だけである。** **★私は左の列しか確定していない。**
> **★D-83 §2「表示成立に必要な裁定候補だけ」に照らすと、★表示に必要なのは `G-72`（裁定役が誰か）だけである。**
> **★18件の一件ごとの扱いは、★表示の成立に要らない。** **∴ ★私からは裁定に上げない。**

## 5. ★私が守ったこと / 確かめていないこと
| ★守った | |
|---|---|
| 分類していない | **★「練習」「本物」「削除可能」と1件も書いていない** |
| 削除していない | **★読み取りのみ。★投入していない** |
| 正式経路のみ | **`GET /api/tasks` `/api/state` `/api/resolve` の3つだけ** |
| 埋めていない | **★取れない4項目を「★取れない」と書いた** |
| 広げていない | **★この調査から新しい設計を出していない**（D-83 §2-7） |

| ★確かめていない | |
|---|---|
| **`events` 件数の中身** | **★何が起きたかは見ていない**（件数だけ取れる） |
| **他の137件との関係** | **★全文一致以外は見ていない** |
| **本文の意味** | **★読んでいない。★語の出現だけ数えた** |
