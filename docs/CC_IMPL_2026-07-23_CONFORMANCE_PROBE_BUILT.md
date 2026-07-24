# 実装担当 → 設計/監査担当: CONFORMANCE_PROBE 実装完了（BUILT・handoff signal）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-23
- 対応: `SPEC_CONFORMANCE_PROBE_v0_4.md`（設計担当 CC-α 投下）

## 成果物（working tree・未commit）

- `twoder/probe/conformance_probe.py`（+ `probe/__init__.py`）— 骨格 FILL×4 実装
- `twoder/tests/test_conformance_probe.py`・`twoder/tests/conftest.py`（発注側同梱を **verbatim 配置**・worker は書いていない）

## 検証（決定論・環境非依存）

- **§5 不変テスト 10/10 green**（T5–T12 ＋ 全緑保持 ＋ halt→NOT_TRAVERSED。実行 0.07s）
  - T1–T4 は test 関数でなく設計保証: 実 symbol(bind_real, spy 0)／:8005 不接触(stub chat_fn)／実 repo 無改変／台帳隔離
- 骨格保存 `verify_skeleton_preserved` = True（固定4区間 byte 一致）
- CLI smoke OK: `python3 -m twoder.probe.conformance_probe` → 9 records の `BREAKAGE_LIST.jsonl` 生成
- **実 repo/台帳 無改変**: working tree = `probe/`・`tests/` のみ。run() が `EGL/DS/DW/RRI_DATA_DIR` を tempfile へ throwaway 隔離し復元

## 設計反映（要点）

- run() は実 `run_minimal_slice`/`validate_approval`/`grant_approval`/`mirror_package`/`verify_skeleton_preserved` を bind_real で呼ぶ（spy 禁止=T1）。gate4 のみ stub chat_fn（:8005 不接触=T3）。
- fault injection は inject 指定時のみ・injected=True で実所見と分離（既定 0 件=T10）。
- gate1b は観測専用（override=None）で `{"distinct": bool}` のみ記録（生 id 非記録=V-2）。gate3 は synthpkg 複製（`twoder/operator.py` shadow を回避／実 twoder 複製は §5 範囲外=`UNRESOLVED_REAL_PKG_UNTESTED`）。

## ハンドオフ

- 次: **設計担当の CONFORMANCE 版 設計整合監査 → CONSISTENT 確定 → commit=Taka**（人間の扉2枚目、現状 `?? probe/ ?? tests/`）。
- **BREAKAGE_LIST の中身は解釈しない（§7）。** 走行→生 jsonl relay は commit 後の §8 step3。実装担当は要約・優先順位付けをしない。
