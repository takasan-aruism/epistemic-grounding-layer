# CC 起草+投入前検証 — SEAM_PKG_MIRROR v0.4 raw_input（マーカー封入）

- 作成: Claude Code（CC-α 起草／2026-07-23 の役割変更後）/ 日付: 2026-07-23
- 対象: `egl/docs/pkg_mirror_v0_4_raw.txt`（submit へ渡す raw_input）
- 由来: 監査済み v0.4 本文（paste-cache `7541c7f74197cdfe.txt` = CLAUDE_WEB 起草、`CC_AUDIT_..._PKG_MIRROR_v0_4.md` で Finding 1/2 解消確認済み）
- 位置づけ: ANCHOR ★3(A) 残ブロッカー=「contract マーカー未挿入（`contract_seal.py:43-44`）」の解消。**move (1)。**
- 生成物 sha256: `edaafe352fa791ea9d1ddd1af63d8a97ac5f0bff1fc168c85d206ba23767fb67`（8,854 bytes）
- 再生成器: `scratchpad/assemble_pkg_mirror_raw.py`（決定論。手写しでなくプログラム抽出）

---

## 何をしたか（起票側の付加知能は 0）

監査済み v0.4 本文の §2 骨格ブロックと §3 不変テストブロックを、```python フェンスを**除外**して
生コードのまま contract マーカーで囲み、BUILD_CAPABILITY ヘッダを前置して 1 本の raw_input にした。
テスト論理・骨格の 1 バイトも変えていない（下記の byte 一致検証で担保）。

```
[header: BUILD_CAPABILITY 宣言 4 行]
<<<2DER:SKELETON>>>        (line 7)
  <§2 骨格・生コード・<<<FILL>>> ×4 保持>
<<<2DER:END>>>            (line 77)
<<<2DER:IMMUTABLE_TESTS>>> (line 79)
  <§3 テスト S1–S10・生コード>
<<<2DER:END>>>            (line 236)
```

## 決定論検証（REAL コードで実行・環境非依存）

| # | 検査 | 結果 |
|---|---|---|
| V1 | `contract_seal.extract_contract(raw)` が封印を返す（`sealed_by="contract_seal"`） | ✅ |
| V2 | 封印 skeleton == v0.4 §2 ブロック（+末尾改行のみ。他バイト差 0）| ✅ `[:-1]` 一致 |
| V3 | 封印 immutable_tests == v0.4 §3 ブロック（同上）| ✅ |
| V4 | `_skeleton_fixed_segments` = 4 塊 / FILL 分割 = 4（挿入で塊が増えていない）| ✅ |
| V5 | raw 全体の `<<<FILL>>>` は 4 個、**すべて SKELETON マーカー内**（ヘッダに literal FILL 無し）| ✅ |
| V6 | 不変テストが `twoder` を static import しない（death#7 hermetic / §4）| ✅ |
| V7 | 不変テストが `pytest.skip` を使わない（族A 回避 / §4）| ✅ |
| V8 | S1–S10 の 10 関数が存在・全文 AST parse 可 | ✅ |
| V9 | マーカー順 SK→END→IT→END（`find(END, sk_start)` が先頭 END を拾う）で正しく分離 | ✅（V1 が含意）|

## routing 事前検査（決定論・台帳無変更・:8005 不使用）

| 検査 | 結果 |
|---|---|
| `request_type.classify_request_type` | **BUILD_CAPABILITY** → `submit.py:368` の契約封印枝に入る |
| `research_signal.detect` acquisition_needed | False → 調査迂回しない |
| `failure_memory.check` dead-approach BLOCK | none |
| `admission_request.detect` | False → DW を飛ばさない |
| ⇒ submit 時 `extract_contract`→`create_task(contract=…)` が座る | **True** |

（`references_prior_work=True` は出るが RESUME_PRIOR 枝でしか使われないため無害。BUILD_CAPABILITY は常に本 raw のハッシュ鍵で**新規**タスクを立てる＝DE-0156/0161。）

## claim ceiling（言えること / 言えないこと）

- **言える:** raw_input はマーカー封入され、REAL `contract_seal`/`generate_via_runner` で契約が座り、
  骨格の固定 4 塊と不変テスト 10 本が監査済み本文と**バイト一致**（末尾改行を除き差分 0）。routing は BUILD_CAPABILITY。
- **言えない（未実行）:**
  1. **submit の実走**（DS/RRI/EGL/DW への副作用を伴う。loop/人間所有の工程。CC は raw を作るまで）。
  2. **12/12 の実測**。不変テストを reference 実装に対して実行（緑）／故意破壊に対して実行（赤）で
     族A（空振り）を最終排除する検査は**未実施**。※テスト**論理**は v0.4 監査で健全確認済み・本 raw で
     バイト不変。実行証明は submit 時の runner 12/12 が担う（S3 checked>=5・S7 陰性対照・S8 自己ホスティングが
     vacuous 合格を構造的に阻む設計）。
  3. `generate_via_runner` への**配線**は §5 で範囲外（プローブ gate3 が測る）。本 raw の DONE は BUILT。

## 次工程（ANCHOR ★3(A)）

- move (2): 本 raw を `python3 -m twoder.submit "$(cat egl/docs/pkg_mirror_v0_4_raw.txt)"` で投入 → runner 12/12 で death#6/#7。
  **副作用（台帳追記）＋ live Qwen(:8005) を伴うため Taka 確認の上で実行。**
- move (3): `CONFORMANCE_PROBE_v0_5` submit → 走行。
- move (4): 実走痕跡があって DONE。
