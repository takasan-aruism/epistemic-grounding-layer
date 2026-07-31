# 【BUILD SPEC / S-3】**★2DER に人間用UIの4つを作らせる** — ★依頼文に★契約を入れる（★前回止まった原因）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 00:2x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ 運用規律 v0.3 確認済 ／ **裁定**: `D-193` §4 S-3
- **この .md がまだ .md である理由**: **依頼文を台帳へ渡す口が front door に無いため（C-1）**
- **★増やす管理対象 0**（規律9）／ **★あなたは production を書かない。★2DER に書かせる**

---

# 1. ★前回 止まった理由（★これを潰すのが今回の全部）
```
★`TASK-2DER-E8F8CA7B` は ★GENERATE→AUDIT→REGENERATE→AUDIT→REGENERATE→AUDIT と★6回 進み、
   ★`JUDGE_REQUIRED` で停止。★逐語: {"status":"FAILED", "reason": ★"SPEC_INCOMPLETE_NO_CONTRACT"}
★★＝ ★依頼文に ★契約（受入試験）が無いので ★合否を判定できない。
★★★∴ ★今回の依頼文には ★契約を入れる。★それだけが前回との差である。
```

# 2. ★契約の入れ方（★現物で確かめた。★想像で書いていない）
```
★`POST /api/submit` が受け取るのは ★`{"raw": "<本文>"}` の ★1文字列だけ（`webui.py:657` 逐語 `SUB.submit(b.get("raw",""))`）
★★契約は ★本文の中の★マーカーで決定論抽出される（`twoder/contract_seal.py:19-21` 逐語）:
   ★`<<<2DER:SKELETON>>>` … `<<<2DER:END>>>`
   ★`<<<2DER:IMMUTABLE_TESTS>>>` … `<<<2DER:END>>>`
★★★fail-closed: ★`def test_` で始まる行が1つも無いと ★`ValueError`（同 `:66-67`）
★★★★片方のマーカーだけ／END 欠落も ★`ValueError`。★両方 無ければ ★契約無し（★前回がこれ）
★★★★★【実測・注記】★`runs/*.json` に `BEGIN_SK` の出現は ★0件
   ＝ ★この契約経路は ★実投入で使われたことが★無い可能性が高い。★★今回が初回かもしれない。
   ★∴ ★マーカーの扱いで落ちたら ★それは成果である（★止まった段と逐語を記録して戻す）
```

# 3. ★依頼文（★下の全文をそのまま `raw` に入れる。★1文字も変えない）

```
2DER の開発状況ページ(GET /)に、人間が読むための4つを足す関数を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

<<<2DER:SKELETON>>>
# human_view.py
def render(roadmap, control, asof, only_incomplete=False):
    """roadmap = GET /api/roadmap の dict, control = GET /api/control の dict.
    戻り値の dict:
      {"asof": str, "source_ids": [str, ...],
       "counts": {"roadmap_done": int, "control_done": int},
       "phases": [{"phase_id": str, "title_ja": str, "status_ja": str,
                   "items": [{"item_id": str, "title_ja": str, "status_ja": str,
                              "summary": str, "full": str}]}]}
    only_incomplete=True のとき DONE の item を除く。"""
    raise NotImplementedError
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
import human_view

RM = {"phases": [{"phase_id": "P1", "title": "Forward-path grounding", "status": "DONE",
                  "items": [{"item_id": "I1", "title": "Alpha", "status": "DONE"},
                            {"item_id": "I2", "title": "Beta", "status": "IN_PROGRESS"}]}],
      "status_counts": {"DONE": 65}}
CT = {"roadmap": {"status_counts": {"DONE": 67}}}

def test_phase_list_has_japanese_title_and_status():
    v = human_view.render(RM, CT, "2026-08-01T00:00:00")
    p = v["phases"][0]
    assert p["phase_id"] == "P1"
    assert p["title_ja"] and isinstance(p["title_ja"], str)
    assert p["status_ja"] and isinstance(p["status_ja"], str)
    for it in p["items"]:
        assert it["title_ja"] and it["status_ja"]

def test_filter_incomplete_only():
    v = human_view.render(RM, CT, "2026-08-01T00:00:00", only_incomplete=True)
    ids = [it["item_id"] for p in v["phases"] for it in p["items"]]
    assert "I2" in ids
    assert "I1" not in ids

def test_summary_and_full_are_separate_fields():
    v = human_view.render(RM, CT, "2026-08-01T00:00:00")
    it = v["phases"][0]["items"][0]
    assert "summary" in it and "full" in it
    assert it["summary"] != it["full"]

def test_page_shows_asof_and_source_ledger_ids():
    v = human_view.render(RM, CT, "2026-08-01T00:00:00")
    assert v["asof"] == "2026-08-01T00:00:00"
    assert "I1" in v["source_ids"] and "P1" in v["source_ids"]

def test_shows_both_counts_while_they_disagree():
    v = human_view.render(RM, CT, "2026-08-01T00:00:00")
    assert v["counts"]["roadmap_done"] == 65
    assert v["counts"]["control_done"] == 67
<<<2DER:END>>>
```

# 4. ★手順（★増やさない）
```
① ★依頼文を機械で抜く（★打ち直さない）→ ★字数と sha1 を書く → ★予告 task_id を書く
② ★`POST /api/submit` に `{"raw": "<全文>"}` ★1回
③ ★直後に `GET /api/receipt`（★他の口を叩く前に）
④ ★`POST /api/run_next?task_id=…` を ★止まるまで（★refused か BLOCKED が出たら終わり）
   ★★gate が閉じたら ★同一依頼文を★再投入して開け直す（★開発者規律 第1章。★task は増えない）
   ★★★再投入した回数と理由を★必ず書く
⑤ ★止まった段・`workflow_state`・`test_result` を★逐語で記録して戻す
```

# 5. ★Monitor を張る（★Taka 指示・`D-193` §5）
```
★対象: ★2DER の front door。★例: 2分おきに `GET /api/control` を叩き、★DE / CHG の件数が
   ★変わった時だけ1行 出す。★1本目は「★起動時の基準値・台帳が動いた証拠ではない」と★明記する
   （★MGR が `D-194` で踏んだ誤りを繰り返さない）
```

# 6. ★やってはいけないこと
```
★あなたが `human_view.py` を書く（★書いたら「★Claude が書いた」と書き、★2DER の実績に数えない）
★依頼文を打ち直す・通りやすくする ／ ★契約のマーカーを変える ／ ★production を直接編集する
★gate にパッチを当てる（★`D-193` §3 の S-2 は ★不要と判明。★在るもので通る）
★新しい台帳・新しい計器を作る ／ ★commit する ／ ★.md で成果を報告する（★台帳の値が動く形で置く）
```

# 7. ★報告（★これだけ）
```
1 ★止まった段（★`workflow_state` と `test_result` を逐語）
2 ★各段の actor（★誰が実行したか。★`CODING_WORKER` / `INDEPENDENT_AUDITOR` / Claude）
3 ★再投入した回数と理由
4 ★A のどの数字が動いたか（★2DER だけで完了した工程 ／ Claude が要る工程）
5 ★あなたが書いた行数（★0 なら「0」。★0 でないなら何を書いたか）
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①前回 `JUDGE_REQUIRED` で止まった理由は `SPEC_INCOMPLETE_NO_CONTRACT`＝依頼文に契約が無いことなので、今回はそれだけを足す ②契約は本文中のマーカー（`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>` / `<<<2DER:END>>>`）で決定論抽出される（`contract_seal.py:19-21`）。`def test_` が1行も無いと `ValueError` で弾かれる ③【実測】`runs/*.json` に `BEGIN_SK` は 0件なので、この契約経路は実投入で使われたことが無い可能性が高い——マーカーで落ちたらそれ自体が成果なので、止まった段と逐語を記録して戻す ④依頼文は skeleton（純関数・本番 import なし・標準ライブラリのみ）と受入試験5本（フェーズ別一覧の日本語／未完だけに絞る／要約と全文が別欄／いつ時点か＋台帳ID／65 と 67 を両方 出す）を含む全文で、1文字も変えない ⑤gate が閉じたら同一依頼文を再投入して開け直す（task は増えない）。回数と理由を必ず書く ⑥あなたは `human_view.py` を書かない。書いたら「Claude が書いた」と明記し 2DER の実績に数えない ⑦Monitor を張り、1本目に「起動時の基準値・台帳が動いた証拠ではない」と明記する。**
