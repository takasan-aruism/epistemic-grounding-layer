# 実装 → 設計/監査: D-21 修正 — path を1表記に正規化した（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-27_D21FIX_SPEC_NORMALIZE_PATH.md` v1.0
- **受領した文書**: 上記実装源 / `CC_DESIGN_2026-07-27_D21_PATH_CONVENTION_DEFECT.md`（原因）
- **本文書は観測と実装を書きます。判定・評価をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` の削除: **[x] 実施済**
- **`cc_register.py` の path 表記の欠陥: [x] 本 build で対応**

---

## 1. 直したもの（`egl/docs/cc_register.py` のみ・3点）
| # | 変更 |
|---|---|
| **①** | `normalize_path()` を新設し、`record_doc` の冒頭で適用。**先頭の `egl/` を1回だけ剥がし、`docs/` で始まらなければ `ValueError`** |
| **②** | **`_meta` に1文を追加**（§2 の文言）。**列ではなく文言。§4-4 参照** |
| **③** | `counts().files_since_start` の対象を **`CC_*.md` 限定 → `egl/docs/` 直下の `*.md` と `*.json`**（`CC_REGISTER.jsonl` と `cc_register.py` は除外）。**母数の訂正であって追加ではない** |

**`doc_id_for` は変更していません。`record_done` も変更していません。列を足していません。行の種類を増やしていません。**

## 2. 受入【監査:IMPL】
### ① 2表記が同じ `doc_id` を返す
```
record_doc("egl/docs/X_D21FIX_A.md", …) = ART-845d63f15f
record_doc("docs/X_D21FIX_A.md",     …) = ART-845d63f15f
一致 = True
```
### ② `docs/` 以外は `ValueError`
```
record_doc("elsewhere/X.md", …)
ValueError: path must be repo-relative under docs/ (got 'elsewhere/X.md' -> 'elsewhere/X.md')
```
### ③ `artifact_registry` と一致
```
artifact_id_for("egl", "docs/X_D21FIX_A.md") = ART-845d63f15f   一致 = True
```
※照合のための一時 import のみ。**`cc_register.py` 本体は `twoder` を import していません。**

### ④ `_meta` の1文 — ★書き換えたことを明記します
**`_META` 定数を直しただけでは反映されませんでした。** `_ensure()` は台帳が既に在れば書かない設計（追記のみ）のため、**既に書き込まれている1行目には効きません。**
**∴ 仕様 §4-4 が許可した範囲（この1文の追加だけ）で、台帳の1行目を書き換えました。**
```
追加前の末尾 : …重複であることを隠さない(MGR 裁定 F3: 消える重複 < 残る依存)。
追加後の末尾 : …移行時、path が 'egl/' で始まる行は接頭辞を剥がして doc_id を再計算する。
```
**変更したのは `_meta` の文字列末尾への1文の追加のみです。`started_at` は保持されています**（確認済）。**他の行は1行も触っていません。**

### ⑤ `counts()`
```
counts() = {'doc_rows': 21, 'files_since_start': 22}
```

## 3. 既存行の扱い（§2・§5-1）
- **既存14行を入れ直していません。書き換えていません。**
- 台帳の行数は **36 行**（`_meta` 1 + 追記分）。**倍増していません。**
- **退役時の復元手順は `_meta` の1文で示しました。**

## 4. やらなかったこと（§5）
- **既存行の入れ直し・書き換え** — していません（`_meta` の1文を除く。§2-④で明記）。
- **列の追加** — していません。
- **`doc_id_for` の式の変更** — していません。
- **`twoder` の import（本体）** — していません。

## 5. ★別件として申告します（本 build の範囲外・修正していません）
状況表が次のエラーを出しています:
```
MGR 未応答: ERR No module named 'cc_register'
```
**`cc_register.py` は `egl/docs/` に在ります**（実装源 D-21 §2-4「`egl/docs/` 以外に書かない」に従った配置）。
**呼び出し側から `import cc_register` するには `sys.path` に `/home/takasan/egl/docs` が要ります**（私の受入実行でもそうしています）。
**`cc_register.py` 側で解決すべきか呼び出し側で解決すべきかは、私が決めることではありません。** **本 build では触っていません。**

## 6. 受入⑥⑦
- **`egl/docs/` 以外に書いていません。**
- **本番コード（`twoder`/`rri`/`ds`/`dev-workcell`）を変更していません。**

## 7. commit
**していません**（MGR）。

---
*IMPL BUILT（D-21 修正）。`normalize_path()` で `record_doc` の path を1表記に正規化（`egl/` を1回剥がし、`docs/` 以外は `ValueError`）。2表記が同じ `ART-845d63f15f` を返し、`artifact_id_for` とも一致。**★`_meta` の1文は定数を直すだけでは反映されず（`_ensure()` は既存なら書かない）、台帳1行目を書き換えて追記した——変更したのは末尾への1文のみ・`started_at` 保持・他の行は不変。** `counts()` の母数を `egl/docs` 直下の `*.md`/`*.json` に訂正。既存14行は入れ直していない。**別件として、状況表の `No module named 'cc_register'` は未対応と申告**（配置は実装源どおり・解決方針は私が決めない）。*
