# 【実測 / `EVO-0024`(C-4)】**AC 系列が別ロードマップとして並んだ（4フェーズ / 8項目）**

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 12:0x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0024_BUILD_SPEC_TWO_ROADMAPS.md`

---

# 1. 変更（★Claude が書いた分。2DER の実績に数えない）

```
twoder/webui.py のみ:
  ① 読む口 :665  … roadmap_view(q.get("roadmap_id", ["ROADMAP-2DER-EVOLUTION-v0.1"])[0])  → +2 / -1
  ② AC の節 _human_view_section 内                                                        → +14
★合計 +16 / -1。★human_view.py は 0行（1文字も触っていない・§2 の sha256）。
★新しい台帳・エンドポイント・状態語なし。61本は走らせていない。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (1) | `?roadmap_id=…AC…` が AC を返す | **○** | `roadmap_id: ROADMAP-2DER-ATTENTION-CENTER-v0.2` / `title: 2DER Execution Attention Center` ／ **phases 4件・items 8件**（AC-00:1 / AC-01:1 / AC-02:6 / AC-03:0） |
| (2) | 既定は従来どおり | **○** | 引数なし → `ROADMAP-2DER-EVOLUTION-v0.1`・**29,337字** |
| (3) | `GET /` に2本が混ざらず並ぶ | **○** | 見出し `別のロードマップ: 2DER Execution Attention Center（4 フェーズ / 8 項目）— 上の一覧とは別物です`。進化の節が先・AC が後 |
| (4) | AC の「完了の数」は control 側が `None` | **○** | `完了の数: roadmap=2 ／ control=None`。**AC の節に 75 は出ていない**（機械で確認） |
| (5) | `human_view.py` を1文字も変えていない | **○** | sha256 `4fe115d154340c3904fe073058407310d63a6484d1f52d49b5f4f19563a17384`（**変わらず**） |
| (6) | 行数を分けて報告 | **○** | §1（2DER 0行 / Claude +16-1） |
| (7) | 戻せる | **○** | ①引数を消す ②AC の節14行を消す。※ commit 後は `git checkout --` では戻らない |

# 3. 予告の当否（`evo0024_pre.txt`）

| 予告 | 結果 |
|---|---|
| webui.py +6行前後 | **外れ（過少）**。実測 **+16 / -1** |
| **items 0件・節を出さない** | **★外れた。実測 8件** ∴ 節を出した（設計の【未確認】が実データで埋まった） |
| phases 4件 | **当たり** |
| 既定は従来どおり | **当たり** |
| control_done は None | **当たり** |
| human_view.py の sha256 不変 | **当たり** |

```
★item の id 体系: `ITEM-2DER-AC-0001` は resolved: false（設計の実測）だが、
   実際の item は `DD-AC-P2-NMIN` のような別体系の id で 8件 在った ＝ ★「無い」ではなく「名前が違う」。
```

# 4. 逐語（`GET /` の AC の節・先頭）

```html
<h3>別のロードマップ: 2DER Execution Attention Center（4 フェーズ / 8 項目）— 上の一覧とは別物です</h3>
<p>完了の数: roadmap=2 ／ control=None（control は この系列の数字が無いので出せません）</p>
<p><b>Phase0 Spec/Registration/Event-Contract</b>（提案）— PHASE-2DER-AC-00</p><ul>
<li>[完了] Spec v0.2 + planner追登録 + event-contract</li>
</ul>
<p><b>Phase1 Minimal Runtime Supervisor</b>（提案）— PHASE-2DER-AC-01</p><ul>
<li>[進行中] Test-Failure Adjudication Point (mechanism implemented, not activated)</li>
</ul>
```

# 5. 記録として1件（★私の作業中に起きたこと）

```
私が2つ目の編集をしている間に MGR が編集途中の webui.py を commit した ∴ HEAD が AC の節を
「進化の一覧より前」の位置で含んでいる。私は最終形で節を後ろへ移した（出力の並びは §4 のとおり正しい）。
機能差は無い。並び順だけの差である。
```

# 6. 走行

```
webui 再起動を確認（9項目 #5）: 起動 12:01:22 > webui.py 12:00:03。
走行 0・task 増 0・:8005 を叩いていない・台帳を直読していない・commit していない。GET / は 48,762 bytes。
```
