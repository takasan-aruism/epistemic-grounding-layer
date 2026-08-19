# 宛: Taka / 設計 / 監査 ―― 重複を**芯で**直した（★完了条件 成立 ／ ★B・C は実走できず理由を特定）

**実 repo 書き込み 0。サイクル本体は書いていない。暴走 TASK は BLOCKED のまま未接触。**

## 0. 完了条件

| 条件 | 実測 |
|---|---|
| 実物の `dry_run_apply` 出力を**無加工**で `dry_run_ok` に渡して `proceed=True` | **★`{'proceed': True, 'reason': None, 'names': []}`** |
| dry-run と apply の filename 集合一致 | **★dry-run `['t.txt']` ／ preimage `['t.txt']` ／ 記録 `['t.txt']` ／ apply後 `['t.txt']`** |
| fail-closed 維持 | **★人工的な不正 duplicate は `duplicate_file` で拒否のまま** |
| 実 repo 書き込み 0 | **★成立**（すべて `/tmp/dedup-*` 配下） |

## 1. ★四問の確認結果（★すべて実物）

### ① 原因は本当に `a/` と `b/` の両側取得か → **★そのとおり**

```
`validate_artifact`（★16-17行・修正前）:
    tokens = artifact['diff'].split()
    filenames = tuple(t[2:] for t in tokens if t.startswith('a/') or t.startswith('b/'))
★実測: modify → ('t.txt','t.txt') ／ 複数file → ('x.txt','x.txt','y.txt','y.txt')
```

### ② create / delete / rename で意味を失わないか → **★失わない（★理由は3つとも別）**

```
★rename … `--- a/old.txt` / `+++ b/new.txt` ＝ ★名前が 違う ∴ ★両方 残る（★実測: ('old.txt','new.txt')）
★★create … `--- /dev/null` → ★`canonical_diff_artifact` が ★先に 拒否（'not a unified diff'）
★★delete … `+++ /dev/null` → ★同上
   逐語（`canonical_diff_artifact`）:
     if line.startswith('--- a/'): has_diff_header = True
     if line.startswith('+++ b/'): has_add_header = True
     if not (has_diff_header and has_add_header): raise ValueError('not a unified diff')
★★∴ ★create / delete は ★そもそも この 経路に 入れない
   ＝★dedupe で 失う 意味は ★無い（★但し ★★別の 発見＝§3）
```

### ③ 順序に意味が在るか → **★在る（★4箇所とも順に使う）∴ 順序を保った**

```
_apply_to_working      … for filename in dict.fromkeys(validated.filenames)  ＝ 順に 当てる
capture_preimage       … for filename in validated.filenames                 ＝ 順に 読む
emit_patch_application … 'filenames': list(validated.filenames)              ＝ 記録に そのまま
dry_run_apply          … for filename in validated.filenames                 ＝ 順に 並べる
★`dict.fromkeys` は ★挿入順を 保つ ∴ ★決定論（★実測: 5回とも ('x.txt','y.txt')）
```

### ④ 3箇所で同じ集合になるか → **★なった（★実走）**

```
dry-run ['t.txt'] ／ preimage ['t.txt'] ／ 記録 ['t.txt'] ／ apply後 ['t.txt'] ／ on-disk 'world\n'
```

## 2. ★直したもの（★1箇所・★抽出の時点）

```python
filenames = tuple(dict.fromkeys(
    t[2:] for t in tokens if t.startswith('a/') or t.startswith('b/')))
```

```
★足場で 黙って 除去していない（★Taka 逐語）＝★芯で 直した
★`_apply_to_working` の `dict.fromkeys` は ★防御として 残した（★Taka 逐語）
★`dry_run_ok` の「duplicate_file → reject」は ★1文字も 変えていない
```

## 3. ★★B・C が実走できなかったこと（★隠さない）

```
★Taka の 試験計画 B（create）／ C（delete）は ★★実走できなかった。
★理由は ★私の 手落ちでは なく ★★`canonical_diff_artifact` が ★構造的に 拒否するから:
   ★`--- a/` と `+++ b/` の ★両方が 無いと ★'not a unified diff'
★∴ ★現在の 2DER は ★★modify（と rename 形）しか 扱えない。
★★これは ★今回の 修正対象では ない ／ ★私は 直していない。
★★但し ★『repo 自己更新』の 本線では ★create（新しい部品を 置く）が ★要る 見込み
   → ★★別件として 記録する（★次に 効いてくる）。
```

## 4. ★他に触れていないもの

```
★`would_write_sha256` の 回帰（★diff の fingerprint を 返す）＝★別件・★未修正（★Taka 逐語どおり）
★allowed_files ／ fingerprint ／ preimage ／ provenance の 意味 ＝★不変
★bridge_minter ／ authority ／ connector ／ delegated energize ＝★未接触
```

## 5. 次（★Taka の順序どおり）

```
connector 本線接続 → delegated energize → 初回 real-repo 1件
★サイクルに 要る 部品は ★全部 揃った:
   dry_run_ok ／ rollback_allowed ／ rollback_outcome ／ unresolved_rollback ／ patch_correspondence
★足場が するのは ★順に 呼ぶ ことだけ（★判断は 1つも 書かない）
```
