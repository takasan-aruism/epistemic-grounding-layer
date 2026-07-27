# BUILD SPEC — D-21 修正: **`record_doc` の path を1つの表記に正規化する（2行）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-27_STAGE3_GO_RESUME_DEV.md` §4「**生成規則を1つに直すだけ。列を足さない**」
- 原因: `CC_DESIGN_2026-07-27_D21_PATH_CONVENTION_DEFECT.md`（**私の設計の内部矛盾**）

## 0. なぜ要るか（1行）
**台帳に2つの表記が混在し、`doc_id` が登記と一致しない行が14行ある。** **表記を1つに寄せないと、ずれ検出が毎回誤検出する。**

## 1. 直すもの（`egl/docs/cc_register.py` のみ・列を足さない）
```
record_doc(path, ...) の冒頭で path を正規化する:
  - 先頭の "egl/" を1回だけ剥がす
  - 正規化後が "docs/" で始まらなければ ValueError（★中核性質を守る検査）
  - 台帳に書く path は正規化後の値
```
- **`doc_id_for` は変更しない**（式は `artifact_registry` と一致している）。
- **`record_done` は `doc_id` を受けるだけなので変更しない。**
- **列を足さない。行の種類を増やさない。**

## 2. 既存14行の扱い（★入れ直さない）
- **追記のみなので消せない。** **正しい id で入れ直すと `DOC` 行が倍になり、ずれ検出の分母が汚れる。**
- **∴ そのまま残す。** **`path` は読める形なので、退役時に接頭辞を剥がして再計算すれば復元できる。**
- **★`_meta` の退役条件に1文だけ足す**（**列ではない。`_meta` の文言**）:
  > 「移行時、`path` が `egl/` で始まる行は接頭辞を剥がして `doc_id` を再計算する。」

## 3. 併せて直す（MGR の計器が誤検出しているため・置き換えであって追加ではない）
**`counts()` の `files_since_start` が数える対象を、`CC_*.md` に限定しない。**
- **理由**: 常設文書（`2DER_EXECUTION_ARCHITECTURE.md` / `.json`）も台帳に載せるべきものだが、glob が `CC_*.md` のみのため**ファイル側に現れず、常にずれとして出る**。
- **対象**: `egl/docs/` 直下の `*.md` と `*.json`（`CC_REGISTER.jsonl` 自身と `cc_register.py` は除く）。
- **★これは追加ではなく、母数の訂正である。**

## 4. 受入
1. **`record_doc("egl/docs/X.md", …)` と `record_doc("docs/X.md", …)` が同じ `doc_id` を返すこと**（実行して両方貼る）。
2. **`record_doc("elsewhere/X.md", …)` が `ValueError` になること。**
3. **返る `doc_id` が `artifact_registry.artifact_id_for("egl", "docs/X.md")` と一致すること**（照合のための一時 import は可・本体では import しない）。
4. **`_meta` に §2 の1文が入っていること**（**既存の `_meta` 行は追記のみの台帳の1行目なので、書き換えてよいのはこの1文の追加だけ**。**★書き換えたことを BUILT に明記する**）。
5. **`counts()` の実行結果**（§3 の後）。
6. **`egl/docs/` 以外に書かないこと。本番コード（`twoder`/`rri`/`ds`/`dev-workcell`）を変更しないこと。**
7. **列を足していないこと・行の種類を増やしていないこと。**
8. **commit しない。** 冒頭に「運用方針 確認済（版: v1.9）」。定型見出し（到達経路 / 前回からの持ち越し）。

## 5. やらないこと
1. **既存14行を入れ直さない・書き換えない。**
2. **列を足さない。**
3. **`doc_id_for` の式を変えない。**
4. **`twoder` を import しない**（照合の一時 import を除く）。

---
*BUILD SPEC v1.0（★実装源）。D-21 修正=`record_doc` の path を1つの表記に正規化する（先頭の `egl/` を1回剥がし、`docs/` で始まらなければ ValueError、台帳には正規化後を書く）。`doc_id_for` と `record_done` は変更しない。列を足さない。★既存14行は入れ直さない（倍になり分母が汚れる）——`_meta` の退役条件に「移行時 `egl/` 接頭辞を剥がして再計算する」の1文だけ足す。併せて `counts().files_since_start` の glob を `CC_*.md` 限定から `egl/docs/` 直下の `*.md`/`*.json` に広げる（常設文書が常にずれとして出るため・追加でなく母数の訂正）。受入=2表記が同じ id を返す／`docs/` 以外は ValueError／`artifact_registry` と一致／`_meta` の1文／`counts()` の結果／`egl/docs/` 以外に書かない／列を増やしていない。*
