# CC 設計整合監査 — SEAM_PKG_MIRROR v0.4 実装

- 監査者: Claude Code（CC-α・設計整合担当）/ 日付: 2026-07-23
- 対象実装: `twoder/seam/pkg_mirror.py`（実装インスタンス投下・19:01・158行）＋ `seam/__init__.py`（空）
- 正本（設計）: `egl/docs/SPEC_PKG_MIRROR_v0_4.md`（§2 骨格 / §3 不変テスト）
- 監査ハーネス: `egl/docs/audit_pkg_mirror.py`（決定論・セルフテスト済＝族A回避を実証）
- **verdict: CONSISTENT**（実装が設計を反映。齟齬なし）

## 監査結果

| チェック | 基準 | 結果 |
|---|---|---|
| C1 骨格保存 | §2 骨格の `<<<FILL>>>` 以外の固定区間が **bytes 一致**で保存 | green |
| C2 不変テスト | §3 を impl に対し**実行** 12/12（S1–S10、S6×3） | green（12 passed / 0.07s） |
| C3 import規律 | `twoder.*` 静的 import 無し（S10 同基準） | green |
| C4 重複定義禁止 | 骨格5シンボルが各1回（S9 同基準） | green |

## 監査の妥当性（族A回避＝空振りしないことの実証）

監査ハーネスは陰性対照でセルフテスト済（`scratchpad/selftest_audit.py`）。**本線は書かず**、使い捨てフィクスチャで各チェックが「壊れていたら赤」を出すことを確認:
- stub 実装 → C2 **RED**（passed=3/failed=9＝collection error でなく**走って弁別**）
- 骨格崩し（import1行削除）→ C1 **RED** ／ `twoder` import 混入 → C3 **RED** ／ シンボル重複 → C4 **RED**
- impl 不在 → `NOT_YET_IMPLEMENTED` ／ 構文途中 → `INCOMPLETE_SYNTAX`（誤検出しない）

## 実装の設計反映（目視確認）

- 規律1〜6 を実装。**「1バイトも書く前に」全 artifacts を事前検証**（族B: 例外を握り潰さず `MirrorHalt`）。
- `MIRROR_EXCLUDE` 除外 ／ traversal ／ overwrite ／ intermediate-is-file ／ write-into-source を halt。
- 中間 `__init__.py` を `created` に分離（sha256 突合対象外）。manifest は `sort_keys`。

## claim ceiling

- **言える:** §3 12/12 green ＋ 骨格保存 ＋ import 規律 ＝ SPEC 反映。**BUILT 到達**（SPEC §5: 本仕様の DONE は BUILT の意）。
- **言えない:**
  1. live 配線（`generate_via_runner` への接続）は SPEC §5 で範囲外 → `CONFORMANCE_PROBE` gate3 が測る。
  2. 実 `twoder` パッケージに対する複製挙動 → `UNRESOLVED_REAL_PKG_UNTESTED`（受入は代表性のある合成 synthpkg でのみ）。
- **観測外の発見（今の判定に影響せず・要記録）:** `twoder/operator.py` が **stdlib `operator` を shadow** する。
  `mirror_package` は `.py` を除外しない（ソースは複製する）ため、実 `twoder` を複製して PYTHONPATH へ入れると
  `operator.py` も複製され、cwd/PYTHONPATH 次第で stdlib import が壊れる罠。`CONFORMANCE_PROBE` gate3（実 twoder 複製）で
  顕在化しうる。**pkg_mirror の欠陥ではなく twoder リポジトリ構成の問題。** gate3 設計時に MIRROR_EXCLUDE か PYTHONPATH 順序で対処要検討。

## 次工程（ANCHOR ★3(A)）

- (2) 実装＋§3 green ＝ ✅ 達成（本監査）。
- 人間の扉2枚目: **commit=Taka**（現状 `?? seam/` untracked）。
- (3) `CONFORMANCE_PROBE`（live 配線・gate3）→ (4) 実走痕跡で DONE。
