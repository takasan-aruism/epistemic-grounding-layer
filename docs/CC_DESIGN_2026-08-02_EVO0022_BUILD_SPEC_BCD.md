# 【BUILD SPEC】C-2 残り3件 (b)(c)(d) — **★(d) は作らない（約束だけ）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 03:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§4）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0022` の `status_note`（逐語:「(b) 雛形に『試験は impl を import』を最初から入れる (c) 止まった理由を雛形に出す (d) task 側の約束(どの phase に BUILT と監査を書くか)を決める。★(d) は作らない=約束だけ」）
- **★(a) は監査済**（`history` 21件・裁定6件が front door から逐語で読める・`record` は最新1件のまま・応答 20,684字）

---

## 1. ★(d) 約束を決める — **★作らない**

**★Claude が task へ書ける phase は3つだけ**（`webui.ingest` 逐語・全数）:
```
PLAN → record_plan ／ DISPOSE → record_disposition ／ UPPER_REVIEW → record_upper_review
それ以外 → raise ValueError(f"no Claude ingest for op={op}")
```

**★∴ 約束（★これを既定とする）**

| 何を | どこへ | 根拠 |
|---|---|---|
| **監査結果**（設計/監査） | **`UPPER_REVIEW` の `review`**（`POST /api/ingest`） | ★`review` は自由な dict（`workcell.py:471-473` 逐語 `{"review": review}`）／★MGR の実測で本文がそのまま残り読み返せた |
| **処置**（findings への判定） | **`DISPOSE` の `finding_dispositions`** | ★既存の形（`verdict` + `basis`）。★新設しない |
| **BUILT**（実装の報告） | **★`ITEM` の `status_note`**（front door の `<<<2DER:PROGRESS>>>`） | ★★task に書ける phase が無い（★上記3つに該当しない）／★★(a) で `history` が読めるようになった ∴ ★履歴が残る |
| **裁定**（MGR） | 同上 | ★既に運用中（★裁定1〜5 が読める） |

```
★★★★新しい phase・状態語・口を ★作らない。★★約束を書くだけ ＝ ★(d) は ★★コード変更 0。
★★★★★★★BUILT を `UPPER_REVIEW` に相乗りさせない（★監査と実装報告が同じ欄に混ざる）。
```

---

## 2. ★(b) 雛形に「試験は impl を import」を最初から入れる

```python
# twoder/request_template.py の ★契約の枠の直前に1行 足す（★文言は日本語・★決定論）
"■ 契約（★合格条件。★ここは人が書きます。★2DER は埋めません）",
★"※ 試験は ★`import impl` と書いてください。★2DER が作る成果物は ★必ず `impl.py` です",
★"※ 骨格に ★埋めてよい場所を ★`<<<FILL: ここに実装>>>` で示してください。★示さないと骨格 全文が変更禁止になります",
```
```
★★根拠（★本日の実測・2件とも我々の事故）:
   ★`import human_view` → ★`ModuleNotFoundError`（★runner は `impl.py` 固定・`generate_via_runner.py:99` 逐語）
   ★`<<<FILL` 0件 → ★骨格 全文が1固定区間 → ★`SKELETON_VIOLATION`（★`artifact_head` で確定）
★★★★★「★読んで気をつける」形にしない ＝ ★雛形に ★最初から入れる（★`EVO-0034` と同じ思想）
```

## 3. ★(c) 止まった理由を雛形に出す

```python
# webui.py:145（★呼び出し元）— ★引数を1つ増やす
"next_request_template": RT.build(goal, tr.get("NEXT_INFORMATION_NEED"), ★stop=_stop_reason(tid)),

# request_template.build に ★任意引数を1つ（★既定 None ＝ ★従来と同じ出力）
def build(goal, next_information_need, ★stop=None):
```
**★`stop` に載せるもの（★既に読める値だけ。★新しく作らない）**
```
★`test_result.reason` ／ ★`runner_exit` ／ ★`skeleton_missing_segment`（★先頭120字）
★★どれも `GET /api/claude_packet` の `test_result` に在る ∴ ★取り直さない
★★★★止まっていなければ（★`test_result` が無ければ）★`stop=None` ＝ ★節ごと出さない
```

---

## 4. 受入 ／ 9項目
```
★(b-1) ★雛形に ★`import impl` と ★`<<<FILL` の2行が★在る（★逐語で確かめる）
★(c-1) ★止まっている task の雛形に ★`reason` と ★`runner_exit` が★出る
★(c-2) ★止まっていない task では ★その節が★出ない（★空欄を出さない）
★(d-1) ★★コード変更 ★0 で在ること（★約束のみ）
★(e) ★戻せる（★(b)(c) の変更を消したら元に戻る）
★★★★★予告を投入前に書く: ★変更行数 ／ ★どの task で測るか

【9項目】1 読める口＝`GET /api/state` の `next_request_template`／2 書く口＝既存（`build` の戻り値）
3 理由を捨てない＝★(c) がまさにそれ／4 作っていないのでは＝★`stop` の値は ★既に在る（取り直さない）
5 走ったか＝★実装が webui 再起動を確かめる／6 名前＝★`impl` を ★雛形に明記（★本日の事故の直接対処）
7 依頼と試験の矛盾＝★(b) がその予防／8 計器＝★front door の値を見る
★9 増える代わりに廃止＝★★「契約の書き方を人が毎回 思い出す」運用を畳む（★雛形が言う）
```

## 5. 禁止
```
★新しい phase・状態語・台帳・エンドポイントを作る ／ ★`ingest` に分岐を足す
★BUILT を `UPPER_REVIEW` へ相乗りさせる ／ ★`record` の形を変える
★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
