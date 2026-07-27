# BUILD SPEC — D-21: **CC 管理台帳（暫定）を1本作る**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-27_D21_RULINGS.md`（承認＋裁定 F1/F3）
- 設計: `CC_DESIGN_2026-07-27_D21_CC_REGISTER_DESIGN.md`（`BUILD_ROLE: 参照`）

## 0. 目的とゴール（これ以外を成果としない）
- **目的**: **3インスタンスが「どの文書が在り、誰宛で、未処理か」を、ディレクトリ走査でなく1本から知る。**
- **ゴール**: **状況表の「MGR 未応答」が `ls` と mtime ではなく台帳から出ている。**
- **★これ以外の機能を足さない**（v1.9）。**足したくなったら止めて MGR へ。**

---

## 1. 作るもの（2つだけ）

### 1-1. 台帳 `egl/docs/CC_REGISTER.jsonl`
**1行目に `_meta` を固定で置く（逐語・この内容を必ず含める）:**
```json
{"_meta": "CC 管理台帳(暫定)。目的=3インスタンスが『どの文書が在り、誰宛で、未処理か』をディレクトリ走査でなく1本から知る。★退役条件=front door から ART- の本文が返るようになったら、内容を artifact_registry の登記へ移し、本台帳と本 _meta の doc_id 計算式の重複、および状況表のずれ検出行を同時に廃止する。doc_id = 'ART-' + sha1('<repo>|<relative_path>').hexdigest()[:8] ——式の出所は twoder/artifact_registry.py の artifact_id_for()。重複であることを隠さない(MGR 裁定 F3: 消える重複 < 残る依存)。", "started_at": "<実時刻>"}
```
- **★`twoder` を import しない**（裁定 F3）。**式を書く。**
- **★`artifact_id_for()` を読んで、桁数と区切りを実物に合わせること。** **推測で書かない。** **合わせた結果を BUILT に書く。**

**行は2種類だけ:**
```
{"kind":"DOC","doc_id":"ART-xxxxxxxx","path":"egl/docs/CC_....md",
 "type":"HANDOFF|BUILD_SPEC|BUILT|FINDING|STATUS",
 "from":"MGR|DESIGN|IMPL","to":"MGR|DESIGN|IMPL|TAKA",
 "build_role":"IMPL_SOURCE|REFERENCE|SUPERSEDED",
 "supersedes":"ART-yyyyyyyy|null","ts":"<実時刻>"}

{"kind":"DONE","doc_id":"ART-xxxxxxxx","by":"MGR|DESIGN|IMPL",
 "by_doc_id":"ART-zzzzzzzz","ts":"<実時刻>"}
```
**★列を足さない。** **追記のみ。状態を書き換えない。**

### 1-2. 書き込み・読み出しの道具 `egl/docs/cc_register.py`
**3インスタンスが同じ形で書くための1ファイル。標準ライブラリのみ。LLM 不使用。**
```
record_doc(path, type, frm, to, build_role, supersedes=None) -> doc_id
record_done(doc_id, by, by_doc_id)                            -> None
pending(to=None)                                              -> DOC 行のうち DONE の無いもの
counts()                                                      -> {"doc_rows": n, "files_since_start": m}
```
- **`ts` は実時刻を入れる**（本台帳は我々の連携用であり、2DER の ts 受領規律の対象外）。
- **★`counts()` の `files_since_start`**: **`_meta.started_at` 以降に作られた `egl/docs/CC_*.md` だけを数える。** **過去の文書は数えない**（前向きのみ・数えると常にずれる）。
- **排他制御を作らない**（裁定 F4／F2。**追記のみで進め、取りこぼしはずれ検出が捕まえる**）。

---

## 2. やらないこと
1. **過去の `CC_*.md` を登録しない。** **前向きのみ。**
2. **列を足さない**（所要時間・集計・要約・優先度・2DER 領域データ）。
3. **`twoder` を import しない。**
4. **状況表を書き換えない**（MGR の持ち場）。**`counts()` と `pending()` を用意するところまで。**
5. **本番コード（`twoder`/`rri`/`ds`/`dev-workcell`）を変更しない。**
6. **排他制御・retry・ロックを作らない。**

---

## 3. 受入
1. **`_meta` の1行目に、退役条件と式の出所が入っていること**（§1-1 の内容を含む）。
2. **`artifact_id_for()` を実読し、桁数・区切りを合わせたことを `file:line` で書く。** **合わせた式を BUILT に貼る。**
3. **`record_doc` → `pending` → `record_done` → `pending` を1往復実行し、結果を貼る**（`pending` から消えること）。
4. **`counts()` の実行結果を貼る。**
5. **`egl/docs/` 以外に書いていないこと。**
6. **本番コード無変更。**
7. 観測と実装を書き、判定・評価をしない。**commit しない。**
8. **BUILT に定型見出し（到達経路 / 前回からの持ち越し）を置く。**
9. **v1.5**: 「動く」と書くときは再現コマンドと結果を併記。

## 4. 予想（実測前に固定）
| 項目 | 予想 |
|---|---|
| `artifact_id_for` の形 | **`"ART-" + sha1(f"{repo}|{relative_path}").hexdigest()[:8]`**。**桁数は【未確認】——実読で決める** |
| `counts()` の初回 | **`doc_rows` と `files_since_start` が一致する**（`started_at` 以降のみ数えるため） |

---

## 5. 位置づけ
- **これは暫定である。** **退役条件を満たしたら消す。**
- **★台帳ができても「2DER で管理されるようになった」と書かない。** **これは 2DER の外に置く、我々の連携用の台帳である。**

---
*BUILD SPEC v1.0（★実装源）。D-21=CC 管理台帳（暫定）を1本作る。作るのは2つだけ——`egl/docs/CC_REGISTER.jsonl`（1行目の `_meta` に退役条件・doc_id の式・式の出所・重複を隠さない旨・`started_at` を固定）と `egl/docs/cc_register.py`（`record_doc`/`record_done`/`pending`/`counts` の4関数・標準ライブラリのみ）。行は `DOC` と `DONE` の2種だけ・追記のみ・状態を書き換えない・列を足さない。★`twoder` を import せず式を書く（裁定 F3: 消える重複 < 残る依存）が、`artifact_id_for()` を実読して桁数と区切りを合わせる（推測しない）。★`counts().files_since_start` は `started_at` 以降の `CC_*.md` だけを数える（過去を数えると常にずれる）。排他制御を作らない（取りこぼしはずれ検出が捕まえる）。やらない=過去の登録／列の追加／`twoder` の import／状況表の書き換え（MGR の持ち場）／本番コード変更／ロックの実装。受入=`_meta` の内容、`artifact_id_for` を実読して合わせた式を `file:line` つきで、`record_doc→pending→record_done→pending` の1往復、`counts()` の結果。暫定であり退役条件を満たしたら消す。台帳ができても「2DER で管理されるようになった」と書かない。*
