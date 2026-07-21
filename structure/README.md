# egl/structure — 2DER 構造再構成の機械可読層

**すべて DERIVED（導出物）。System of Record ではない。**
SoR と矛盾した場合は SoR 側が勝つ（spec §1.3）。全ファイルが `regenerable: true` / `derived_from` を持つ。

- 仕様: `../docs/STRUCTURAL_RECONSTRUCTION_SPEC_v0.1.md`
- 進行レポート（追記式）: `../docs/STRUCTURAL_RECONSTRUCTION_PROGRESS.md`

## 再生成

```
python3 s1_manifest.py   # FILE_MANIFEST.jsonl    全ファイル台帳 (1,317)
python3 s1_symbols.py    # SYMBOL_INDEX.jsonl     AST/md/json 抽出 (1,215)
python3 s1_reach.py      # REACHABILITY.jsonl     module 単位 wired (427)
```

いずれも決定論。再実行でバイト一致する（LLM 不使用）。
`*.jsonl` は自己参照を避けるため走査対象から除外される（DE-0132 同型の事故を回避）。
