# 【BUILT】D-176 — **★欄を1つ足したら、その欄が埋まった。★ただし「値」は本文に0件のまま**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-31 16:4x / TYPE=BUILT
- **運用方針 確認済（版: v2.9）** ／ **実装源**: `CC_DESIGN_2026-07-31_D176_BUILD_SPEC_ADD_THE_FIELD.md`
- **`:8005` が呼ばれた**（★私は直接 叩いていない。**投入で4件／`run_next` で2件**＝`attempts=2` と一致）
- **★2DER 担当工程数の前回差分: 0**

---

# 1. ★変更した1箇所
```
twoder/build_planner.py ／ 1 hunk ／ ★2挿入・0削除
足したもの: _plan_prompt の JSON 欄の定義に ★"already_satisfied" を1つ
  '  "already_satisfied": array of strings (items that need NOT be built because they are already available; empty if none),'
★禁止語(gpu/nvidia/port/docker/disk/memory)は diff に ★0件（大小無視・打ち切り無しで走査）
★STRUCTURED_KEYS / EXECUTABLE_KEYS は diff に ★0件（★触っていない）
★「観測を使え」という指示は足していない（★器を1つ作っただけ）
```
**★欄名の理由（1行）**: **既存の語彙（`unresolved_assumptions` のような「状態を述べる欄」）に寄せ、★特定の主題語を含めずに「作らない」を書ける器にするため。**
**★先に自分で確かめたこと**: `validate_plan` は **欠けている欄しか見ない**（`build_planner.py:264-276`）＝**★未知の欄を弾く枝は無い** ∴ 欄を足しても検査は壊れない。

---

# 2. ★評価（★Taka の4点。★1と2を分ける）

## ★足した欄に実際に入ったもの（★全文）
```json
"already_satisfied": [
  "Basic process listing with PID, RSS, and command name is already available via 'ps -eo pid,rss,comm'.",
  "Basic GPU memory usage (total used/total) is already available via 'nvidia-smi' without compute apps.",
  "Basic listening ports are already available via 'ss -ltn'."
]
```

| # | 見るもの | 印 | 根拠 |
|---|---|---|---|
| **1** | **引用したか**（★値を書いただけでは不可・「既知情報として扱った」と読めるか） | **○** | **★「is already available via …」＝既知情報として明示的に扱っている。** `cites_source_ids` も `OBS-00987〜00990`（今回の投入の refs と一致） |
| **2** | **利用したか**（★「再取得不要」／「これを前提に次工程へ」に当たる記述） | **★○（境界。★下に反証も書く）** | **★既知と不足を切り分けている**: `nvidia-smi` は「compute apps 無しの合計は既知」→ 不足は `--query-compute-apps`／`ss -ltn` は既知→ 不足は `-ltnp`（プロセス対応）／`ps` の basic は既知→ 不足は拡張フィールド。**★不足だけを新規対象にする形になっている** |
| | **★反証（★同じ本の中に在る）** | | **★`steps` は `ps`・`nvidia-smi`・`ss` を★もう一度 実行する**（オプションを増やして）。**★「再取得不要」とは書いていない。** **★D-166 の厳格な線（既取得を実装対象に入れたら ×）を当てれば、★これは ×** |
| **3** | **無視した場合** | **★該当なし** | ★無視していない（欄が埋まった） |
| **4** | **★Prompt の論理整合性（最重要）** | **★下に別項** | |

## 2-1. ★受入3 相当（★重複計画）は ★×（★物差しを変えない）
```
★steps: 「'ps' を pid,user,state,vsz,rss,ppid,comm,cmdline,… で実行」← ★rss は既知（already_satisfied に自分で書いた）
★∴ `D-166` の線をそのまま当てると ★×。★「既知と不足を切り分けた」ことは ★③の判定を変えない。
★★ただし前回までと違い、★何が既知かを★自分で書き出したうえで再実行している。★この差は事実として書く。
```

## 2-2. ★「値」は本文に0件（★前回までと同じ数え方）
```
★観測値トークン24件（pid・rss の数値・VLLM::… ・qwen36_vllm）のうち、★本文に出たもの ★0件
★★`already_satisfied` の中にも ★0件 — ★書かれたのは「★どのコマンドで取れるか」＝★手段であって、★値ではない
```

---

# 3. ★Prompt の論理整合性（★§3-1 の6欄。★PASS でも「なぜ通ったか」を書く）

| 欄 | |
|---|---|
| **却下対象** | **★無し（PASS）。** ★ただし「受入3 相当は ×」を別に立てている |
| **証拠** | ★`already_satisfied` に3件が入った（★前回まで、この内容が入る欄は存在しなかった）／`cites_source_ids` は今回の refs と一致／`plan_source=QWEN_BUILD_PLANNER`・`runtime_recovery={attempts:2, 4096, RECOVERED}`／`:8005` は `run_next` で2件（attempts と一致） |
| **★入力間の矛盾** | **★2つ在る。** ①**★prompt は「Use ONLY the Python standard library」と言うが、観測ブロックの中身は外部コマンドの出力である**（★「使うな」と「これが素材だ」が同居している）②**★prompt は IMPLEMENTATION PLAN を必ず出させる**（`target_file` / `test_body` / `test_command` は必須欄）**∴「作らない」で終われる道が構造として無い** |
| **★推定原因** | **★「作らない」を書ける器が無かったことが、★観測が使われなかった理由の少なくとも一部である**（★欄を1つ足しただけで、その欄が埋まった）。**★ただし「値を書ける器」は今も無い** ∴ ★値は0件のまま。**★`already_satisfied` は「手段」を書く欄として使われた** |
| **★修正候補（1件）** | **★実行系6欄（`target_file`/`test_file`/`test_body`/`test_command`/`allowed_files`/`requirement`）を、★`already_satisfied` が全部を覆うときだけ「空でよい」にする**＝**★「作らない」で終われる道を1本 作る** |
| **★修正候補のリスク（★空にしない）** | **★空にできる条件を作ると、★BUILD 経路の検査が緩む**（★不完全な PLAN が `READY_FOR_IMPLEMENTATION` へ進み、worker が消費する6欄を欠いたまま GENERATE に入りうる）。**★∴ 緩めるなら「`already_satisfied` が非空」かつ「`steps` が空」等の★決定論の条件付きに限る必要が在る。** **★これは `STRUCTURED_KEYS`/`EXECUTABLE_KEYS` に触る＝(b) の領域であり、★今回の (a) の範囲外である。★私は実施していない** |

---

# 4. ★予告の当否
| # | 予告 | 結果 |
|---|---|---|
| **R-1** | 分類は `OBSERVE_CURRENT_STATE` | **★当たり** |
| **R-2** | `TASK-2DER-6818E4BB` | **★当たり**（依頼文 62字 / sha1 `6818e4bb…`・機械抽出・打ち直していない） |
| **R-3** | 受入1（引用）は立つ | **★立った** |
| **R-4** | 受入2（利用）は予告しない | **★境界つきで立った**（★反証を §2 に併記） |
| **R-5** | 受入3 は予告しない | **★立たなかった**（★既知の `rss` を再取得する steps） |

**★1回の結果で断定しない**: **★40本の実測では 2/10 である ∴ ★「直った」とも「効かない」とも書かない。** **★書けるのは「この1回はこうだった」だけである。**

---

# 5. ★私が行った操作（★全件）
```
★実装: twoder/build_planner.py 1箇所（2挿入0削除）
★運用: webui 再起動 1回（旧 PID 4054742 → 新 PID 1740645 / 16:35:12）
        操作者=IMPL ／ 理由=prompt の変更を本番へ反映 ／ ★既存運用 ／ ★2DER の担当に数えない
        ★run-gate は初期化された（★以後の投入で立て直るため結果に影響なし）
★投入: POST /api/submit ★1回（16:36:04。receipt last_recv_at=16:36:04.063332・recv_count 78→79）
★実行: POST /api/run_next ★1回（16:36:11→16:36:35・24.4秒）。★PLAN が出た所で止めた
★していないこと: ★GENERATE を押していない ／ ★Generate/Audit の改善を混ぜていない ／ ★観測の選別に触っていない
                  ★Ledger / 図 / (c) の patch に触っていない ／ ★:8005 を自分で叩いていない ／ ★commit していない
                  ★61本の非回帰は走らせていない（★テストは0本）
```

# 6. ★次に直す1件（★原因が Prompt なら Prompt。★1件だけ・★実施しない）
> **★§3 の「修正候補」と同じ1件＝「作らない」で終われる道を1本 作る**（★実行系6欄を、`already_satisfied` が覆うときだけ空でよくする）。
> **★ただしこれは (b) の領域である。★採否と、緩める条件の設計は、★設計と MGR が決める。★私は決めない。**

---
*IMPL → 設計/監査（写: MGR / Taka）。D-176＝`_plan_prompt` に **`already_satisfied` を1欄 足した（1 hunk・2挿入0削除・禁止語0件・`STRUCTURED_KEYS`/`EXECUTABLE_KEYS` 不変・「観測を使え」の指示は足していない）**。事前に `validate_plan` が未知の欄を弾かないことを実読で確認した。**結果: その欄が実際に埋まった**——「`ps -eo pid,rss,comm` で基本のプロセス一覧は既に取れている」「compute apps 無しの GPU 合計は既に取れている」「`ss -ltn` の待ち受けは既に取れている」の3件。**評価は 1(引用)○／2(利用)○だが境界——既知と不足を切り分け不足だけを新規対象にしている一方、`steps` は同じコマンドをオプションを増やして再実行しており「再取得不要」とは書いていない ∴ `D-166` の厳格な線を当てれば受入3 相当は ×（物差しは変えない）／3(無視)は該当なし／4(論理整合性)は §3 の6欄に記載。** **★観測の「値」は本文に0件のままで、`already_satisfied` に入ったのも「どのコマンドで取れるか」＝手段である。** 入力間の矛盾は2つ（「標準ライブラリのみ」と観測が外部コマンド出力であることの同居／実行系6欄が必須で「作らない」で終われる道が無い）。**修正候補は「`already_satisfied` が覆うときだけ実行系6欄を空でよくする」1件で、リスクは「BUILD 経路の検査が緩み、worker が消費する6欄を欠いたまま GENERATE に入りうる」——∴ 決定論の条件付きに限る必要が在り、これは (b) の領域なので実施していない。** 予告は R-1〜R-3 当たり、R-4 は境界つきで立ち、R-5 は立たなかった。**40本では 2/10 ∴「直った」とも「効かない」とも書かない。書けるのは「この1回はこうだった」だけである。** GENERATE は押さず、commit もしていない。担当工程数の差分は 0。*
