# 実装 → 設計/監査: **「取れない」を2つに割りました（文言だけ・振る舞いは不変）**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-29 / TYPE=BUILT
- **運用方針 確認済（版: v2.8）**
- 実装源: `CC_DESIGN_2026-07-29_D56_SPLIT_C_BUILD_SPEC_v1_0.md` v1.0
- **受領した文書**: 上記 / `CC_MGR_2026-07-29_D56_SPEC_APPROVED_ONE_CONTRADICTION.md`（写しで観測）/ `CC_DESIGN_2026-07-29_D56_CASE1_CONFIRMED_AND_4TH_FOUND.md`（同）/ `CC_MGR_2026-07-29_D57_STOP_FINDING_ONE_AT_A_TIME_COUNT_THEM_ALL.md`（同・**「D-56 は BUILT と受入へ進む」を確認して続行**）

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**

## 結果（★2軸）
### 経路
- [x] **実装した**（`droppedBlock` の1分岐＋呼び出し2箇所・**Python 側は1行も変えていない**）
- [x] **止まってよい場所には当たりませんでした**（§4）
### 実測
- [x] 受入1 (c1) の文言（`TASK-2DER-B9B4DA3B`・`etrace_run_id=None`）
- [x] 受入2 (c2) の文言が画面のソースに在る（**★実例が無いので「在ること」まで**）
- [x] 受入3 (b) が壊れていない（`ETR-0f6fae35665a`・Σ=0）
- [x] 受入4 **`ok`/`bad` を足していない**（★差分だけで数えた・追加8行中0件）
- [x] 受入5 既存が不変（sha256 `acc9ddba5f0f4bec` 一致）
- [x] 受入6 非回帰 91 passed / 7 failed（顔ぶれ diff 空）

---

## 1. 実装（★文言だけ。振る舞いを変えていません）
```javascript
function droppedBlock(rec,hasRunId){
  if(!rec) return "<div class='k'>取りこぼし</div><div class='v'>"
    +(hasRunId ? "取りこぼしの件数は取得できない（run_id は在るが、記録を引けなかった）"
               : "取りこぼしの件数は取得できない（この依頼の run_id が記録に無い）")+"</div>"+DROP_NOTE;
```
| 呼び出し箇所 | 渡した `hasRunId` | 理由 |
|---|---|---|
| `missingCard(s,rec)` | **`!!s.etrace_run_id`** | `/api/state` の返りに既に在る値 |
| 「run だけの画面」 | **`true`** | その経路は `/api/resolve` で**引けた** run しか通らない |

- **★新しい fetch を1つも足していません。** **★新しい状態変数を作っていません**（表示の分岐です）。
- **★どちらも「0件」と出しません。** **どちらも `DROP_NOTE` を出します。**
- **★(c2) の文言に原因を書いていません**（「引けなかった」まで）。
- **(a)(b) の文言・`DROP_NOTE`・`truncated` 併記を1文字も変えていません。**

## 2. 受入（★投入なし）
```
再現: GET /command （認証つき・HTML を実取得）
  (c1)「取りこぼしの件数は取得できない（この依頼の run_id が記録に無い）」      在り
  (c2)「取りこぼしの件数は取得できない（run_id は在るが、記録を引けなかった）」 在り
  DROP_NOTE / (a)(b) の文言 / truncated 併記                                   すべて在り

再現: GET /api/state?task_id=TASK-2DER-B9B4DA3B
  etrace_run_id = None → hasRunId=false ∴ ★(c1)

再現: GET /api/resolve?id=ETR-0f6fae35665a
  Σ dropped_before = 0 → 「記録できた取りこぼし: 0 件」＋併記（★(b) は壊れていない）
再現: GET /api/state?task_id=TASK-2DER-D84215A8
  etrace_run_id = ETR-0f6fae35665a → rec が在るので件数分岐へ

受入4 再現: git diff webui.py | grep "^+" | grep -v "^+++"   → 追加8行
            そのうち pill ok / pill bad / class='ok' / class='bad' に当たる行 → ★0件
            （★ページ全体では数えていません。差分だけで数えました）
受入5 sha256: before acc9ddba5f0f4bec / after acc9ddba5f0f4bec  ★一致
受入6: 非回帰98本 91 passed / 7 failed（基準と★顔ぶれ diff 空）
差分:  webui.py | 8 insertions(+), 5 deletions(-)   ★すべて HTML/JS 文字列の中
```

## 3. ★(c2) は実例が無いので「動いた」と書きません
- **実装源 §4-1 のとおり、`run_id` は在るが引けない依頼の実例は在りません。**
- **★作って試していません。** **示したのは「文言が画面のソースに在ること」だけです。**
- **∴ `G-61`・(a) と同じ扱いで、★未検証のまま登記されるべきものです。**

## 4. 止まってよい場所（実装源 §5・いずれにも当たりませんでした）
| # | 条件 | 実際 |
|---|---|---|
| 1 | (c1)/(c2) を分けると (b) が壊れた | **壊れていません**（Σ=0 の表示を実測） |
| 2 | 判定に新しい値が要る | **要りませんでした**（既に持っている2値だけ） |
| 3 | JS だけでは足りず Python が要る | **要りませんでした** |
| 4 | SPEC が2通りに読める | 無し |

## 5. ★観測した事実（判定はしません）
- **設計/監査が「4段目が実在した」と報告しています**（「欠損・失敗の記録なし」が2つの場合をまとめている）。
- **★その4段目は、私が D-49 で入れた文言です。**
- **本 build では触っていません**（実装源 §3「(a)(b) の文言を変えない」／MGR §順番「D-56 と D-57 を同時にやらない」に従いました）。
- **★D-57 の指示が来たら直します。**

## 6. 触ったファイル / commit
```
twoder/webui.py のみ（HTML/JS 部分）
```
**commit していません**（MGR）。**投入していません。** **資料の同期はしていません**（実装源 §6・設計/監査の担当）。

---
*IMPL BUILT（D-56）。「取れない」を2つに割った——`droppedBlock(rec,hasRunId)` の `if(!rec)` 分岐で **(c1)「この依頼の run_id が記録に無い」と (c2)「run_id は在るが、記録を引けなかった」を出し分ける**。呼び出しは `missingCard` が `!!s.etrace_run_id`、「run だけの画面」が `true`（その経路は引けた run しか通らないため）。**新しい fetch も新しい状態変数も作らず、どちらも「0件」と出さず、どちらも `DROP_NOTE` を出し、(c2) に原因を書かない**（「引けなかった」まで）。(a)(b) の文言・`DROP_NOTE`・`truncated` 併記は1文字も変えていない。★受入は**投入なしで6件**（(c1) は `TASK-2DER-B9B4DA3B` の `etrace_run_id=None`／(c2) は**実例が無いので HTML に文言が在ることまで**／(b) は `ETR-0f6fae35665a` の Σ=0 で壊れていない／**`ok`/`bad` は差分だけで数えて追加8行中0件（ページ全体では数えていない）**／`/api/state` の sha256 が `acc9ddba5f0f4bec` で前後一致／非回帰 91/7・顔ぶれ diff 空）。差分は 8 insertions / 5 deletions ですべて HTML/JS 文字列内。★(c2) は作って試さず「動いた」と書かない（`G-61`・(a) と同じ未検証扱い）。止まってよい場所4件はいずれにも当たらず、特に (b) は壊れておらず、判定に新しい値も Python 変更も要らなかった。★観測した事実=設計/監査が報告した「4段目」（「欠損・失敗の記録なし」が2つの場合をまとめている）は**私が D-49 で入れた文言**だが、本 build では触っていない（実装源 §3 と MGR の「D-56 と D-57 を同時にやらない」に従った）。D-57 の指示が来たら直す。commit・投入・資料同期はしていない。*
