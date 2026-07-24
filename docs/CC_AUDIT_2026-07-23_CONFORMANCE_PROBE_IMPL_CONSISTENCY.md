# CC 設計整合監査 — CONFORMANCE_PROBE v0.4 実装

- 監査者: Claude Code（CC-α・設計整合担当）/ 2026-07-23
- 対象: `twoder/probe/conformance_probe.py`（366行・20:01）＋ `tests/test_conformance_probe.py`・`tests/conftest.py`
- 正本: `SPEC_CONFORMANCE_PROBE_v0_4.md`
- 監査ハーネス: `egl/docs/audit_conformance_probe.py`
- **verdict: CONSISTENT**

## 監査結果

| チェック | 基準 | 結果 |
|---|---|---|
| C1 骨格保存 | §4 骨格の `<<<FILL>>>` 以外が bytes 保存 | green |
| C2 §5 不変テスト | 実配置 pytest 実行 T1–T12 | green（passed=10 / failed=0） |
| C3a テスト verbatim | §5 テスト == 実装 `tests/test_conformance_probe.py` | green |
| C3b conftest verbatim | §5 conftest == 実装 `tests/conftest.py` | green |
| C4 spy 規律 | spy/fake/mock 非import ＋ `bind_real` の SPY ガード温存 | green |

（`ladder_symbols`(8) と `_build_ladder`(9) の差は `gate4_worker` のみ＝stub で実symbol無しゆえ T8 対象から正当に除外。設計整合。）

## 環境障害（監査を一時阻害・実装欠陥ではない）

- **`/tmp` に `tmp*.jsonl` が約2,100万個** → ext4 単一ディレクトリ htree 上限で `mkdir` が `ENOSPC`（容量は444G空・inode 32%＝余裕なのに `No space left`）。
- 初回監査で C2 の `test_t9` が tempdir 作成に失敗し 1 failed。**回避: `TMPDIR=/home/...` に逃がして再監査 → C2 10/10 green。**
- **源**: `tempfile.mkstemp(suffix=".jsonl")`（prefix無し・未unlink、`twoder/regression/test_fi_min.py` 等）の過去の暴走残骸。**現 `ps` に生成源プロセス無し＝停止**（常駐は webui:8770 と vllm のみ、どちらも源でない）。
- **掃除**: `find /tmp -maxdepth 1 -name 'tmp*.jsonl' -delete` をバックグラウンド実行中（task `bpgfl3q8x`）。
- **恒久対処（別タスク）**: 該当テストの `mkstemp` を prefix付与＋teardown unlink、または `mkdtemp` 隔離に。

## 観測（設計側の軽微な未更新・CC-α のミス）

- `PROBE_SPEC = "SPEC_CONFORMANCE_PROBE_v0_3"`（`conformance_probe.py:21`）。**v0.4 骨格でこの定数を更新し忘れた＝起草ミス。実装は骨格を忠実に保存しただけ。** 実害は `BREAKAGE_LIST` の spec 名表示のみ。commit 前に SPEC 骨格を `v0_4` へ直すか次版でまとめるかは Taka 判断（骨格の固定区間なので直すと実装 1行追随が要る）。

## claim ceiling

- **言える**: 実装が SPEC v0.4 を反映（骨格保存＋§5 T1–T12 green＋発注物 verbatim＋spy規律）。**BUILT 到達。**
- **言えない**: `BREAKAGE_LIST` の走行結果（どの gate が不一致か）は §8 step3（commit 後）の relay 事項。CC は解釈・要約しない（§7 職掌）。

## 次工程（ANCHOR ★3(A)）

- 人間の扉2枚目: **commit=Taka**（現状 `?? probe/` `?? tests/`）。
- §8 step3: `BREAKAGE_LIST` 走行 → 生 jsonl relay（commit 後）。
- ★3(A) は BREAKAGE_LIST 走行痕跡で DONE 見込み。
