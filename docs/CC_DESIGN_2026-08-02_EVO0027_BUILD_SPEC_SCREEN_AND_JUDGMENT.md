# 【BUILD SPEC ＋ 判定】`EVO-0027` 受入(2)(3) — **★成果物は試験を通るが ★依頼文を満たしていない（実データで3件）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 06:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§6）** ／ **★3値 確認済（★§2）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0027` の `status_note`（逐語:「★畳めるかは設計が判定すること」「★残り受入: (2)… (3)…。手番=設計」）
- **★走行 0・★task 増 0・★commit 0**（★成果物は scratchpad で動かした。★本番に触れていない）

---

## 1. ★判定：`cc_register.py` は **★畳めない**

```
★退役条件の逐語:「★front door から ★ART- の本文が返る」
★実測: ★`GET /api/resolve?id=ART-ae789b58f7` → ★`relative_path: webui.py` ／ `absolute_path` ／
        ★`current_git_commit` ／ `git_blob_sha` ／ `content_hash` ＝ ★★登記であって ★本文ではない。
★★いま返るようになったのは ★`test_result.artifact`（★task 経由）であり、★★`ART-` の id では引けない。
★★★∴ ★★退役条件は ★満たしていない。★★畳めない。★別件として残す（★借金は減っていない）。
```

## 2. ★3値（★成果物は画面に載せられるか）

| 問い | 3値 | ★逐語・実測 |
|---|---|---|
| 本文は取り出せるか | **★在る** | `TASK-2DER-112D3FA7` の `test_result.artifact` **1671字・49行**／★sha256 `85a87e5c…` が**本文から再計算して一致**／★骨格 `def render(roadmap, control, asof, only_incomplete=False):` が**1文字も変わらず残っている** |
| 入力の形は実データと合うか | **★合う** | `/api/roadmap` に `phases[].items[].{item_id,title,status}` と `status_counts.DONE` ／ `/api/control` に `roadmap.status_counts.DONE` ＝ **★契約の想定どおり。★変換を書く必要が無い** |
| 中身は依頼文どおりか | **★★違う（3件）** | ★§3。★★封入した7本の試験は ★この3件を検査していない |

## 3. ★★実データで動かして出た3件（★決定論・私が測った）

```
★手順: ★本文を scratchpad で exec し、★`/api/roadmap` と `/api/control` の ★実データを渡した。
```

| # | 依頼文の逐語 | 成果物 | 実データでの影響 |
|---|---|---|---|
| **①** | 「DONE=完了 / IN_PROGRESS=進行中 / **PLANNED=予定 / PROPOSED=提案 / DEFERRED=保留 / DROPPED=取り下げ**」 | `status_map = {"DONE": "完了", "IN_PROGRESS": "進行中"}` ＝ **★6語中2語** | **★★14件が日本語にならない**（実測: `PLANNED` 3 ／ `PROPOSED` 10 ／ `DROPPED` 1） |
| **②** | 「summary = 1行。**★書式はちょうど: `"[" + status_ja + "] " + title_ja`**」 | `" ".join([item_id, title_ja, status_ja, phase_id])` | 実物 `'ITEM-2DER-EVO-0001 EGL admission in the forward path 完了 PHASE-2DER-EVO-01'`／期待 `'[完了] EGL admission in the forward path'` ＝ **★不一致** |
| **③** | 戻り値の形「`"phases": [{"phase_id": str, ★"title_ja": str, ★"status_ja": str, …}]`」 | phase の欄は `['items','phase_id','status','title']` | **★`title_ja` も `status_ja` も無い** |

```
★★★合っている物も書く（★片側だけ書かない）:
   ★`counts` = ★`{"roadmap_done": 73, "control_done": 75}` ＝ ★★食い違う2つの数字が ★両方 出ている（★受入の要）
   ★`asof` ／ `source_ids` ／ `only_incomplete` ／ `full` の4行 ＝ ★依頼文どおり
```

## 4. ★★原因（★9項目 #7 の3回目）

```
★成果物は ★★封入した7本を ★全部 通している（★PASSED/ok=true・★私も本文から確認）。
★★∴ ★欠陥は ★worker ではなく ★★★契約の側にある——★依頼文は書式を1文字ずつ書いたのに、
   ★封入した試験が ★その書式を ★★1本も検査していない。
   ★逐語: `test_summary_and_full_are_derived_not_invented` は ★`[` `]` を空白に置換して語だけ照合する
          ∴ ★★空白で連結しても ★通ってしまう。
★★★★★★「読んで気をつける」形が ★また残っていた ＝ ★C-2(b) と同じ構図（★雛形で塞いだのは import 名と `<<<FILL` だけ）。
```

## 5. やること

### 5-1. ★★次の依頼に足す試験（★3本・★そのまま封入できる形。★既存7本は1本も消さない）
```python
def test_all_six_status_words_are_translated():
    RM6 = {"phases": [{"phase_id": "P1", "title": "T", "status": "IN_PROGRESS",
                       "items": [{"item_id": "A%d" % i, "title": "X", "status": s} for i, s in
                                 enumerate(["DONE", "IN_PROGRESS", "PLANNED", "PROPOSED", "DEFERRED", "DROPPED"])]}],
           "status_counts": {"DONE": 1}}
    got = [it["status_ja"] for it in impl.render(RM6, CT, ASOF)["phases"][0]["items"]]
    assert got == ["完了", "進行中", "予定", "提案", "保留", "取り下げ"]

def test_summary_format_is_exactly_bracket_status_space_title():
    it = impl.render(RM, CT, ASOF)["phases"][0]["items"][0]
    assert it["summary"] == "[完了] Alpha"

def test_phase_has_japanese_title_and_status():
    p = impl.render(RM, CT, ASOF)["phases"][0]
    assert p["title_ja"] == "Forward-path grounding"
    assert p["status_ja"] == "完了"
```
```
★①②③ に ★1本ずつ対応する。★既存7本と ★矛盾しないことを ★確かめた
   （★`[完了] Alpha` は ★既存の「入力外の語を足さない」試験を ★通る——★`[` `]` は置換されるため）
★★封入は ★人（★MGR/Taka）。★★私は封入しない。★worker に直させる（★Claude が書き直さない＝受入(3) を守る）
```

### 5-2. ★配線（★受入(2)・★★Claude が書く行。★2DER の実績に数えない）
```
★置き場: ★`twoder/human_view.py` に ★★本文を1文字も変えずに置く（★`impl.py` は runner 固定名 ∴ 使わない）
★入口  : ★`webui.py:626` の ★`GET /` — ★既存 `render_report_page(rep)` の ★後ろに1節 足す
★入力  : ★`roadmap_view()` と ★`control_view()` の ★戻り値を ★そのまま渡す（★★変換を書かない・★§2 で合うと実測済）
★★★★行数を ★必ず報告する。★★成果物の本文の行数（49行）と ★Claude が書いた配線の行数を ★分けて書く
★★★★★★配線は ★5-1 が通って ★新しい本文が出てから（★古い本文を載せない）
```

## 6. 受入 ／ 9項目
```
★(1) ★5-1 の3本を足した契約で ★成功走行が1回 通る（★★7+3=10本 全通）
★(2) ★新しい本文を ★実データに当てて ★①14件が日本語になる ②summary が `[完了] …` ③phase に title_ja/status_ja
★(3) ★`GET /` に ★5点（★フェーズ別一覧／★未完だけ／★要約と全文／★いつ時点と台帳ID／★両方の数字 73 と 75）が ★日本語で出る
★(4) ★★載せた本文の sha256 が ★`test_result.artifact_sha256` と ★一致（★★Claude が書き直していない証拠）
★(5) ★Claude が書いた配線の行数を書く（★2DER の実績に数えない）
★(6) ★戻せる

【9項目】1 読める口＝`GET /`／2 書く口＝既存（配線）／3 理由を捨てない＝★§3 を全部 書いた
4 作っていないのでは＝★★本文は既に在る（★作り直さない・★足すのは試験3本だけ）
5 走ったか＝★実装が webui 再起動を確かめる／6 名前＝★`human_view`（★`impl` は runner 固定名 ∴ 衝突させない）
★7 依頼と試験の矛盾＝★★本件そのもの（★§4）／8 計器＝★sha256 の突き合わせ＝自己申告でない
★9 増える代わりに廃止＝★★「生JSONを人が読む運用」を畳む。★★(3) が通るまでは ★畳んだと書かない
```

## 7. 禁止
```
★Claude が成果物の中身を書き直す（★受入(3) が壊れる。★どうしても要るなら ★行数を書いて ★実績に数えない）
★依頼文を成果物に合わせて書き換える ／ ★既存7本の試験を消す・緩める
★`ART-` 側を混ぜる（★§1 で ★別件と判定）／ ★新しい台帳・エンドポイント・状態語を作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
