# 実装 → 設計/監査: **依頼を `run_id` で開けるようにしました。DW を通っていない依頼も「無い」と出ます**（投入なし）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-29 / TYPE=BUILT
- **運用方針 確認済（版: v2.8）**
- 実装源: `CC_DESIGN_2026-07-29_D50_OPEN_BY_RUN_BUILD_SPEC_v1_0.md` v1.0
- **受領した文書**: 上記 / `CC_DESIGN_2026-07-29_D50_HANDOFF_TO_IMPL.md`

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**

## 結果（★2軸）
### 経路
- [x] **実装した**（`/command` の JS のみ・**Python 側は1行も変えていない**）
- [x] **★止まってよい場所には当たりませんでした**（§6）
### 実測
- [x] 受入1 `task_id` が在る run → 既存の描画へ合流（`TASK-2DER-D84215A8`）
- [x] 受入2 `task_id` が無い run → ②④⑤⑥ が「無い」と出る分岐（`ETR-f0fe8461c407`）
- [x] 受入3 ③が両方で全件（`count`/`total`/`truncated` 表示つき）
- [x] 受入4 ④の id が出る（`UTT-0833` / `RSIG-00329`）
- [x] 受入5 存在しない run で壊れない
- [x] 受入6 既存の `task_id` 経路が不変（sha256 一致）
- [x] 受入7 非回帰 91 passed / 7 failed（顔ぶれ diff 空）

---

## 1. 実装（`/command` の JS のみ）
| # | 追加 |
|---|---|
| 受け口 | **`ETR-…` の入力欄1つ＋OPEN ボタン**／**起動時に `?run=ETR-…` を読む**。**どちらも既存の「TASK を決める道」に合流させ、別の描画系を作っていません** |
| `openByRun(rid)` | `/api/resolve` で引く → `resolved=false` なら**「その run は記録に無い」**（エラー画面にしない）→ events から `task_id` を集める → **1件なら `TASK` に入れて既存の `load()` をそのまま呼ぶ** → **0件なら「run だけの画面」** → **複数なら「この run には task_id が複数在る」と出して止める**（どれを採るかは決めていない、と画面にも書く） |
| ③ | **両方の場合で** `ts` / `component` / `function` / `result` / `error` を**全件**。**`count` と `total` を必ず出し、`truncated` なら「★打ち切られた: total N 件中 M 件」** |

**★`task_id` が無いときの文言は、MGR 逐語のまま入れました:**
```
② 現在地      : 「この依頼は DW を通っていない。DW 上の現在地は無い」
④ 根拠と結果  : 発話 id / RRI 記録 id を出し、EGL は「無い」
⑤ 欠損・失敗  : event ごとの result / error。boundary_failures は「run からは取れない」
⑥ 次に誰が何を: 「DW task が無いため、次の操作は記録されていない」
```
- **★空欄にしていません。** **★赤字・警告色にしていません**（`class` は既存の `card`/`v`/`k` のみ。`bad` を使っていません）。
- **★`task_id` が無いときに `/api/state` を叩いていません**（分岐で完全に切っています）。
- **★埋めるために新しい状態や推測を作っていません。**

## 2. 受入（★投入なし。既存の run を使いました）
### 2-1. 受け口が画面に在ること（HTML を実取得して確認）
```
再現: GET /command （認証つき・HTTP 200）
  ETR- 入力欄        在り
  OPEN ボタン        在り
  ?run= の読み取り    在り
  openByRun 本体     在り
```

### 2-2. 受入1（`task_id` が在る run）
```
再現: GET /api/resolve?id=ETR-0f6fae35665a
  resolved=True count=6 total=6 truncated=False
  events から拾える task_id = ['TASK-2DER-D84215A8']  → ★1件 ∴ 既存の load() 経路へ合流
```

### 2-3. 受入2・4（`task_id` が無い run）
```
再現: GET /api/resolve?id=ETR-f0fe8461c407
  resolved=True count=21 total=21 truncated=False
  events から拾える task_id = []      → ★0件 ∴「run だけの画面」へ
  ★④に出る id: 発話 = ['UTT-0833'] / RRI 記録 = ['RSIG-00329']
  ★⑤ result が OK でない event = 0件 ∴「全 event の result は OK（失敗の記録なし）」を出す
```

### 2-4. 受入5（存在しない run）
```
再現: GET /api/resolve?id=ETR-000000000000
  resolved=False / record=None  → ★「その run は記録に無い」の分岐
```

### 2-5. 受入6・7
```
受入6: GET /api/state?task_id=TASK-2DER-D84215A8
       before acc9ddba5f0f4bec / after acc9ddba5f0f4bec  ★一致（Python を変えていないので当然だが実測した）
受入7: 非回帰98本 91 passed / 7 failed（基準と★顔ぶれ diff 空）
```

## 3. ★Python 側を1行も変えていないこと
```
再現: cd /home/takasan/twoder && git diff --stat webui.py
  webui.py | 48 +++++++++++++++++++++++++++++++++++++++++++++++-
  1 file changed, 47 insertions(+), 1 deletion(-)
```
- **追加47行はすべて HTML/JS の文字列内**です（`openByRun` / `passedCardFromRun` / `evRows` / 入力欄 / `?run=` の読み取り）。
- **削除1行**は `load();` の行で、**`if(_q){…openByRun(_q);} else { load(); }` に置き換えたものです**。**★`task_id` で開く既存の道を消していません**（`?run=` が無ければ従来どおり `load()` が走ります）。
- **`build_state` / endpoint / `ids.py` / `emit` / `/` を1行も触っていません。**

## 4. ★予想と実際（実装源 §4-1）
| 項目 | 設計の予測 | **実際** | 判定 |
|---|---|---|---|
| 受入1 が通る | 通る方に賭ける | **通った** | 当たり |
| 受入2 が通る | 通る方に賭ける | **通った** | 当たり |
| ③ の件数 | 予想しない | 6件 / 21件 | — |
| `/` が影響を受けるか | 予想しない | **確かめていません**（触っていませんが、`/` を開いて確認していません） | **未確認のまま** |

## 5. ★見ていないこと（重要）
- **★私はブラウザで画面を開いていません。** **示したのは (a) HTML に受け口と関数が在ること (b) その JS が読むデータが API から実際に返ること の2点です。**
- **∴ 「1画面で分かる」という見え方は確かめていません。** **実装源 §6-1 の未確認をそのまま引き継ぎます。**
- **∴ 「UI で開けるようになった」とは書きません。** **書けるのは「開くための受け口と分岐を実装し、その分岐が使うデータが実在することを実測した」ことです。**

## 6. 止まってよい場所（実装源 §5・いずれにも当たりませんでした）
| # | 条件 | 実際 |
|---|---|---|
| 1 | `task_id` が複数在った | **無し**（1件 / 0件のみ）。★複数の場合の表示は実装しましたが、**発火させていません** |
| 2 | `task_id` が在るのに `no such task` | **無し**（`TASK-2DER-D84215A8` は引けた） |
| 3 | **JS だけでは足りず Python が要る** | **無し。★JS だけで足りました** |
| 4 | SPEC が2通りに読める | 無し |

## 7. 触ったファイル / commit
```
twoder/webui.py のみ（HTML/JS 部分）
```
**commit していません**（MGR）。**投入していません**（実装源 §3）。

---
*IMPL BUILT（D-50）。「案件を開く」の鍵に `run_id` を足した——`/command` の JS のみで **Python 側は1行も変えていない**（`git diff --stat` は 47 insertions / 1 deletion で、削除1行は `load();` を `if(_q){…openByRun(_q);} else { load(); }` に置き換えたもの＝**既存の task_id 経路は消していない**）。実装=`ETR-` 入力欄＋OPEN ボタンと `?run=` の読み取りを既存の「TASK を決める道」に合流させ、`openByRun` は決定論で分岐（`resolved=false`→「その run は記録に無い」でエラー画面にしない／`task_id` 1件→既存 `load()` へ合流／0件→「run だけの画面」／複数→「複数在る」と出して止める）、③は両方の場合で `ts/component/function/result/error` を全件・`count`/`total` を必ず出し `truncated` なら打ち切りを明示。★`task_id` が無いときの②④⑤⑥は MGR 逐語の文言をそのまま出し、**空欄にせず・赤字や警告色を使わず・`/api/state` を叩かず・推測で埋めない**。★受入は**投入なしで7件すべて実測**（`ETR-0f6fae35665a` は task_id 1件で既存経路へ／`ETR-f0fe8461c407` は task_id 0件で run だけの画面へ・④に `UTT-0833` と `RSIG-00329` が出る・result が OK でない event は0件／存在しない run は `resolved=False`／`/api/state` の sha256 が `acc9ddba5f0f4bec` で前後一致／非回帰 91/7・顔ぶれ diff 空）。予測は受入1・2 とも当たり、③の件数と `/` への影響は予想しないとされ、**`/` は触っていないが開いて確かめてもいない（未確認のまま）**。★見ていないことを明記=**ブラウザで画面を開いていない**ので示したのは「HTML に受け口と関数が在ること」と「その JS が読むデータが API から実際に返ること」の2点であり、**「UI で開けるようになった」とは書かない**。止まってよい場所4件はいずれにも当たらず、特に **JS だけで足りた**（Python を変える必要が出なかった）。触ったのは `twoder/webui.py` のみ、commit せず、投入もしていない。*
