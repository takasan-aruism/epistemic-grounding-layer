# ★STOP — 設計/監査 → IMPL（写: MGR / Taka）: **Build 9A を止める。依頼が planner の設計に拒否される。私の予想は「当たり」だが理由が間違っていた**

- `BUILD_ROLE: 参照`（**`CC_DESIGN_2026-07-27_BUILD9A_SPEC_SUBMIT_WIRING_REQUEST.md` v1.0 の §1 依頼文と §3 区分を訂正する。着手前なら投入しないこと**）
- **宛: IMPL（coder）** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=STOP
- **運用方針 確認済（版: v1.5）**
- 契機: **Taka 直接指摘**「Worker内の処理はかなり厳格な内部システムが構築済み、DW側は問題ないけど設計はまだClaude担当になると思う。ちゃんと調べてね」

---

## 0. IMPL への指示（先に・短く）
1. **未投入なら投入しない。**
2. **既に投入していたら、投入したこと自体は問題ない。ただし結果を §2 の4区分に当てはめないこと。** **区分表は誤っている。§3 の新しい区分で書くこと。**
3. **本番コードを手で直さない**（従来どおり）。

---

## 1. ★調べた結果 — worker は production repo に書けない。偶然ではなく設計である【監査:CC-α・コード構造】

```
twoder/build_planner.py:59
  PROD_REPO_ROOTS = ("/home/takasan/egl", "/home/takasan/ds", "/home/takasan/rri",
                     "/home/takasan/dev-workcell", "/home/takasan/twoder")
twoder/build_planner.py:254-255   （決定論バリデーション・LLM 判断ではない）
  elif any(ws.rstrip("/") == root or ws.startswith(root + "/") for root in PROD_REPO_ROOTS):
      reasons.append("workspace/scope: target_workspace %r is an existing project repo (forbidden)" % ws)
twoder/build_planner.py:38  コメント逐語
  "target_workspace",  # str: a temp/sandbox workspace (NOT a production repo)
```

**さらに二重・三重に閉じている:**
```
twoder/qwen_worker.py:32-56  _safe_target_path()
  絶対パス・`..` traversal・symlink 脱出を REJECT。**workspace 相対しか書けない**
twoder/live_worker_scaffold.py:21  _MUST_BE_TRUE
  ("workspace_isolated", "process_kill_cleanup", "host_filesystem_unreachable",
   "production_credentials_unreachable", "secrets_unreachable", "network_egress_default_deny")
  → **host_filesystem_unreachable が True 必須**
twoder/build_planner.py:23  逐語
  "On any rejection the actor records NOTHING and reports recorded=False, so dispatch falls back to the
   Claude barrier (fail-closed): a bad Qwen plan can never advance the task."
```

**∴ Taka の指摘は正しい。DW/worker 側は厳格に閉じている。** **問題は DW ではない。**

**∴ 私が §1 で投入させようとした依頼「`submit.py` の routing に分岐を1つ足せ」は、`/home/takasan/twoder` を触る依頼である。**
**∴ この依頼は planner の決定論バリデーションで拒否される。** **拒否されたら `recorded=False` で Claude barrier に落ちる。**

### 1-1. なお決定論テンプレートも本件を扱わない
`dev-workcell/dw/plan_template.py` は **「source-grounded bounded reproduction candidate」専用**（逐語: `True ONLY for a source-grounded bounded read-only-first reproduction candidate`）。**配線依頼は対象外。** ∴ `build_planner` に落ち、そこで拒否される。

---

## 2. ★私の誤り（今回は「当たったが理由が間違っていた」型）
**Build 9A SPEC §2 で私はこう予想した:**
> **`twoder/submit.py` に実際に配線が入るか → ★入らない（F1/F2）。生成物は一時 workspace に留まると予想する**

**予想は当たる。しかし理由が違う。**
| 私が書いた理由 | 実際 |
|---|---|
| 「一時 workspace に**留まる可能性が高い**」（＝観測して確かめるべき**未知**として書いた） | **決定論バリデーションで拒否される。** **観測するまでもなく、コードに書いてある** |

**∴ 私は「調べれば分かること」を「投入して確かめること」にしていた。**
**∴ 本日7回目の同型の誤り**（ソースを読まずに／読んだだけで／確かめずに前提を置いた）。**Taka に指摘されるまで気づかなかった。**

**★これは「予想を先に固定する」作法の穴でもある**: **予想を固定する前に、決定論で確定できることを確定しておかないと、予想が当たっても何も学べない。** **当たった理由が違えば、次の一手を間違える。**

---

## 3. ★区分表を訂正する（本件の核・SPEC §3 を差し替え）

**旧 §3 の4区分には、実際に起きる結果が入っていない。** 次に差し替える:

| 区分 | 意味 | 次の欠落はどこか |
|---|---|---|
| **★(0) 設計どおり拒否された** | planner が `target_workspace が production repo` として REJECT し、`recorded=False` で Claude barrier に落ちた | **★欠落ではない。正しい動作である。** **planner を直す方向へ行かないこと** |
| (1) 作れなかった | (0) 以外の理由で PLAN が出ない／依頼と無関係なものが出た | 生成の限界 |
| (2) 作れたが置けなかった | sandbox 内に成果物は出たが production へ届かない | **★これも欠落ではない可能性が高い。§4 参照** |
| (3) 置けたが動かなかった | — | 品質の限界 |
| (4) 通った | — | — |

**★(0) を (1) に分類すると、「planner が弱い」と読まれ、planner を緩める方向へ行く。** **それは境界を壊す方向である。** **絶対に混ぜないこと。**

---

## 4. ★MGR の枠組みを1点だけ差し戻す — 「配置が未実装」は誤読になる

**MGR は `CC_MGR_2026-07-27_BUILD9_C_APPROVED.md` §3 でこう書いた:**
> 「**『置けなかった』なら、Taka が Claude に残した役割『外注で生成、配置するまで』の配置が未実装だということになる。次の欠落はそこである。**」

**【設計:CC-α】これは誤読になる。** **Taka の逐語を読み直す:**
> 「**あるとしてもプログラムを外注で生成、配置するまで**」

**＝ 生成と配置は、Taka が Claude に残した役割である。** **2DER に配置させる話ではない。**
**∴ worker が production に置けないのは、未実装の欠落ではなく、役割分担そのものである。**
**∴ Taka の「設計はまだ Claude 担当になると思う」も同じことを言っている。**

**∴ 正しい役割の切り方:**
```
Claude（市民・外）  : 設計する / 依頼する / 受け取った成果物を配置する
2DER（中）          : sandbox 内で生成し、テストし、判定する（host filesystem には届かない）
```
**∴「2DER が自分自身を配線する」は、現在の設計では成立しない。** **成立させるべきかは、Taka の判断である**（§6）。

---

## 5. ★では Build 9A の問いをどう変えるか（提案・裁定を待つ）

**旧: 「`submit.py` を配線せよ」→ 拒否されることが分かっている。投げる価値が下がった。**

**新（案）: 依頼を sandbox で完結する形に切り直す。**
> **`twoder/ids.py::resolve` を呼ぶ薄いアダプタ（question + id → ANSWERED / NOT_FOUND / NOT_ANSWERABLE の3状態を返す純関数）を、sandbox workspace 内に1ファイルで作り、テストも書け。**
> **production repo は触らないこと。配置は依頼者が行う。**

- **これなら planner の受理条件を満たす**（`target_workspace` が sandbox・`files_expected` 1本・`test_plan` あり・`prohibited_actions` に production を書ける）。
- **経路の実証は保たれる**: 「Claude が外から依頼し、2DER が生成する」は測れる。
- **配置（`submit.py` への差し込み）は Claude 側の作業として分離する。** **これは代替ではなく、設計上の役割である**（§4）。
- **★ただし1つ未確認**: **sandbox は `host_filesystem_unreachable` である。** **∴ worker は `twoder/ids.py` を読めない可能性が高い。** **∴ 依頼には `ids.resolve` の呼び出し規約（引数と戻り値）を仕様として書いて渡す必要がある。** **これが Taka の言う「設計はまだ Claude 担当」の具体形である。**

---

## 6. Taka の判断が要るもの（MGR 経由）
1. **§5 の切り直しでよいか。** それとも **Build 9A を予定どおり投げて「(0) 設計どおり拒否された」を記録として残すか**（**拒否されることは分かっているが、記録に残す価値はある**）。**私の推奨は §5 の切り直しである。** 拒否の記録は本文書のコード引用で足りる。
2. **「2DER が production repo を書ける経路」を将来作るか。** **今は作らない方に倒すべきと考える**（作れば sandbox 隔離が意味を失う）。**Taka の境界設定と正面から関わるので、私が決めない。**

---

## 7. 記録（消さない）
- **本件は Taka の「ちゃんと調べてね」で見つかった。** **指摘が無ければ、私は拒否されると分かっている依頼を投げ、結果を「経路の限界」と誤って記録していた。**
- **予想を先に固定する作法に、前段を足す**: **予想する前に、決定論で確定できることを確定する。**
- **`ids.resolve()` は依然として実行していない**（v1.5）。

---
*CC-α STOP。Taka 指摘「DW側は問題ない・設計はまだClaude担当・ちゃんと調べてね」を受けて調査。★worker は production repo に書けない——`build_planner.PROD_REPO_ROOTS` に `/home/takasan/twoder` が入り :254 で決定論的に REJECT、`qwen_worker._safe_target_path` が絶対パス/traversal/symlink を拒否、sandbox は `host_filesystem_unreachable` 必須、拒否時は `recorded=False` で Claude barrier に fail-closed。偶然ではなく設計。∴ Build 9A の依頼文（submit.py に分岐を足せ）は拒否されることがコードで確定しており、投入して確かめる対象ではなかった。★私の予想「配線は入らない」は当たるが理由が違う（「一時workspaceに留まる可能性」ではなく「決定論バリデーションによる拒否」）＝本日7回目の同型の誤りで、Taka の指摘まで気づかなかった。作法に前段を足す=予想を固定する前に決定論で確定できることを確定する。★区分表を訂正: (0) 設計どおり拒否された を新設——(1) 生成の限界 に混ぜると planner を緩める方向に行き、境界を壊す。★MGR の「置けなかったら配置が未実装＝次の欠落」を差し戻す: Taka 逐語「プログラムを外注で生成、配置するまで」は生成と配置が Claude の役割という意味であり、worker が production に置けないのは欠落でなく役割分担。∴「2DER が自分自身を配線する」は現設計では成立しない。★提案=依頼を sandbox 完結の薄いアダプタ生成に切り直す（planner の受理条件を満たす・経路の実証は保たれる・配置は Claude 側）。ただし sandbox は host filesystem に届かないので `ids.resolve` の呼び出し規約を仕様として渡す必要がある＝これが「設計はまだClaude担当」の具体形。Taka 判断=切り直すか拒否記録を取るか／将来 production を書ける経路を作るか（私は作らない方を推す）。*
