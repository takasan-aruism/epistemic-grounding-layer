# 設計担当 → 実装担当: commit 受領・CONFORMANCE_PROBE 起草着手（handoff signal・返信）

- 発: 設計担当 CC-α（`egl/docs` を保守する側）/ 2026-07-23
- 宛: 実装インスタンス（Monitor `b0718vzrg`）
- 対応 handoff: `CC_IMPL_2026-07-23_PKG_MIRROR_COMMITTED.md`

## 受領（deadlock を解く返信）

- pkg_mirror commit `c1ffef5` を**受領**。anchor ★3(A) を **BUILT+committed** に反映済み（stale 解消）。
- ボールは設計担当（私）にあることを確認。**CONFORMANCE_PROBE の起草に着手した。**

## いま起草しているもの（＝実装待機は「両者待ちで固まっている」のではなく「handoff 進行中」）

`SPEC_CONFORMANCE_PROBE_v0_4` を起草中。正本＝Web 起草 v0.3（適合プローブ）。v0.4 で解く点:

1. **新フロー整合**: v0.3 は「実装=Qwen / 投入=submit / CC=監査のみ」前提。新フロー（§1-1: 実装=実装インスタンスが working tree 直接、commit=Taka）へ FLOW NOTE で置換。
2. **前提工程更新**: v0.3 は `SEAM_PKG_MIRROR_v0_2` 7/7 前提 → 実際は **v0.4 12/12 committed `c1ffef5`**。gate3 は実装済み `twoder/seam/pkg_mirror.py` を使う。
3. **唯一の実 blocker=`probe_env` fixture 未同梱を解消**（CC 監査 `CC_AUDIT_2026-07-23_SEAM_v0_2_PROBE_v0_3.md` の E）。§5 テスト（T5/T6/T7/T8/T9/T10）が `probe_env`/`ladder_symbols` に依存するが未定義＝collection error。→ 骨格に `run(inject=None)` / `ladder_symbols()` / CLI を**固定 API**として昇格し、`probe_env` fixture（conftest）を発注側同梱する。
4. **gate3 の既知の罠を明記**: `twoder/operator.py` が stdlib `operator` を shadow。実 twoder 複製時 `MIRROR_EXCLUDE` か PYTHONPATH 順序で対処（両監査で記録済み）。

## 段取り（正常フロー）

1. 私が gate 境界（`generate_via_runner` が各 callee に渡す actual ⇔ `authority`/`pkg_mirror`/`verify_skeleton_preserved` が期待する expected）を精査。
2. `SPEC_CONFORMANCE_PROBE_v0_4.md` を `egl/docs` へ投下（＝あなたの Monitor が拾う signal）。
3. あなたが working tree に実装（骨格末尾 FILL＝各 probe 実装/FaultInjection/ladder/CLI/BREAKAGE_LIST 書き出し）→ §5 の T1–T12 green。
4. 私が CONFORMANCE 版の設計整合監査（pkg_mirror と同型の決定論ハーネス）で CONSISTENT を確定。
5. commit=Taka（人間の扉2枚目）。

**投下まで待機で正常です。** 投下 file 名は `SPEC_CONFORMANCE_PROBE_v0_4.md`。それ以外の私の docs（audit/anchor/本 signal）は実装対象ではありません。

---

## ✅ 投下完了（追記 2026-07-23）

`SPEC_CONFORMANCE_PROBE_v0_4.md` を **投下しました**。決定論検証 ALL OK:
- §4 骨格: `<<<FILL>>>`×4（import後 / `ladder_symbols`本体 / `run`本体 / 末尾）。v0.3 の `run_ladder`/`bind_real`/`source_ref`/`GateOutcome`/`_record` はバイト温存、固定 API `ladder_symbols()`/`run(inject=None)` を追加（fixture が呼ぶ）。FILL=pass で構文健全。
- §5: 不変テスト T1–T12 温存 ＋ **conftest（`probe_env` fixture）同梱**（v0.3 の E＝collection error を解消）。
- 新フロー整合 / 前提=pkg_mirror v0.4 `c1ffef5` / gate3 に `operator.py` shadow 罠を明記。

**実装対象 = `twoder/probe/conformance_probe.py`（§4 骨格 FILL 実装）＋ `tests/test_conformance_probe.py`・`tests/conftest.py`（§5 をそのまま配置）。** §5 T1–T12 green で BUILT。私が CONFORMANCE 版の設計整合監査（実装配置に合わせて用意）で CONSISTENT を確定します。commit=Taka。

