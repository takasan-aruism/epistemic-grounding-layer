# 実装 → 設計/監査: D-21 CC 管理台帳（暫定）を1本作った（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-27_D21_SPEC_CC_REGISTER.md` v1.0
- **受領した文書**: 上記実装源 / `CC_DESIGN_2026-07-27_D21_CC_REGISTER_DESIGN.md`（参照）
- **本文書は観測と実装を書きます。判定・評価をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` の削除: **[x] 実施済**（本 build では触っていない）

---

## 1. 作ったもの（2つだけ）
| ファイル | 内容 |
|---|---|
| `egl/docs/CC_REGISTER.jsonl` | 1行目に `_meta`（退役条件・式・式の出所・重複を隠さない旨・`started_at`） |
| `egl/docs/cc_register.py` | `record_doc` / `record_done` / `pending` / `counts`（＋補助 `doc_id_for` / `started_at`）。**標準ライブラリのみ** |

**`egl/docs/` 以外に書いていません**（受入⑤）:
```
-rw-rw-r-- CC_REGISTER.jsonl  1190 B
-rw-rw-r-- cc_register.py     5550 B
```

## 2. ★受入② — `artifact_id_for()` を実読して合わせました
**出所**: `twoder/artifact_registry.py:30-31`
```python
def artifact_id_for(repo_name, relative_path):
    return "ART-" + hashlib.sha1((repo_name + "|" + relative_path).encode()).hexdigest()[:10]
```
**実装源 §4 の予想は「桁数は【未確認】——実読で決める」でした。実物は `[:10]` です**（仕様本文の例示は `[:8]`）。**実物を採りました。**

**書き写した式（`twoder` を import していません・裁定 F3）**:
```python
def doc_id_for(relative_path, repo=REPO):
    return "ART-" + hashlib.sha1((repo + "|" + relative_path).encode()).hexdigest()[:10]
```
**一致の実測（再現コマンドと結果・v1.5）**:
```
cc_register.doc_id_for("docs/CC_x.md")              = ART-32ae52c44d
artifact_registry.artifact_id_for("egl","docs/CC_x.md") = ART-32ae52c44d
一致 = True
```
※ この照合のためだけに `artifact_registry` を一時 import しました。**`cc_register.py` 本体は import していません。**

## 3. ★受入③ — 1往復の実行結果
```
record_doc(...)  -> ART-ffd8456279
pending(to="DESIGN")  件数=1 / 当該を含む=True
record_done(ART-ffd8456279, "DESIGN", "ART-dummy0001")
pending(to="DESIGN")  件数=0 / 当該を含む=False      ← ★pending から消えた
```

## 4. ★受入④ — `counts()` の実行結果
```
counts()    = {'doc_rows': 1, 'files_since_start': 0}
started_at  = 2026-07-27T20:32:06
```
**実装源 §4 の予想「初回は `doc_rows` と `files_since_start` が一致する」は、実際には `1` と `0` で一致しませんでした。**
**観測された事実**: `files_since_start` は `_meta.started_at`（20:32:06）以降に作られた `CC_*.md` を数えます。**登録した文書は `started_at` より前に作られたもの**（Build 12 の BUILT）なので数えられていません。**私は原因の判定をしません。**

## 5. 台帳の実物（全3行）
```json
{"_meta": "CC 管理台帳(暫定)。… doc_id = 'ART-' + sha1('<repo>|<relative_path>').hexdigest()[:10]
 ——式の出所は twoder/artifact_registry.py:30-31 の artifact_id_for()。実読して区切り '|' と桁数 [:10] に
 合わせた(仕様案の [:8] は【未確認】とされていたため実物を採った)。重複であることを隠さない
 (MGR 裁定 F3: 消える重複 < 残る依存)。", "started_at": "2026-07-27T20:32:06"}
{"kind":"DOC","doc_id":"ART-ffd8456279","path":"egl/docs/CC_IMPL_2026-07-27_BUILD12_RUN_WORKER_BUILT.md",
 "type":"BUILT","from":"IMPL","to":"DESIGN","build_role":"REFERENCE","supersedes":null,"ts":"2026-07-27T20:32:06"}
{"kind":"DONE","doc_id":"ART-ffd8456279","by":"DESIGN","by_doc_id":"ART-dummy0001","ts":"2026-07-27T20:32:06"}
```
**行は `DOC` と `DONE` の2種だけ。列を足していません。追記のみで、状態を書き換えていません。**

## 6. やらなかったこと（実装源 §2）
- **過去の `CC_*.md` を登録していません**（前向きのみ）。
- **列を足していません。**
- **`twoder` を import していません**（`cc_register.py` 本体）。
- **状況表を書き換えていません**（`counts()` と `pending()` を用意するところまで）。
- **本番コード（`twoder`/`rri`/`ds`/`dev-workcell`）を変更していません。**
- **排他制御・retry・ロックを作っていません。**

## 7. 位置づけ（緩めません）
- **これは暫定です。** 退役条件（front door から `ART-` の本文が返る）を満たしたら消します。
- **台帳ができても「2DER で管理されるようになった」とは書きません。** **これは 2DER の外に置く、我々の連携用の台帳です。**

## 8. commit
**していません**（MGR）。

---
*IMPL BUILT（D-21）。`egl/docs/CC_REGISTER.jsonl` と `egl/docs/cc_register.py` の2つだけを作成。**`artifact_id_for()` を `twoder/artifact_registry.py:30-31` で実読し、区切り `"|"`・桁数 `[:10]` に合わせた**（仕様例示の `[:8]` でなく実物を採用）——一致を実測で確認（`ART-32ae52c44d`）。`record_doc→pending→record_done→pending` の1往復で pending から消えることを確認。**`counts()` は `{'doc_rows':1,'files_since_start':0}` で、予想の「一致する」とは異なった**（登録対象が `started_at` 前の文書だったため・原因の判定はしない）。`twoder` を import せず・列を足さず・追記のみ・本番コード無変更。暫定であり退役条件を満たしたら消す。*
