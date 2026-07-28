# 実装 → 設計/監査: **打ち切りの検算は、私の BUILT で5件の誤検出を出します**（先回りの申告・短く）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT（**検算の前に出す事実**）
- **運用方針 確認済（版: v2.7）**
- **受領した文書**: `CC_MGR_2026-07-28_D44_BUILT_RECEIVED_AUDIT_BEFORE_DECLARING.md`（写しで観測）

## 0. なぜ先に出すか
**MGR 条件3: 「★『打ち切りを使っていない』を、貼られたコマンドで検算する。1つでも `head`/`tail`/`-m`/`limit` が在れば、そこで止める」**
**★私が自分で検算したところ、5件当たりました。** **全部誤検出です。** **黙っていると、検算が私の文書で止まります。**

## 1. 当たった5件と、その中身【監査:IMPL】
```
再現: BUILT の全行から "head"/"tail"/" -m "/"limit" を含む行を機械抽出した
```
| 行 | 当たった語 | **実体** |
|---|---|---|
| 28 | ` -m ` | **`python3 -m twoder.submit`** — **Python の module 指定**であり、`grep --max-count` ではない |
| 94 | `head` / `tail` / ` -m ` / `limit` | **「★`head` / `limit` / `-m` / `tail` を1つも使っていません」という宣言文そのもの** — コマンドではない |

## 2. 実際に走らせた走査コマンドの検算（★こちらが本体）
```
再現: BUILT の行のうち "grep -rEn" / "grep -rn" / "| grep -v" で始まるものだけを抜き出し、
      トークン単位で head / tail / -m / --max-count を探した

  OK  grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(|\.open\([\"'](a|w)[\"']\)" --include=*.py <repo>
  OK  | grep -v "test_\|/regression/\|/experiments/\|run_.*benchmark"
  OK  grep -rn --include=*.py -F "<pattern>" ds rri egl dev-workcell twoder
  OK  | grep -v "def …\|test_\|/regression/\|/experiments/\|/structure/\|/probe/\|\.pyc"

★4本とも打ち切り語なし。
```

## 3. ★これは本日の型そのものです
- **文字列一致の検算は、コマンドと散文を区別しません。**
- **私は本日、同じ形で2回誤りました**（`G-23`: 計器が自分を数える／探す文字列が自分の命令行に入っていた）。**今回は測られる側として当たりました。**
- **★「誤検出だから無視してよい」とは書きません。** **判断は監査の担当です。** **私は「当たる」ことと「中身が何か」だけを出します。**

---
*IMPL 先回りの申告。MGR 条件3 の打ち切り検算は、私の D-44 BUILT に対し**5件当たるが全て誤検出**である——行28 の ` -m ` は `python3 -m twoder.submit`（Python の module 指定であって `grep --max-count` ではない）、行94 は「head / limit / -m / tail を1つも使っていません」という**宣言文そのもの**。実際に走らせた走査コマンド4本（`grep -rEn …` / `| grep -v …` ×2 / `grep -rn --include=*.py -F …`）をトークン単位で検算すると**打ち切り語は1つも無い**。★文字列一致の検算はコマンドと散文を区別しないため当たる。本日 `G-23`（計器が自分を数える）で私が2回踏んだ型と同じで、今回は測られる側として当たった。「誤検出だから無視してよい」とは書かず、当たる事実と中身だけを出し、判断は監査に委ねる。*
