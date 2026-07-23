# CC 投入前監査（詳細・relay 用）— PKG_MIRROR v0.4

- 監査者: Claude Code（監査のみ）/ 日付: 2026-07-23
- 対象: `パッケージ複製 seam（PKG MIRROR）実装仕様 v0.4`（v0.3 を SUPERSEDE）
- 前報: `docs/CC_AUDIT_2026-07-23_PKG_MIRROR_v0_3.md`（Finding 1 blocker / Finding 2 risk）
- 結論: **Finding 1・2 とも解消を確認。submit ブロッカーは無い。残るは submit 機構側の必須 1 点（contract マーカー）。**
- 用途: Claude Web への relay。事実と `file:line` のみ。修正案・優先順位付け・評価語は含めない。

---

## 🟢 Finding 1（artifact 発見）— 解消を確認（コード読取・環境非依存）

v0.4 `_load_artifact` の第2候補 `_HERE/impl.py` が実 artifact を指す。

```
- worker は tp["target_file"]（既定 "impl.py"）を ws へ書く / qwen_worker.py:88-89 (_safe_target_path(workspace,...)), LocalWorker.run:26
- test は tp["test_file"]="test_impl.py" として同じ ws に seed / live_worker_runtime.py:104-106
- 実行は subprocess pytest test_impl.py（cwd=ws）/ live_worker_runtime.py:116, _run_test:36-41
- _HERE = dirname(abspath(__file__)) = ws → _HERE/impl.py = ws/impl.py ✓
- v0.3 の 0/10 原因（探索名を pkg_mirror.py にしていた）は消えた
```

---

## 🟢 Finding 2（sandbox の `import twoder`）— 構造的に回避を確認

```
- §3 のテスト import は ast, hashlib, importlib.util, json, os, subprocess, sys, pytest のみ
- import twoder はテスト内・artifact 内（S10 が AST で静的 import を禁止）とも 0 件
- pkg_root fixture は synthpkg を tmp に生成（実 twoder 不使用）。
  代表性: __init__.py / 平坦モジュール / intra-package import（beta→alpha）/ サブパッケージ（sub/gamma）
- クロスプロセス検証 _run は自前で env={**os.environ,"PYTHONPATH":sandbox} を張る
  → death#7（_run_test が PYTHONPATH 無設定 = live_worker_runtime.py:41）に依存しない
- Y-4 撤回（「偽パッケージ＝族A」）は妥当。失うもの（実 twoder 挙動）を
  UNRESOLVED_REAL_PKG_UNTESTED として過小主張せず明示
```

---

## 🟠 新チェックポイント（submit 機構・要対応）— contract マーカー

`contract_seal.extract_contract`（`contract_seal.py:39-67`）は **明示マーカー必須**。

```
- skeleton        = <<<2DER:SKELETON>>> … <<<2DER:END>>>
- immutable_tests = <<<2DER:IMMUTABLE_TESTS>>> … <<<2DER:END>>>
- マーカーが無ければ None（契約無し）を返す / contract_seal.py:12,43-44
  → runner に skeleton/immutable_tests が渡らず 12/12 ゲートが発火しない
- 抽出は raw_input[sk_start:sk_end][1:]（マーカー直後の1文字=改行を除去）/ contract_seal.py:48-59
  → 囲む中身は生コードのみ。```python フェンス行を含めると、その行が bytes 一致の
     固定区間になり artifact 側に無く SKELETON_VIOLATION / generate_via_runner.py:204
- 順序は SK→END→IT→END（find(END, sk_start) が先頭 END を拾う）/ contract_seal.py:48-56
```

**事実:** 貼られた v0.4 本文にこのマーカーは 1 つも無い。
submit 時にラッパが §2 骨格（フェンス除外・`<<<FILL>>>` は残す）と §3 テストを生コードで囲む運用なら可。本文をそのまま提出すると契約が座らない。

---

## claim ceiling

```
- Finding 1/2 の解消はコード読取で確定（環境非依存）
- S1–S10 のロジックは健全（S3 checked>=5 / S7 陰性対照 / S8 自己ホスティング / S10 AST は空振りしない）
- 未検査: contract マーカーが submit ラッパで実挿入されるか（運用側の事実。
  CC は raw_input 生成を担わない = 監査範囲外）
- ここが埋まれば v0.4 は submit 可能。CC は「マーカーが無い」という事実のみ渡す。挿入はしない
```
