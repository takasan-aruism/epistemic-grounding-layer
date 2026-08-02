# 【実測 / `EVO-0027` 受入(3)〜(6)】**`GET /` に 2DER の成果物が日本語で出た**（本文は1文字も書き直していない）

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 07:1x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0027_BUILD_SPEC_SCREEN_AND_JUDGMENT.md`

---

# 1. 行数（★2DER の分と Claude の分を分ける）

```
★2DER が書いた本文: twoder/human_view.py  ★70行（TASK-2DER-A64D0C6D の artifact 2099字をそのまま置いた）
★Claude が書いた配線: twoder/webui.py     ★+28 / -1（_human_view_section 27行[docstring 4行含む] ＋ GET / の1行）
★★配線は 2DER の実績に数えない。★本文は Claude が1文字も書き直していない（§2 の sha256）。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (3) | `GET /` に5点が日本語で出る | **○** | §3（5点すべて在り・48,084 bytes） |
| (4) | 載せた本文の sha256 が `artifact_sha256` と一致 | **○** | 置いたファイル `4fe115d154340c3904fe073058407310d63a6484d1f52d49b5f4f19563a17384` ＝ **記録と完全一致** |
| (5) | Claude が書いた配線の行数 | **○** | **28行**（§1） |
| (6) | 戻せる | **○** | 手で戻した `webui.py` が `HEAD` と**バイト一致**／`human_view.py` は新規 ∴ 削除で戻る |
| (1) | 10本 全通の成功走行 | **○（MGR 実測）** | `TASK-2DER-A64D0C6D` PASSED・artifact 2099字。私はこの本文を front door から取っただけ |
| (2) | 実データ①②③ | **設計の手番** | MGR の note の指定どおり私は判定していない。ただし §3 に実物が出ている |

> **訂正(08:3x)**: 本文の行数を **71行 → 70行**。`count("\n")+1` が末尾改行を1行 多く数えていた（`splitlines()` も `wc -l` も 70）。設計の独立監査の指摘が正しい。

# 3. 逐語（`GET /` の新しい節・先頭）

```html
<h2>2DER が作った画面（human_view.render）</h2>
<p>いつ時点: 2026-07-11T09:00:00 ／ 参照した台帳ID: 103 件（例 ITEM-2DER-EVO-0001, …）</p>
<p>完了の数: roadmap=73 ／ control=75（★2つは別々に数えたもので、食い違うことがあります）</p>
<h3>フェーズ別 一覧（全部）</h3>
<p><b>Forward-path grounding</b>（提案）— PHASE-2DER-EVO-01</p><ul>
<li>[完了] EGL admission in the forward path<details><summary>全文</summary><pre>item_id: ITEM-2DER-EVO-0001
title_ja: EGL admission in the forward path
status_ja: 完了
phase_id: PHASE-2DER-EVO-01</pre>…
```

| 5点 | 判定 |
|---|---|
| フェーズ別一覧 | ○ `<h3>フェーズ別 一覧（全部）</h3>` |
| 未完だけ | ○ `<h3>未完だけ</h3>` |
| 要約と全文 | ○ `[完了] …` ＋ `<details><summary>全文</summary>` |
| いつ時点と台帳ID | ○ `いつ時点: 2026-07-11T09:00:00 ／ 参照した台帳ID: 103 件` |
| 両方の数字 | ○ `roadmap=73 ／ control=75` |

# 4. SPEC との食い違い（1件・私の判断でなく報告）

```
SPEC §5-2 は入力を「roadmap_view() と control_view() の戻り値」と書いているが、
★`control_view()` という関数は無い（実測: webui.py に定義なし）。/api/control が返すのは CSR.build_report() の結果である。
∴ 私は GET / の枝が既に作っている `rep`（＝ /api/control と同じ物）をそのまま渡した。変換は書いていない。
```

# 5. 走行・戻し方

```
webui 再起動を確認（9項目 #5）: 起動 07:05:39 > webui.py 07:05:28 / human_view.py 07:05:08。
走行 0（本文は front door から取っただけ）・task 増 0・:8005 を叩いていない・commit していない。
戻し方: ① webui.py の _human_view_section を消し GET / の行を元に戻す ② twoder/human_view.py を消す。
        ※ commit 後は `git checkout --` では戻らない。
★「生JSONを人が読む運用」の廃止は、Taka が画面を見て判断するまで畳んだと書かない。
```
