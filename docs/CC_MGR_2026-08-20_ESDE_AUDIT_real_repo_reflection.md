# ESDE 監査 ―― 実 repo 反映 一本（★AXIS = REAL_REPO_REFLECTION）

**2026-08-20 20:4x ／ ★source 読解を PASS に していない ―― ★全点 実走 ／ ★実装 0 ／ 実 repo 変更 0**
**★ESDE 指標 v0.1 の ★最初の 実測データ**

---

## 1. ★★因果鎖は **一周 通った**（★throwaway 実走）

```
★Taka authority(adjudication) → reconciliation → RECONCILIATION_BALANCED → mint_real_energize
→ source_to_patch(artifact) → patch apply → ★実 file が 変わった → PATCH_APPLICATION 記録
```

**★実測の 逐語:**

```
★mint 通過        token=TOK-E2E-1
★apply            outcome=APPLIED
★実 file          'ALLOWED_TARGET_FILES = ("impl.py", "linkage.py")\n'
★★期待どおり 変わった = True
★記録 kind        ['RECONCILIATION_BALANCED', 'ENERGIZATION_ADJUDICATION', 'PATCH_APPLICATION']
```

**★★＝ ★設計は 成立する。★足りないのは ★接続と 値と ★下記の 構造欠陥。**

---

## 2. ★★門が どの 順で 拒むか（★実走で 確認 ―― ★source では 出ない）

| 与えた もの | 実測の 拒否 |
|---|---|
| 裁定 event なし | `MintRefused: no ENERGIZATION_ADJUDICATION event for adjudication_id` |
| `attribution="taka-credential"` | `MintRefused: authority_owner != TAKA` |
| `expires_at=None` | `MintRefused: adjudication has no expiry (fail-closed)` |
| 上記を 揃えた（proof 無し） | **`MintRefused: no fresh reconciler balance-proof`** ★私が 数え忘れて いた 門 |
| proof を 実際に 作って 全部 揃えた | **★通った** |

---

## 3. ★★実走で しか 出なかった 構造欠陥（★2件・★新規）

### ★欠陥A ―― `mint` の token を `apply_cycle` が **構造上 受け付けない**

```
★実測:
   bare `patch_bridge` と `twoder.patch_bridge` は ★同じ file だが ★★別の module object
   → `_EnergizedApply` が ★★別の class
   → `bridge_minter` は bare 側の class を 返す ／ `apply_cycle` は pkg 側で isinstance する
   → `_require_energize` が `TypeError: not an _EnergizedApply` を 投げる
★★∴ ★実 repo 経路は ★★『繋いでも 動かない』。★caller を 足すだけでは 直らない。
★原因 = `bridge_minter.py:26` の ★素の `from patch_bridge import _EnergizedApply`
```

### ★欠陥B ―― `/home/takasan/twoder` を `sys.path` に 入れると **stdlib が 壊れる**

```
★実測: `ImportError: cannot import name 'eq' from 'operator' (/home/takasan/twoder/operator.py)`
★★＝ ★`twoder/operator.py` が ★stdlib の `operator` を 食う。
★★＝ ★欠陥A を 「path を 足せば よい」で 直すと ★★Python 自体が 壊れる（★順序依存の 地雷）。
★★∴ ★直し方は ★`bridge_minter` の import を ★`from twoder import patch_bridge` へ 揃える 側。
```

---

## 4. ★★ESDE 3指標（★総合点に 潰さない ／ ★分母・分子・欠損ID）

### 対称性 ―― `required=6 / present=4 / missing=2`

| counterpart | reader | writer | 判定 |
|---|---|---|---|
| `ENERGIZATION_ADJUDICATION` | `bridge_minter:50` | **★0** | **MISSING** |
| `ENERGIZATION_REVOCATION` | `bridge_minter:57` | **★0** | **MISSING** |
| `RECONCILIATION_*` | `latest_balance_proof` | `emit_reconciliation` | PRESENT（★本番 caller 0） |
| `PATCH_APPLICATION` | `bridge_minter:66,120` ／ reconciler | `emit_patch_application` | PRESENT |
| real energize | `apply_cycle` | `mint_real_energize` | PRESENT（★本番 caller 0 ／ ★欠陥A で 受け取れない） |
| artifact → patch | `apply_cycle` | `source_to_patch` | PRESENT（★本番 caller 0） |

```
★missing ID = ENERGIZATION_ADJUDICATION(writer) / ENERGIZATION_REVOCATION(writer)
★★別枠で 記録: ★本番 caller を 持つ counterpart = ★1/6（`emit_patch_application` のみ）
```

### 連動性 ―― `declared=8 / observed=6 / broken=2`

```
①Taka authority → adjudication record      ★broken（writer 0）
②adjudication → mint                        ✔observed（実走）
③reconcile → proof                          ✔observed（実走）
④proof → mint                               ✔observed（実走）
⑤mint → energize token                      ✔observed（実走）
⑥token → patch apply                        ★broken（★欠陥A ／ ★bare 経路でのみ observed）
⑦apply → 実 file 変更                       ✔observed（★中身一致 True）
⑧apply → PATCH_APPLICATION 記録             ✔observed
★broken ID = ①Taka→adjudication ／ ⑥token→apply
```

### 階層性 ―― `required=5 / passed=4 / violation=1 / unreachable=0`

```
✔ authority は Taka のみ                     … ★実走で "taka-credential" を 拒否
✔ 自己発行の 禁止                            … `_FORBIDDEN_ATTRIB` allowlist
✔ reconciler は read-only inspector          … 逐語＋`refused non-read-only git subcommand`
✔ 書込は workspace に 縛られた energize 必須  … ★実走で `TypeError` に なった＝★効いて いる
★violation = ★『新規 file 配置』と『既存 file 変更』の 責務差
   ―― ★私が 今日 `_place_and_commit`（新規）と `apply_cycle`（変更）を 同じ『repo へ 置く』と 扱い
     ★「実 repo へ 書く口は 無い」と 誤報した。★★機構では なく ★私の 認識の violation。
```

---

## 5. ★★最終報告（★成立 / 不成立 / 未実証 を 分ける）

```
★★成立（★実走で 確認）
   ・adjudication → mint → proof → mint 通過
   ・source_to_patch → artifact → apply → ★実 file が 期待どおり 変わった
   ・PATCH_APPLICATION の 記録
   ・門の 拒否 4種（裁定なし／attribution／expiry／proof）
★★不成立（★実走で 確認）
   ・token → apply（★欠陥A：class 同一性）
   ・Taka authority → adjudication record（★writer 0）
★★未実証（★成立に 数えない）
   ・rollback を 実 token 経路で 通す こと（★throwaway minter では 確認済み ／ ★real token では 未）
   ・再実走 → declared/observed 照合（★実 repo 変更が 本番経路で 起きて いない ため 未到達）
   ・第四の 6条件（★①〜⑥ すべて 未実証）
```

**★「ほぼ成功」「土台完成」とは 書きません。★成立は 上の 4行だけです。**

---

## 6. ★調査方法の 自己評価（★ご指示）

```
★★なぜ 正しい 欠損を 見つけられたか
   ★『source を 読んで PASS に しない』を 守り ★★実際に `mint_real_energize` を 叩いた から。
   ★欠陥A（class 同一性）と 欠陥B（stdlib 汚染）は ★★source を 何回 読んでも 出ない。
   ★『どの 門が どの 順で 拒むか』を 1つずつ 与えて 潰した ので ★数え忘れた 門(3)も 出た。
★★外した 調査は 何を 調べた から 外れたか
   ★前々回 = ★『自分が 作った 部品の 呼び手』を 起点に 数え ★`_place_and_commit` を 見落とした。
   ★前回   = ★『10欄を 引く』まで やった が ★★門(3)の proof を ★欄では ない ので 数えなかった
             ＝ ★★『欄』を 起点に した から ★『前提条件』が 落ちた。
   ★★∴ ★起点を「欄」でも「部品」でもなく ★★『拒否条件』に 置くべきだった。
★★次回 同型を 機械的に 防ぐ 規則（★2DER へ）
   ★★R4 GATE_ENUMERATION_REQUIRED ―― ★通す 前に ★★『拒否条件を 全部 列挙し ★1つずつ 与えて
      ★実際に 拒否させる』。★通った ことだけを 見ない。★拒否が 全部 再現できて 初めて 門を 理解したと する。
```

---

## 7. ★していないこと

```
★実装 0 ／ コード 0行 ／ 実 repo 変更 0（★throwaway のみ）／ 語彙追加 0 ／ 発行口 0
★`taka-credential` を 読み替えて いない ／ 有効期限を 決めて いない
★第四を Claude が 完成させて いない ／ 実装主体は 2DER の まま
★SELF_DEV_TOKEN = ★5/5
```
