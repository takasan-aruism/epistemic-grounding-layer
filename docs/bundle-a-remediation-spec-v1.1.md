# 束A 修復仕様 — bridge/minter(JREV-0010r 対応)v1.1

status: 仕様確定案(FIX-LIFT-JREV0010 の Taka 捺印後に packet 化して Qwen へ)。
v1.0 → v1.1: GPT 補強 A(CORRECTION 権限根)・B(apply 原子性 + T-8)を反映。
GPT 判定: READY_FOR_TAKA_FIX_LIFT_DECISION / NOT_AUTHORIZED_FOR_EXECUTION。
date: 2026-07-21 / 起草: Claude Web
対象: twoder patch_bridge.py(5ca50050)/ bridge_reconciler.py(41c404ca)/
      bridge_minter.py(d77c5530)
根拠: JREV-0010-F1(GPT)/ EM-1..3(GPT)/ 設計側裁定 束A / DE-0479(遡及確認)
実装者: Qwen(workcell)。Claude Code = 照合適用・実測・監査のみ(CC-0)。
全差分は diff → CONTENT_SEAL → sha 束縛。

---

## R1: repo identity binding(F1 / EM-4 / EM-3(a))

```
R1-1  PATCH_APPLICATION payload に repo_identity(canonical 名)と
      repo_realpath を必須化する。欠落 event は以後の対象計算に含めず、
      検出時は fail-closed(reconcile 不能 → mint 拒否)。
R1-2  reconcile() は要求 repo の identity で PA events を filter する。
      filter は realpath 照合(文字列 alias を弾く)。
R1-3  RECONCILIATION_* proof に repo_identity / repo_realpath /
      checked_head / checked_ledger_offset / proof_issuance_identity を
      必須化する。
R1-4  minter は request・PA events・proof の三者 repo binding を検証し、
      不一致・欠落は MintRefused。
R1-5  既存 event(DE-0438 の PA 3件)への遡及: 原 event は改変しない。
      repo identity を付す CORRECTION 型の後続 event で補完し、DE-0479 の
      代理指標(base_commit ancestry / fingerprint 一致)を根拠として引く。
R1-6  CORRECTION の権限根(GPT 補強A): CORRECTION event は
      correction 対象 record_hash / correction authority / evidence refs /
      repo_identity / repo_realpath を sealed field として持つ。
      **元 event を書いた通常 writer は、単独で自 event の repo identity
      correction を成立させられない**(authority は Taka 裁定参照または
      独立検証済み evidence を要する)。後付け帰属偽装の遮断。
```

## R2: apply 時再検査(EM-1 = 選択肢 A)【Taka veto 対象の実装】

```
R2-1  _apply_to_working / _restore_preimage は書込み直前に SoR から
      revocation / expiry / consumption を再検査する(mint 時検査に加えて)。
      revoked / expired / consumed → 書込み拒否 + 拒否 event 記帳。
R2-2  再検査の SoR 読取は reconciler と同じ read-only 制約下(AST ゲート
      対象に含める)。
R2-3  原子性(GPT 補強B・TOCTOU 遮断): 検査→apply の間隙を塞ぐため、
      **方式A を採用**: apply は書込みに先立ち token の consumption claim を
      SoR へ原子的に記帳(既存の fcntl 直列化 append を使用)し、claim 成立後
      にのみ書込む。claim 済み token での二重 apply は claim 段で拒否。
      apply 失敗時も claim は残す(fail-closed: 中途失敗 token は再使用不可、
      Taka 再 mint 経路へ。取り残しは安全側)。
```

## R3: clock fail-closed(EM-2)

```
R3-1  now_ts を必須化。minter 内部で clock を取得し、取得失敗は
      MintRefused(fail-closed)。
R3-2  時刻表現は ISO8601 UTC 固定・strict parse。文字列比較を廃止し
      parse 済み比較へ。malformed timestamp は refuse。
R3-3  R2 の apply 時再検査にも同一 clock 規律を適用。
```

## R4: 語彙・設計文言の訂正(EM-3(b))

```
R4-1  設計文書の freshness 主張を NO_RECORDED_APPLY_AFTER_LAST_BALANCED_
      PROOF へ縮小(RECONCILER_DEMONSTRABLY_LIVE は撤回)。
R4-2  真の liveness(heartbeat + bounded validity)は別チケット
      (EM-2 解消後・clock 基盤前提)。
```

## 受け入れ試験(不変・packet の immutable tests に含める)

```
T-1  cross-repo 汚染: 対象 repo dirty + 同名同 fingerprint の別 repo PA
     → reconcile IMBALANCED / mint 拒否(JREV-0010-F1 の再現 → BLOCKED)。
T-2  missing-repo-id PA → 対象計算から除外 + fail-closed。
T-3  alias-repo-id(symlink / 相対 path / 大文字小文字)→ realpath 照合で
     不一致検出。
T-4  mint → revoke → 既存 token で apply → R2-1 が拒否。
T-5  now_ts 欠落 / clock 取得失敗 / malformed timestamp → MintRefused。
T-6  proof の repo binding 欠落 / request と不一致 → MintRefused。
T-7  回帰: A1..A6 全 BLOCKED / §4 gate 11 injections 0 SLIPPED /
     reconciler oracle 7 / minter oracle 18 無退行。
T-8  同一 token で並行 apply 2件(GPT 補強B)→ 最大1件のみ書込成功、
     他方は consumption claim 段で拒否。
T-9  CORRECTION 偽装(GPT 補強A): 通常 writer が単独で自 event の
     repo identity CORRECTION を試行 → authority 欠如で reject。
```

## 再戦(JREV-0010r・DE-0426 準拠)

修復が導入する概念(repo binding / apply 時再検査 / clock 規律)を再利用
した novel attack を独立 attacker(local agent)が実行し、GPT が裁定。
候補面: repo_identity の CORRECTION event 偽装 / 再検査の SoR 読取自体への
汚染 / clock source の操作。terminal = T-1..7 PASS + 再戦 0 BREACH +
JREV-0010r CLOSE → FIX-LIFT auto-refreeze。
