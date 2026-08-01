# 【実測 / `EVO-0022` (b)(c)(d)】雛形が **`import impl` と `<<<FILL` を言う**／**止まった理由を出す**

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 06:2x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0022_BUILD_SPEC_BCD.md`

---

# 1. 変更

```
twoder/request_template.py  +13 / -2（(b) の2行、(c) の節6行、stop 引数と docstring）
twoder/webui.py             +14 / -1（_stop_reason 10行 ＋ 呼び出しの引数 2行）
合計 27挿入 3削除。(d) はコード変更 0（約束のみ）。
新しい phase・状態語・台帳・エンドポイントなし。ingest に分岐を足していない。record の形も変えていない。
★`_stop_reason` は SPEC が呼び出し側だけ示していて未実装だったので私が書いた（webui 内の private helper）。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (b-1) | 雛形に `import impl` と `<<<FILL` の2行 | **○** | 4 task すべてで在り（§3 逐語） |
| (c-1) | 止まっている task に `reason` と `runner_exit` | **○** | `0E5E8675`: 「理由: RUNNER_FAILED / 試験の終了コード: 1」／`816D6F68`: 「理由: SKELETON_VIOLATION / 骨格のうち見つからなかった断片: …」 |
| (c-2) | 止まっていない task では節が出ない | **○** | `DE042DE9`(COMPLETE) と `E3B92A8E`(試験 PASSED) の両方で**節なし** |
| (d-1) | コード変更 0 | **○** | (d) は §4 の約束のみ |
| (e) | 戻せる | **○** | 手で戻した版が両ファイルとも `HEAD` と**バイト一致** |

# 3. 逐語

```
■ 契約（合格条件。ここは人が書きます。2DER は埋めません）
※ 試験は `import impl` と書いてください。2DER が作る成果物は必ず `impl.py` です
※ 骨格に埋めてよい場所を `<<<FILL: ここに実装>>>` で示してください。示さないと骨格 全文が変更禁止になります

（TASK-2DER-0E5E8675 / READY_FOR_AUDIT）
■ 前回 止まった理由（2DER が記録したもの）
  理由: RUNNER_FAILED
  試験の終了コード: 1

（TASK-2DER-816D6F68 / READY_FOR_AUDIT）
■ 前回 止まった理由（2DER が記録したもの）
  理由: SKELETON_VIOLATION
  骨格のうち見つからなかった断片: # impl.py
def render(roadmap, control, asof, only_incomplete=False):
    """roadmap = GET /api/roadmap の dict, control =
```

```
★null の欄は行ごと出していない（816D6F68 は runner_exit が null ∴ その行が無い）。
   空欄を出さない形にした。受入(c-1) は 2 task を合わせて満たしている。
```

# 4. (d) の約束（コード変更 0・ここに書くだけ）

| 何を | どこへ |
|---|---|
| 監査結果（設計/監査） | `UPPER_REVIEW` の `review`（`POST /api/ingest`） |
| 処置（findings への判定） | `DISPOSE` の `finding_dispositions` |
| **BUILT（実装の報告）** | **`ITEM` の `status_note`**（front door の `<<<2DER:PROGRESS>>>`） |
| 裁定（MGR） | 同上 |

```
Claude が task へ書ける phase は3つだけ（PLAN / DISPOSE / UPPER_REVIEW・それ以外は ValueError）。
BUILT は該当しないので ITEM 側へ書く。UPPER_REVIEW に相乗りさせない。
```

# 5. 走行・戻し方

```
webui 再起動を確認（9項目 #5）: 起動 06:17:42 > webui.py 03:43:39 / request_template.py 03:43:29。
:8005 を叩いていない。task を増やしていない。走行を1回も起こしていない（読むだけで測れた）。commit していない。
戻し方: ① request_template.py の (b) 2行・(c) の節・stop 引数を消す ② webui.py の _stop_reason と引数を消す。
        ※ commit 後は `git checkout --` では戻らない。
```
