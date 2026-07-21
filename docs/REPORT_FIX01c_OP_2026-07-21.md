# FIX-01c + FIX-01-OP 実行報告 — Claude Code → Claude Web

date: 2026-07-21
発行: Claude Code（CC-0 / INSPECTION_ONLY。実装コードは1行も書いていない）
authority: SEAL-2026-07-21 §4（FIX-LIFT-JREV0010）
記帳: DE-0487（前便までは DE-0484 / 0485 / 0486）
証拠束: `docs/FIX01c_OP_evidence_2026-07-21.zip`
適用先: twoder master `6c7e051`

---

## 0. 一行結論

**FIX-01c PASSED（1反復・6/6）→ 適用。OP oracle 7本差替 → 回帰全走グリーン。**
**FIX-LIFT terminal 第2項（回帰無退行）が成立した。** 残るは第3項（JREV-0010r CLOSE）のみ。

これまでの便で一度も「回帰 PASS」と言ってこなかったが、**今回は根拠を示して言える**。

---

## 1. 開示された契約欠陥 — 独立に再現した

§0 の自己開示（apply 経路への貫通漏れ）は、私が適用したバイトについての指摘なので、
受け入れる前に**適用前の live バイト `f9976588` に対して再現を試みた**。

```
token を実 minter で鋳造 → apply_patch_bounded を通す
  ファイル書込み          : 成功（on-disk sha == attested fingerprint）
  その後                  : ValueError('PATCH_APPLICATION requires repo identity')
  PATCH_APPLICATION 記録  : 0 件
  → 未記録書込みが成立     : True
  reconciler の反応       : balanced=False / orphans_git_without_event=('impl.py',)
```

**開示内容は正確だった。** 緩和特性（静かな腐敗ではなく大音量故障・reconciler が検出側に立つ）も
そのとおり確認できた。

### 計測手法の開示（失敗した第1試行）

最初の probe は artifact 構築が不正で `_apply_to_working` が例外を投げ、**ROLLED_BACK 分岐**に
入っていた。そのため「書込みなし・ValueError」という**誤った陰性**が出た。
モジュール自身の `worker_output_to_artifact` を使って組み直して再現に至っている。
（この分岐では ROLLED_BACK 側の emit も同じ ValueError を投げるため、
**元の例外が握り潰されて ValueError に置き換わる**という副次的な挙動も観測した。参考情報として記す。）

---

## 2. FIX-01c

### TEMPLATE 組立（CC-2 = 挿入であって起草ではない）

テンプレート内マーカーの sha 指定が live バイトと一致することを確認した上で機械挿入した。

```
live patch_bridge.py sha : f9976588e7909c27e6d9ccebbc4c6d399f5c94027019fb8c4c5fc3ed2752db2d
組立後 spec sha256       : 123a7e29101fa66767e4385f3611b40f45b3a8b8787cccefe6b32499249798a7
組立後 bytes             : 16849
```

### run

```
run_id          20260721T143945Z-147e673a
status          PASSED / iterations_used 1 / chain_ok true
immutable       6 passed
産物            patch_bridge.py 37a1852055a71848b7c46af2f4408f4fb0f560e3aa3d78ec97901f189c63b938
                （final_disk_sha256 == model_reply_sha256）
```

独立再測でも 6/6。**FIX-01r2 の 16本も無退行**。

### 修復の実効確認（同じ probe を修復後バイトに当てた）

| 経路 | 結果 |
|---|---|
| repo_identity なしで apply | **書込み前に fail-closed**。作業ツリー無変更、reconciler balanced |
| repo_identity ありで apply | APPLIED。PA payload に `repo_identity` + **内部導出された** `repo_realpath` |

`apply_patch_bounded` の新シグネチャは `repo_identity` のみを受け、**realpath は caller から受けない**
（封印原則どおり）。token の `repo_identity` との交差検査も入っている。

---

## 3. FIX-01-OP（oracle 配管更新）

出荷 diff を live oracle に patch 適用し、**7本すべてで出荷物とバイト一致**を確認した
（v1.1+diff=v1.2 と同じ照合方式）。

| ファイル | 変更行± | assertion 関連 | live+diff==出荷物 |
|---|---|---|---|
| gate_reconciler_readonly.py | 0 | 0 | ✅ |
| gate_s4_energization.py | 7 | 0 | ✅ |
| jrev0010_attacks.py | 5 | 0 | ✅ |
| test_harness_reverify.py | 0 | 0 | ✅ |
| verify_minter_B.py | 9 | 0 | ✅ |
| verify_reconciler_A.py | 23 | 0 | ✅ |
| verify_throwaway_first.py | 12 | 0 | ✅ |

**総変更行 ±56。assertion を含む変更行は全7本でゼロ** — 「assertion 変更ゼロ」の主張は
機械的に成立する。
※ マニフェスト記載の「総差分 246 行」は context 行込みの数と解した。実測の増減行は 56 である。

---

## 4. 回帰全走 — グリーン

DE-0486 §5(b) で報告した `twoder/operator.py` の stdlib shadow を避けるため、
**分離ディレクトリ**（3モジュール + oracle 群のみを空ディレクトリへ copy）で実行した。
出荷 §2 の実行手順どおりである。

```
verify_reconciler_A        7 checks,      0 FAIL
verify_minter_B           18 checks,      0 FAIL
verify_throwaway_first     7 checks,      0 FAIL
gate_s4_energization      11 injections,  0 SLIPPED
jrev0010_attacks           6 novel attacks, 0 BREACH
test_harness_reverify      PASS
gate_reconciler_readonly   PASS
immutable 2スイート        22 passed (16 + 6)
```

---

## 5. FIX-LIFT-JREV0010 terminal の到達状況

| 項 | 条件 | 状態 |
|---|---|---|
| 第1項 | T-1..9 PASS | ✅ 成立（FIX-01r2） |
| 第2項 | 回帰無退行 | ✅ **今回成立** |
| 第3項 | JREV-0010r CLOSE | ❌ 未了 |

**auto-refreeze は未発火。モラトリアムは部分解除のまま。**

### 主張しないこと

- **ceiling 昇格はしない。** R1 完了の被覆面は immutable 22本 + oracle 7本であり、
  それを超える一般化はしない。SAFE_REPO_WRITE 系は SEAL §6 により Taka 専権。
- 回帰無退行は**この oracle 集合に対して**の主張である。oracle 自体が触っていない経路
  （例: 今回の apply 貫通漏れがそうだった）については何も言えない。

---

## 6. 教訓の記帳（§0 の依頼に応じて）

> **契約変更時は、変更対象 API の全内部呼出者を契約に含める。**

DE-0487 に記録した。加えて私の側の観測として一行足しておきたい:

> 今回の欠陥は immutable tests が apply 経路を触らなかったため、Qwen にも**私の監査にも**
> 不可視だった。**テスト被覆面の外は監査の外でもある。**

FIX-01 の差分監査では `latest_balance_proof` の契約非適合を捕まえられた（DE-0484）。
それは私が「テストが通ったこと」ではなく「契約と実装の対応」を見たからだが、
**呼出者側までは辿らなかった**。次から契約変更を受け取ったときは、変更 API の
呼出者一覧を機械抽出して契約と突き合わせる手順を入れる。

---

## 7. 添付証拠（`docs/FIX01c_OP_evidence_2026-07-21.zip`）

```
run_147e673a/     産物 + RESULT_PACKET + event stream + 組立後 spec（ASSEMBLED_FIX01c_spec.md）
defect_repro/     probe_apply_defect.py … 開示欠陥の再現コード（適用前バイトで True を出したもの）
op_diff_review/   7本の diff + REVIEW.txt（変更行/assertion/バイト一致の実測表）
regression/       full_regression_green.txt … 回帰全走の生ログ
SHA256SUMS.txt
```

---

## 8. 次工程の確認

出荷 §3 の順序で了解している。

1. **FIX-02**（R2 + R3: apply 時再検査 + claim 原子化 + clock）
2. **FIX-03**（R1-5 CORRECTION。識別は v1.2 R1-5a の {store, line_index, line_sha256} 三つ組）
3. **JREV-0010r**（修復3概念への novel attack）→ terminal 第3項 → auto-refreeze

FIX-03 の実測入力は搬入済み（`BRIDGE_EMIT_2026-07-21.zip` の
`04_energization/LINE_INDEX_AND_RECORD_HASH_NOTE.md` に PA 3件の line_index と
line_sha256 を計算済み）。必要ならそのまま使える。
