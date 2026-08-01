# 【実測 / `EVO-0031` (a)】`artifact_head` — **一致する先頭 = 0文字。欠けているのは `# impl.py` 行**

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 01:2x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号: #1 — §5）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0031_BUILD_SPEC_SHOW_THE_ARTIFACT_HEAD.md`

---

# 1. 変更（Claude が書く例外 ∴ 2DER の実績に数えない）

```
twoder/generate_via_runner.py  +3 / -1   (_art, _head の2行 ＋ 返り値に artifact_head)
twoder/webui.py                +2 / -1   (test_result に1欄 ＋ 前行の末尾カンマ)
検査(verify_skeleton_preserved / skeleton_missing_segment)は変えていない。新しい状態語・台帳・計器・エンドポイントなし。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (1) | `test_result` に `artifact_head` が在り読める | **○** | 欄8つ: `status, ok, reason, artifact_sha256, runner_exit, runner_stdout_tail, skeleton_missing_segment, artifact_head` |
| (2) | 並べて「どこが違うか」人に分かる | **○** | **一致する先頭 = 0文字**（§3） |
| (3) | 400字で切れ、切ったと分かる | **○** | 両方 **412字**・末尾 `…(truncated)` |
| (4) | 戻せる | **○** | 手で2箇所を戻した版が `600841a~1` と**バイト一致** |

# 3. 逐語（`TASK-2DER-816D6F68` / `SKELETON_VIOLATION`）

```
skeleton_missing_segment（先頭200字）:
'# impl.py\ndef render(roadmap, control, asof, only_incomplete=False):\n    """roadmap = GET /api/roadmap の dict,
 control = GET /api/control の dict.\n    戻り値の dict:\n      {"asof": str, "source_ids": [str,'

artifact_head（先頭200字）:
'def render(roadmap, control, asof, only_incomplete=False):\n    status_map = {"DONE": "完了", "IN_PROGRESS": "進行中"}
\n    \n    source_ids = []\n    phases_out = []\n    \n    for phase in roadmap.get("phases"'

★一致する先頭 = 0 文字。
   骨格は `# impl.py` の行から始まる。成果物は `def render(` から始まる。
   ＝ 成果物に `# impl.py` の行と docstring が無い。1文字目から違う。
```

# 4. 走行

```
新しい走行は「要った」（SPEC §4 の見込みは外れ）。既存の記録は変更前に作られており artifact_head を含まないため。
作り方 = TASK-2DER-816D6F68 を再投入(sha1 一致 ∴ task 増なし) -> run_next で REGENERATE(57.7秒 / QWEN_LIVECODER)。
webui 再起動を確認(9項目 #5): 起動 01:05:50 > webui.py 01:04:34 / generate_via_runner.py 01:04:31。
★1回目の run_next は refused: `no runnable DW task (observe/blocked context)` / runnable=false。
   submit 応答は runnable=true だった ∴ その間に別の投入が run-gate(_LAST・単一枠)を上書きしている。
   再投入と run_next を連続で打って通した。
```

# 5. 9項目のうち外れた番号

```
#1（置いたなら どこから読めるか）: artifact_head は `GET /api/claude_packet` に在る。
   `GET /api/state` には無い（build_state の返すキーに test_result 自体が無い・webui.py:124-140）。
   ∴ /api/state を見ると「無い」と映る。どちらの口に出すかは設計の判断。
他の番号は外れていない。
```

# 6. 戻し方

```
① generate_via_runner.py の `_art` / `_head` の2行を消し、返り値から `"artifact_head": _head` を消す
② webui.py の `"artifact_head": …` の1行を消し、前行の末尾カンマを取る
※ `git checkout --` では戻らない(HEAD が変更を含む・600841a)。
```
