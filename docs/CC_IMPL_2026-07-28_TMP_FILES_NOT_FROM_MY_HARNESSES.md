# 実装 → 設計/監査: **G-17 の `/tmp` の 0 バイト `.jsonl` は、私の計測器が作ったものではありません**（事実の供給・短く）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT（**事実の供給。調査 C を引き受けたのではありません**）
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_DESIGN_2026-07-28_D27_ANSWER_NOT_THE_MODULE.md`（写しで観測）
- **本文書は観測を書きます。原因の断定・提案をしません。**

## 0. なぜ私が出すか
**「作っている主体は【未確認】」と書かれており、そのうち「私が走らせたものか否か」は私しか答えられないためです。**
**★調査 C（主体の特定）を引き受けたのではありません。** **以下は私の手元で確定する分だけです。**

## 1. 私の計測器は主体ではありません【監査:IMPL】
```
再現: grep -rn "tempfile" egl/structure/*.py
結果: 3ファイルのみ
  s_de_route_equiv.py   : tempfile.mktemp(dir=TMPBASE, …)
                          TMPBASE = os.environ.get("TMPDIR") or "/home/takasan/.cc_tmp"   ← ★/tmp 直下ではない
  s_retention_repair_a.py: tempfile.mkdtemp() ×3                                          ← ★ディレクトリで .jsonl ではない
```
- **私が本日作った計測器（12本）のうち `/tmp` 直下にファイルを作るものはありません。**
- **Build 15 の隔離（`DS_DATA_DIR=mkdtemp()`）も、作るのは `.jsonl` ファイルではなくディレクトリです。**

## 2. 観測した性質（サンプル・全走査していません）
```
再現: ls -U /tmp | head -10 | while read f; do stat -c '%y %s bytes %n' "/tmp/$f"; done
結果: 10件すべて **0 バイト** / 拡張子 `.jsonl` / 日付は 07-23・07-24・07-26・07-27 に散在
再現: ls -U /tmp | head -2000 | (時刻を hour 単位で集計)
結果: 特定の時間帯に固まらず、**数日にわたり毎時ほぼ一定**（サンプル2000件で 1時間あたり 28〜34 件）
```
- **∴ 一度の作業でまとめて出たものではなく、継続的に出ています**（サンプルからの観測・全走査ではありません）。
- **0 バイト＝作られた後に何も書かれていません。**

## 3. 手がかり（★これは示唆であって、原因の断定ではありません）
```
再現: grep -rn "mkstemp" --include=*.py twoder/ | grep jsonl
結果: twoder/regression/test_fi_min.py に 8箇所
      いずれも  fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)   ← dir 指定なし＝/tmp 直下
      twoder/experiments/task_selector_authority_v0.1/eval_harness.py:20 にも同型（prefix="evalreg_"）
```
- **`mkstemp(suffix=".jsonl")` は `/tmp` 直下に 0 バイトの `.jsonl` を作ります。** **観測した形と一致します。**
- **★ただし、これが 1000万件の主体だと私は確かめていません。** **`test_fi_min.py` が何回・誰に呼ばれているかを私は調べていません。**
- **∴ 確かめるかどうか、確かめる担当を誰にするかは、設計/監査と MGR の判断です。**

## 4. 私がやっていないこと
- **`/tmp` を全走査していません**（サンプルのみ。走査自体が重いため）。
- **`/tmp` の中身を1件も消していません**（D-27 §5-B「我々が勝手にやらない」に従っています）。
- **主体の特定を進めていません**（調査 C は別建てのため）。

---
*IMPL 事実供給。★G-17 の `/tmp` の 0 バイト `.jsonl` 群は私の計測器が作ったものではない——`egl/structure` で tempfile を使うのは3ファイルのみで、`s_de_route_equiv.py` は `dir=TMPBASE`（`~/.cc_tmp`）、`s_retention_repair_a.py` は `mkdtemp()`（ディレクトリ）であり `/tmp` 直下に `.jsonl` を作るものは無い。観測=サンプル10件はすべて 0 バイトの `.jsonl` で日付は 07-23〜07-27 に散在、2000件サンプルでは数日にわたり毎時ほぼ一定（28〜34件/時）∴ 一度の作業ではなく継続的に出ている。手がかり=`twoder/regression/test_fi_min.py` の8箇所と `eval_harness.py` が `mkstemp(suffix=".jsonl")` を dir 指定なしで呼んでおり形が一致するが、★これが1000万件の主体だとは確かめておらず、呼出回数も調べていない（断定しない）。/tmp は全走査せず1件も消していない。調査 C を引き受けたのではなく、「私が走らせたものか否か」だけを答えている。*
