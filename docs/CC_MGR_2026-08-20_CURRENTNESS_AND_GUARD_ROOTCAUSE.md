# 宛: Taka ―― **`currentness=CURRENT` の 矛盾 と ★GUARD false match の 原因（★調査のみ）**

**2026-08-20 06:1x ／ ★実装 0 ／ ★投入 0 ／ ★guard 変更 0 ／ ★failure memory 変更 0 ／ ★BLOCK 解除 0**
**★SELF_DEV_TOKEN = ★5/5 ／ ★HEAD = `24c649a`（不変）／ ★常駐 停止のまま**

---

# 第1部 ―― `measured_state` が 実コードと 矛盾した 原因

## 1. ★誰が 生成したか（★入口から 出所まで）

```
★① `egl/self_grounding.py:213`（★prompt・逐語）
   「Return ONLY a JSON object with keys: answer_claims
    (list of {text, record_ids, ★currentness:CURRENT|HISTORICAL}), …」
   ＝ ★★`currentness` は ★Qwen が ★自分で 付ける ラベル。
★② `twoder/submit.py:298`（★逐語）
   `_rec("MEASURED_STATE", [c for c in (ans.get("answer_claims") or [])
                            if any(x in str(c) for x in ("秒", "s", "174", "ms", "%"))])`
   ＝ ★`answer_claims` を ★絞って `MEASURED_STATE` に する。
★★但し 絞りの 条件に ★`"s"` が 入っている ∴ ★英字を 含む 主張は ★ほぼ 全部 通る
   （★実測: 今回の 2件は どちらも `IMPLEMENTATION_RUN_MISSING` 等を 含む ∴ `"s"` に 当たる）
★③ `submit.py:646` で `knowledge_packet.provenance.measured_state` に 載り、応答へ 出る。
```

```
★★＝ 生成者は ★Qwen（★`self_grounding.answer_question` の 意味トラック）。
★★＝ `MEASURED_STATE` は ★『測った 値』では なく ★『Qwen の 主張の 部分集合』。
```

## 2. ★根拠に なった もの

```
★応答の `egl_source_refs` = ★["DE-0484", "DE-0457"]（★2件のみ）
★`record_ids` も 同じ 2件
★★＝ ★根拠は ★過去の DE 記録 2件 ―― ★commit も ★hash も ★実コードの 観測も ★1つも 無い。
```

## 3. ★`CURRENT` を 決める 規則

```
★`egl/egl/contracts.py`（★`self_grounding.answer_question` の 契約・逐語）:
  guarantees … 「構造化 answer contract を validate_answer が決定的に検査(hermetic, total):
    **全 citation class**(claim.record_ids / historical.superseded_by / source_trace)の
    ★実在を検証し、無出典 assertion・捏造 record_id・非 dict claim entry・
    ★currentness=HISTORICAL の誤配置を検出」
  non_guarantees … 「baseline のみ: retrieval は naive keyword…、supersession は ★heuristic…、
    answerer は ★単一 Qwen(teacher_signal…)」
★`self_grounding.py:360-361` ―― 検査するのは ★『HISTORICAL が answer_claims に 誤配置されていないか』だけ。
★★＝ ★検査は ★『出典が 実在するか』と ★『ラベルの 置き場所』のみ。
★★＝ ★★『その 主張が 現在の コードと 合っているか』は ★検査対象では ない（★契約に そう 書いてある）。
```

## 4. ★実コードとの 結び付き

```
★`self_grounding.py` を ★`HEAD` / `git rev-parse` / `commit` / `sha256(open(...))` /
  `file_mtime` / `source_hash` で 走査 → ★★0件。
★★＝ ★`CURRENT` は ★repo HEAD・commit・hash・実コードの どれとも ★結び付いていない。
```

## 5. ★古い 記録 と 現在コードが 矛盾した ときの 設計

```
★★どちらが 勝つかを 決める 規則は ★存在しない（★比べていない ∴ ★勝負が 起きない）。
★`supersession` は 在る が ―― ★契約の 逐語で ★heuristic（「supersede/撤回/廃止 語 + rule token で
  over/under-flag する」）＝ ★★記録 同士の 新旧のみ。★コードとは 突き合わせない。
★★∴ ★stale / superseded / invalidated を ★コードに 対して 判定する 機構は ★無い。
```

## 6. ★★分類（★ご指定の A〜E）

```
★★★B ＋ D の 複合 ―― ★★E（複数原因）。

★B（CURRENT 判定に 実コードとの 照合が 存在しない）= ★確定
   根拠 = §3 契約の 逐語（意味的正しさは 検査しない）／ §4 走査 0件
★D（生成時点から 事実抽出が 誤っていた）= ★確定
   根拠 = ★根拠は DE 記録 2件のみ（§2）／ ★実コードを 1行も 見ずに
          「変更され」「持つ」と 断定した ＝ ★Qwen の 生成物
★A（古い 記録を CURRENT と 誤認）= ★★該当しない
   理由 = ★該当する 古い 記録が 在った わけでは ない。★DE-0484/DE-0457 は
          ★『そう 書いてある 記録』では なく ★出典と して 添えられただけ。
★C（照合機構は あるが 働かなかった）= ★★該当しない
   理由 = ★照合機構 自体が ★無い（§4）
```

---

# 第2部 ―― GUARD の `BLOCKED_DEAD_APPROACH`

## 7. ★GUARD は 何を 見たか（★`measured_state` を 使ったか）

```
★`submit.py:362-363`（逐語）:
   `from twoder import failure_memory as FM`
   `_dead = [m for m in FM.check(★{}, ★raw_input) if m.get("guard_action") == "BLOCK"]`
★`FM.check(signature, raw_input, …)` ―― ★第1引数は ★空辞書 ／ ★第2引数は ★依頼の 生文。
★`_mentions_dead_revival(raw, rec)`（逐語）:
   `low = (raw or "").lower()`
   `name = any(k.lower() in low for k in (rec.get("match_keywords") or []))`
   `make_live = any(v in low for v in _LIVE_VERBS)`
   `return name and make_live`
★★＝ ★GUARD は ★`measured_state` を ★★見ていない。★依頼文の 文字列だけ を 見る。
★★＝ ★第1部の 誤りとは ★独立した 判定（★材料に していない）。
```

## 8. ★★同一性の 根拠は 在るか → **★無い（★guard false match）**

**★CLOSED-NEGATIVE の 原文（逐語）:**

```
failure_id = "DEAD-afe-detector"
approach   = ★"AFE/Formal structural operators as a live detector
              (content <= generic skepticism)"
ref        = "DE-0103/DE-0104"
match_keywords = ★["afe", "run_afe", "formal esde", "structural operator", "aruism operator"]
_LIVE_VERBS    = ["live", "detector", "検出器", "常時", "always-on", "always on", "wire",
                  "組み込", "復活", "reconnect", "再接続", "revive", "有効化"]
```

**★★当たった 語（★私の 依頼文を 走査した 実測）:**

| 判定側 | 当たった 語 | ★依頼文の 中の 実物 |
|---|---|---|
| `match_keywords` の **`"afe"`** | 1件 | **★`safety`**（★"s-★afe-ty"） |
| `_LIVE_VERBS` の **`"live"`** | 1件 | **★`_work_kind_vs_deliverable_min_diff.md`**（★"de-★live-rable"） |

```
★★＝ ★判定は ★★部分文字列の 一致（★語境界を 見ない）。
★★＝ ★`safety`（★Taka が 「safety boundary を 無効に しない」と 書けと 指示した 語）と
   ★`deliverable`（★MGR の 文書名）が ★偶然 当たった。
★★＝ ★『AFE/Formal structural operators』も『live detector』も ★依頼文に ★1つも 無い。
★★∴ ★★★guard false match と 記録する。
★★（★解除していません ／ ★failure memory も ★guard も ★1文字も 触っていません）
```

## 9. ★★重なりの 帰結（★事実の 連鎖）

```
★① Qwen が ★実コードを 見ずに 「もう 出来ている」と 書く（★第1部・B+D）
★② GUARD が ★`safety` と `deliverable` の ★部分一致で ★止める（★第2部・false match）
★★→ ★実際には ★1行も 実装されていない のに ★『済み』かつ ★『再挑戦 禁止』に 見える。
★★→ ★①と②は ★独立（★材料を 共有していない）―― ★偶然 同時に 起きた。
```

## 10. ★していないこと

```
★実装 0 ／ 修正 0 ／ 新しい task 0 ／ 投入 0
★guard 変更 0 ／ failure memory 変更 0 ／ ★BLOCK 解除 0 ／ 迂回 0（★言い換え再投入も していない）
★実 repo 書き込み 0 ／ DISPOSE 0 ／ 常駐 再開 0 ／ SELF_DEV_TOKEN = ★5/5
★★名称検索だけで 判定していない ―― ★prompt / 契約 / `FM.check` / `_mentions_dead_revival` /
  `match_keywords` / `_LIVE_VERBS` を ★実物で 読み、★依頼文を ★正規表現で 走査した
```
