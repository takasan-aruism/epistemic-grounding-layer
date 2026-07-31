# 【処置案 / D-200】S-3 の AUDIT 指摘2件 — **★1件は結論だけ正しい（根拠が事実と違う）**

- `BUILD_ROLE: ★実装源` / **宛: MGR**（★承認して `/api/ingest` で戻す役） / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 01:2x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **裁定**: `D-200` §4（設計が書き、MGR が承認して戻す）
- **この .md がまだ .md である理由**: **処置案を MGR へ渡す口が front door に無いため（C-1）。★最終記録は台帳（`/api/ingest`）であり、本書ではない。**
- **★私は ingest していない ／ ★コードを1行も変えていない ／ ★S-3 の依頼文に触っていない**

---

# 1. ★★先に、指摘の根拠を現物と突き合わせた（★これが処置を分ける）

```
★指摘① 逐語:「The implementation packet is ★explicitly 'null' and the diff is 'None'.」
★★現物（★front door `GET /api/claude_packet?task_id=TASK-2DER-B37727E3`）:
   ★`implementation_packet_ref` は ★★null ではない。★中身が在る（逐語 冒頭）:
     「Implement a pure Python function `render` in `human_view.py` that transforms roadmap and control
      data into a human-readable view structure, supporting incomplete filtering and Japanese status labels.」
   ★★★null なのは ★`worker_run_ref` の方である（逐語: `"worker_run_ref": null`）
★★★★∴ ★指摘①の ★根拠の記述は ★事実と違う。★★ただし ★結論（★コードが無い）は ★合っている。
★★★★★理由の推定（★断定しない・1回の観測）: ★auditor が見る入力は
   `dispatch.py:_MAP` 逐語で `"READY_FOR_AUDIT": ("AUDIT","INDEPENDENT_AUDITOR",★"LATEST_DIFF+TEST_RESULT",False)`
   ＝ ★auditor は ★diff と test_result しか見ていない ∴ ★packet を見ずに「packet は null」と書いた形。
```

---

# 2. ★処置案（★`record_disposition` の要件に合わせた形。★そのまま送れる）

```json
{
  "task_id": "TASK-2DER-B37727E3",
  "actor_role": "MANAGER",
  "result": {
    "finding_dispositions": [
      {
        "finding_id": "AF-qwen3.6@8005#auditor-seed101-run-0",
        "verdict": "PARTIAL",
        "accepted_portion": "コードが生成されていない（worker_run_ref が null / RUNNER_FAILED）という結論は妥当である。次の再生成は『実装が空である』ことを対象にする。",
        "basis": "結論は現物と一致する（worker_run_ref: null・test_result.reason: RUNNER_FAILED）。ただし根拠の記述『implementation packet is explicitly null』は事実と異なる——packet は存在し内容も在る（front door で確認）。null なのは worker_run_ref である。∴ 指摘の対象は保つが、根拠は採らない。"
      },
      {
        "finding_id": "AF-qwen3.6@8005#auditor-seed101-run-1",
        "verdict": "ACCEPTED",
        "basis": "RUNNER_FAILED は実行基盤の失敗であって、コード品質の判定材料にならない——これは正しく、かつ重要である。この指摘が無ければ FAILED をコード欠陥と読み違える。再生成では『テスト結果が load-bearing であること』を条件に含める。"
      }
    ]
  }
}
```

## 2-1. ★形式の確認（★`dev-workcell/dw/workcell.py:402-418` 逐語に照らした）
```
★`finding_dispositions` は ★非空 list ✓
★各要素は ★`finding_id` を持つ dict ✓
★`verdict` は ★{ACCEPTED, PARTIAL, REJECTED, REMAINS} のいずれか ✓
★★`PARTIAL` は ★`accepted_portion` 必須 → ★①に付けた ✓
★★★下流の効き方（同 `:433-447` 逐語 `rework_items`）:
   ★ACCEPTED は ★finding ごと渡る／★PARTIAL は ★`accepted_portion` だけ渡る
   ★REJECTED / REMAINS は ★渡らない
   ∴ ★①を PARTIAL にしたことで、★★事実と違う根拠は ★worker に渡らず、★結論だけが渡る。
```

---

# 3. ★私が★断定していないこと（★材料として置く）

```
★`test_result.artifact_sha256` は ★在る（`479629fd29c949aff…`）のに ★`worker_run_ref` は ★null。
★★＝ ★成果物の指紋は記録されたのに、★実行の記録が無い。★噛み合っていない。
★★★1回の観測である ∴ ★私は原因を書かない。★★処置の材料として ★そのまま置く。
★★★★これが ★もう一度 同じ形で出たら、★その時に調べる（★今 調べると ACTIVE が増える・規律9）。
```

---

# 4. ★MGR がやること（★私はやらない）

```
★① 本処置案を ★承認するか決める（★私は自分の監査を自分で承認しない）
★② `POST /api/ingest` に ★§2 の JSON を ★そのまま送る
★③ ★★応答を捨てない（`-o /dev/null` にしない・規律6）。★返ってきた `state` を書く
★④ ★その後 `POST /api/run_next?task_id=TASK-2DER-B37727E3` で ★次の段へ
   ★★gate が閉じていたら ★同一依頼文の再投入で開け直す（★第1章。★task は増えない）
★★★★★期待される次の段（★予告。★外れたら「外れた」と書く）:
   ★`DISPOSE` 後は ★`READY_FOR_REGENERATE` → ★`REGENERATE`（`CODING_WORKER`）…確信 中
   ★根拠: ★ACCEPTED が1件 在る ∴ `rework_items` が空にならない
```

---

# 5. ★やっていないこと
```
★ingest していない（★承認の手番を飛ばさない）／ ★コードを1行も変えていない
★S-3 の依頼文に触っていない ／ ★新しい台帳・計器・状態語を作っていない
★`artifact_sha256` と `worker_run_ref` の噛み合わなさを★調べていない（★材料として置いただけ）
★★`D-199`（2DER が単発で Claude を呼ぶ）に手を出していない（★Taka 指示で保留）
   ★★参考として1つだけ残す: ★`claude -p` を呼ぶコードは ★`twoder`/`dev-workcell`/`ds`/`rri`/`egl` の
      `*.py` ★全数走査で ★0件（★打ち切り無し）。★保留のまま。★着手していない
★★★止めたものはそのまま: C-3 ／ `D-191` ／ 案C の測定 ／ 受入3 の採点 ／ Ledger ／ 図 ／ (c) patch
```

---
**決めたこと**: **①指摘①の根拠は事実と違う——`implementation_packet_ref` は null ではなく中身が在り、null なのは `worker_run_ref` である。auditor が見る入力が `LATEST_DIFF+TEST_RESULT` だけなので packet を見ずに書いた形と推定するが、断定しない ②∴ 指摘①は `PARTIAL`（結論は妥当・根拠は採らない）、指摘②は `ACCEPTED`（RUNNER_FAILED をコード品質の判定に使わないという指摘は正しく重要）③`PARTIAL` にしたことで、`rework_items` の仕様上、事実と違う根拠は worker に渡らず結論だけが渡る ④`artifact_sha256` が在るのに `worker_run_ref` が null という噛み合わなさは1回の観測なので原因を書かず、処置の材料として置く。同じ形がもう一度 出たら調べる ⑤MGR は承認して `/api/ingest` に §2 の JSON を送り、応答を捨てずに `state` を書く。その後 `run_next`、gate が閉じていたら同一依頼文の再投入で開け直す ⑥予告は「DISPOSE 後は `READY_FOR_REGENERATE` → `REGENERATE`」（確信 中。ACCEPTED が1件 在るので `rework_items` が空にならない）⑦`D-199` は保留のまま着手していないが、`claude -p` を呼ぶコードは5 repo の `*.py` 全数走査で 0件だったことだけ参考に残す。**
