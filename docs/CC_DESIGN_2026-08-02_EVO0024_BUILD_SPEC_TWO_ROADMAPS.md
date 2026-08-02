# 【BUILD SPEC】`EVO-0024`(C-4) — **★読む口が1行 足りない。★成果物は作り直さない**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 11:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§5）** ／ **★3値 確認済（★§1）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0024` の `status_note`（逐語:「★AC 系列が ★混ぜずに 別ロードマップとして並んで出る」「★数字が口ごとに食い違う間は ★両方を並べて出す」「★作る前に3値(既に在る節に足すだけで済むか)」）
- **★走行 0・★task 増 0・★commit 0**（★front door を叩いて測っただけ）

---

## 1. ★3値：「★既に在る節に足すだけで済むか」＝ **★済まない（★但し1行）**

| 問い | 3値 | ★逐語・実測 |
|---|---|---|
| AC 系列は台帳に在るか | **★在る** | `GET /api/resolve?id=PHASE-2DER-AC-00` → `roadmap_id: "ROADMAP-2DER-ATTENTION-CENTER-v0.2"` ／ `title: "Phase0 Spec/Registration/Event-Contract"` ／ `status: PROPOSED` |
| front door から AC を**ロードマップとして**読めるか | **★★無い** | `GET /api/roadmap?roadmap_id=ROADMAP-2DER-ATTENTION-CENTER-v0.2` は **★進化ロードマップを返した**（`roadmap_id: ROADMAP-2DER-EVOLUTION-v0.1`）。逐語 `webui.py:665` `return self._send(roadmap_view())` ＝ **★引数を渡していない**（★隣の `:667` は `q.get("id")` を渡している） |
| 中の関数は対応しているか | **★★設計どおり在る** | `webui.py:241` 逐語 `def roadmap_view(roadmap_id="ROADMAP-2DER-EVOLUTION-v0.1")` ＝ **★最初から受け取る形になっている** |

```
★★∴ ★欠けているのは ★★読む口の1行だけ。★機構を作る話ではない。
★★★∴ ★★★2DER の成果物(`human_view.render`)は ★★作り直さない——★`roadmap` を ★引数で受ける設計 ∴
   ★同じ関数を ★2回 呼べば ★2本目のロードマップが出る。★★規律9（増やさない）に合う。
★★★★★「★成果物は 2DER に作らせる」は ★今回 ★作らせる物が無い ＝ ★★作らないのが正しい（★過大に作らない）
```

## 2. やること（★2箇所）

### 2-1. ★読む口（★`webui.py:665`・★`/api/resolve` と同じ流儀にするだけ）
```python
        if u.path == "/api/roadmap":
            return self._send(roadmap_view(★q.get("roadmap_id", ["ROADMAP-2DER-EVOLUTION-v0.1"])[0]))
```
```
★既定は今までと同じ ∴ ★既存の読み手は ★1つも壊れない。★戻し方＝★引数を消す。★可逆
```

### 2-2. ★人間用の節（★`_human_view_section`・★2本目を並べる）
```python
    rm2 = roadmap_view("ROADMAP-2DER-ATTENTION-CENTER-v0.2")
    v2  = human_view.render(rm2, ★{}, asof)          # ★control は空 dict
```
```
★★★`control` に ★`rep` を渡してはならない。★`rep` は ★進化ロードマップの数字である。
   ★渡すと ★AC の節に ★★別ロードマップの 75 が出る ＝ ★★嘘になる。
★★`{}` を渡すと ★成果物の規則どおり ★`control_done` は ★★`None`（★依頼文逐語「★0 で埋めない」）
★★★見出しに ★ロードマップの `title` を出して ★混ぜない（★実測: `/api/roadmap` は `title` を返す）
★★★★★★節は ★2本目を ★足すだけ。★1本目の出力を ★1文字も変えない
```

## 3. ★★確かめていないこと（★先に言う）

```
★`roadmap_view("ROADMAP-2DER-ATTENTION-CENTER-v0.2")` が ★items を ★何件 返すかは ★★測っていない【★未確認】
   ★理由: ★読む口が無いので ★front door から測れない（★それが本件である）
   ★`ITEM-2DER-AC-0001` は ★`resolved: false` だった ∴ ★item の id 体系が ★違う見込み【★未確認】
★★★∴ ★受入(1) を ★★「件数を報告する」形にした。★★0件なら ★★「0件だった」と書くこと。
   ★★★★0件のまま画面に空の節を出さない（★空の節は ★在るように見せる）
```

## 4. 受入

```
★(1) ★`GET /api/roadmap?roadmap_id=ROADMAP-2DER-ATTENTION-CENTER-v0.2` が ★AC を返す
     ★★phases と items の ★件数を書く（★0件なら ★0件と書き ★★§3 のとおり節を出さない）
★(2) ★既定（引数なし）で ★従来どおり ★進化ロードマップが返る（★応答字数を ★前後で書く）
★(3) ★`GET /` に ★2本が ★混ざらずに並ぶ（★見出しに ★それぞれの `title`）
★(4) ★★AC の節の「完了の数」は ★`control` 側が ★★`None`(または「分かりません」)で出る——★★75 が出たら ★失敗
★(5) ★★`human_view.py` を ★1文字も変えていない（★sha256 が ★`4fe115d1…` のまま）
★(6) ★Claude が書いた行数を ★分けて報告（★2DER の実績に数えない）／ ★(7) ★戻せる
★★★★★予告を投入前に書く: ★変更行数 ／ ★(1) の件数の見込み
```

## 5. ★9項目（私の分）
```
1 読める口＝`GET /api/roadmap?roadmap_id=`（★受入(1)）／2 書く口＝★本件は読み取り ∴ 該当なし
3 理由を捨てない＝★★`control` に 75 を出さず `None` にする（★受入(4)）＝「分からない」を捨てない
4 作っていないのでは＝★★`roadmap_view` は ★最初から roadmap_id を受ける（★`:241` 逐語）∴ ★作らない
5 走ったか＝★実装が webui 再起動を確かめる／6 名前＝★`roadmap_id`（★既存の引数名。★改名しない）
7 依頼と試験の矛盾＝★成果物を作らない ∴ 該当なし／8 計器＝★front door の値と sha256
★9 増える代わりに廃止＝★★「正典が2本あるのに画面が1本しか見せない」状態を畳む。★★新しい物は ★0
```

## 6. 禁止
```
★`human_view.py` を書き換える ／ ★AC の節に `rep`(進化側の control) を渡す ／ ★`control_done` を 0 で埋める
★AC と進化を ★同じ一覧に混ぜる ／ ★items 0件のまま空の節を出す
★新しい台帳・エンドポイント・状態語を作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
