# 2DER SESSION ANCHOR v2 — 毎セッション冒頭に貼る

- **これは何か:** 現在地の1枚。**履歴は書かない**（履歴は DE 台帳）。
- **サイズ上限: この文書は 1 画面。** §2 の各セルは「状態1行＋次の一手1行＋DE番号」まで。
  それ以上書きたくなったら DE を切って番号だけ置く。**v1 は 21KB まで肥大して読めなくなった。同じ轍を踏まない。**
- **序列: 台帳(DE) > 実測4部作 > MANAGER_ANCHOR > 本書 > 誰の記憶よりも。**
- **保存:** `egl/docs/2DER_SESSION_ANCHOR.md` / 更新はセッション末に依頼された側が行い Taka は保存のみ。
- last_updated: 2026-07-23 / 前版(21KB)を SUPERSEDE / CC 監査反映（death#5=HEAD反映済・#2=OPEN継続・骨格A1逆）＋ 仕様2本 pre-submit 監査（SEAM v0.2 / PROBE v0.3）

---

## §1. 不変の前提（変更は Taka 裁定のみ。再議論しない）

1. **【2026-07-23 Taka 裁定で変更】実装 = 本 Claude Code インスタンス**（旧 Qwen worker の役）。仕様起草 = 別の Claude Code インスタンス（旧 Claude Web の役）で、**spec を `egl/docs` に書き込む**。本インスタンスは `egl/docs` を能動監視し（本セッション: Monitor task b0718vzrg）、spec の投下/更新を検知したら **twoder working tree に実装し §3 immutable tests を green** にする。commit は人間の扉＝Taka。旧「CC=監査のみ／実装は Qwen／submit→runner」（下の §1-2・§1-4）は**本フローでは置換**。
2. **投入経路:** 開発依頼は仕様文書を raw_input として submit へ。手作りタスク禁止（DE-0301 が弾く）。
3. **人間の扉は2枚:** 判定(JUDGE) と 実 repo 書込み(トークン)。自動化しない。
4. **runner 方式が標準:** 骨格＋不変テストは発注側が固定。**worker は全文生成する**（穴埋め worker は存在しない=DE-0511）。
   生成後 `verify_skeleton_preserved` で骨格固定区間の bytes 一致を決定論検査（DE-0512）。**worker のテスト自作は違反。**
   骨格の固定/自由の分割は **`<<<FILL>>>` 行**が正本（`generate_via_runner.py:49`）。FILL 以外は全て固定＝bytes 一致対象。
5. **DONE の定義:** ROADMAP の `DONE` は **acceptance 記録のみ**を意味する（DE-0488）。live 接続は加算列 `wiring_state` を見る。
   2DER の作業完了は live 実行痕跡があって DONE、無ければ BUILT。**status の書き換えはしていない。**
6. **橋（FIX-01c 系譜）・JREV-0010r は凍結。** 再開判断は Taka のみ。

## §2. 現在地

| # | 作業 | 状態 | 次の一手 |
|---|---|---|---|
| 1 | producer 完成 | ✅ 完了（DE-0497 / twoder 85af03c） | — |
| 2 | walking skeleton 受入 | ✅ 完了（DE-0498） | — |
| ★3(A) | 恒久連結: GENERATE 段 = runner | 機構完備・§6 DONE 構造達成（DE-0513/0515）。SEAM v0.4（合成パッケージ検査で death#6/#7 を回避、Finding 1/2 解消＝CC監査 07-23, docs/CC_AUDIT_2026-07-23_PKG_MIRROR_v0_4.md）。**フロー変更（§1-1）: submit→Qwen を廃し CC 直接実装。contract マーカー blocker は旧 submit 経路のみの問題で本フローでは moot。** | ~~(1) 起草→投下~~=✅ **`egl/docs/SPEC_PKG_MIRROR_v0_4.md` 投下済**（CC-α、監査済み v0.4 を §2/§3 バイト不変で転記、FILL×4、submitマーカー無し）→ ~~(2) 実装+§3 green~~=✅ **`twoder/seam/pkg_mirror.py`(158行,19:01) 実装済・§3 12/12 green・CC設計整合監査=CONSISTENT**（骨格保存/import規律/重複定義すべてgreen, docs/CC_AUDIT_2026-07-23_PKG_MIRROR_IMPL_CONSISTENCY.md, 監査ハーネス=docs/audit_pkg_mirror.py・セルフテスト済）→ **BUILT+committed=commit `c1ffef5`**(Taka承認, twoder master ahead1・未push, handoff=docs/CC_IMPL_2026-07-23_PKG_MIRROR_COMMITTED.md) → (3) `CONFORMANCE_PROBE` ~~起草~~=✅ **`SPEC_CONFORMANCE_PROBE_v0_4.md` 投下済**(CC-α, v0.3土台+固定API `ladder_symbols`/`run`追加+`probe_env` fixture同梱でblocker E解消+新フロー整合, 決定論検証ALL OK, 実装対象=`twoder/probe/conformance_probe.py`+`tests/`)→ ~~実装+監査~~=✅ **`twoder/probe/conformance_probe.py`(366行,20:01)+tests/ 実装済・§5 T1–T12 10/10 green・CC設計整合監査=CONSISTENT**(骨格保存/verbatim/spy規律 all green, docs/CC_AUDIT_2026-07-23_CONFORMANCE_PROBE_IMPL_CONSISTENCY.md, ハーネス=docs/audit_conformance_probe.py)→ **BUILT到達。人間の扉2枚目=commit(Taka, 現状 `?? probe/` `?? tests/`)** → (4) ✅ `BREAKAGE_LIST` 走行済(9 records・TMPDIR回避・docs/BREAKAGE_LIST_2026-07-23.jsonl)=実走痕跡=**★3(A) 実質DONE**(commit=Taka は非同期の扉)。採取: **DIRECT破断1件=gate1_token 型不一致(死因#4)**→3Bへ。※観測: PROBE_SPEC=v0_3(CC-α起草ミス・軽微)・次版でまとめ。※`pkg_mirror_v0_4_raw.txt`/`CC_PRESUBMIT_…_RAW.md`は旧submit経路の産物＝実装対象でない。※観測外: `twoder/operator.py`が stdlib operatorをshadow=実twoder複製(gate3)で罠→MIRROR_EXCLUDEかPYTHONPATH順序で対処 |
| ★3(B) | token=authority 統合 | ✅**DONE(commit済 `38d1988` death#2/#4 closed・twoder ahead3未push)**。ts 完了(DE-0505) / provenance 完了(DE-0515)。✅**TOKEN-GATE-01 BUILT**(`approval_registry.py` 実装+§3 7/7+CC監査 CONSISTENT, docs/CC_AUDIT_2026-07-23_TOKEN_GATE_01_IMPL_CONSISTENCY.md)。破断採取済(DIRECT=gate1_token) | **配線=B採用（Taka裁定: §9 全経路統一）**。調査済(6経路とも dict中身未使用=validate/consume運搬のみ・低リスク／consume対=gate4/live_worker_runtime/operator/ab_harness/command_surface／発行源=issue_approval(dict)/mint_token(str))。設計=**アダプタ方式**: `approval_registry` に `validate_by_token`/`consume_by_token`(dict/str→approval_id抽出→台帳照合・中身は捨て族C両立)を足し6経路をそれ経由へ。発行側(issue_approval)は別途。probe gate1/gate7 も更新。→ ✅**配線実装+CC監査 CONSISTENT**(approval_registry アダプタ+6経路+probe, docs/CC_AUDIT_2026-07-23_TOKEN_WIRING_IMPL_CONSISTENCY.md)。再走行=**gate1_token green(死因#4消滅)**。**★重要所見: gate1b_ts DIRECT は計器欠陥(族E)**=probe `_gate1b_ts` が `grant_approval` 同一引数直呼び(SPEC は「実 mint 経路 mint_token を2回」を逸脱)。検証: mint_token(attempt違い)→approval_id相異=**death#2は実経路でCLOSED**。→ ✅**gate1b修正済(mint_token2回・SPEC v0.4§3準拠)・CC監査+再走行=DIRECT破断無し=★3(B) 実走痕跡DONE**(docs/CC_AUDIT_2026-07-23_GATE1B_FIX_AND_3B_DONE.md, BREAKAGE_LIST_rerun2)。死因#4消滅+#2 CLOSED。**残=commit(Taka)のみ** |
| 4 | SPR 抽出 | 仕様済・保留 | Taka 起動指示待ち |
| 5 | 台帳の家事（機械処分18／IDLE 8／DISPOSE 16内訳） | 未・裁定不要 | いつでも並行可 |
| 6 | 橋・JREV-0010r | 凍結 | 触らない |

**★3 の死因ラダー（1件ずつ直列に出ている＝これ自体が問題。→ 適合プローブで並列化する）**

| # | 死因 | 状態 |
|---|---|---|
| #1 | worker 自作テストの品質 | ✅ runner 方式で解決（DE-0497） |
| #2 | 固定 TS によるトークン永久消費 | ✅ **CLOSED（2026-07-23・commit 38d1988）。** gate1b=実 mint 経路 `mint_token` を attempt 違いで2回→`approval_id` 相異で決着＝**実経路は非退化**（固定 ts は attempt が task_id を変えるため無害）。当初 probe が `grant_approval` 直呼びで偽陽性＝族E も是正（gate1b を SPEC 準拠化） |
| #3 | provenance 未渡し | ✅ DE-0515（live 実証済） |
| #4 | token 型不一致（str / dict） | ✅ **DONE（commit 38d1988）。** 配線=`approval_registry.validate_by_token`（dict/str→approval_id 台帳照合・中身は捨て族C）で6経路統一 |
| #5 | token 3フィールド不整合 | ✅ **HEAD に反映済**（`authority.py:133` ts込み hash / mint・validate 整合）。commit すべき diff 無し（CC監査 07-23） |
| #6 | 受入オラクルと artifact の分離 | **未。`SEAM_PKG_MIRROR_v0_4` で直す**（TOKEN-GATE-01 の仕様に逃がさない） |
| #7 | sandbox に PYTHONPATH 未設定＝パッケージ import 不可 | ⚠️ **命名済（Web Y-3）。** `_run_test` が env 無指定（`live_worker_runtime.py:36-41`）。SEAM の配線（PYTHONPATH=sandbox＋複製）が #6 と同時に閉じる。配線は SEAM 範囲外 |

## §3. 決定ログ（番号のみ。中身は台帳を引く）

- **DE-0489〜0491**: 台帳登記簿 / 追跡外 LIVE 台帳の保全 / canonical 台帳は sole writer 必須
- **DE-0492〜0498**: producer 裁定 → 初回走行 → TEST_DEFECT 判定 → runner 方式確立 → 初の自律 CREATE
- **DE-0499〜0503**: GENERATE backend 置換（seam 構築 → cw 再配線 LIVE）
- **DE-0504〜0512**: 契約 passthrough A/B → ts 実ISO化 → iv 完成（骨格保存検査）
- **DE-0513〜0515**: PROBE-PIPE-01（§6 DONE 構造達成）→ halt → provenance 受け渡し完了
- **DE-0488**: DONE の定義確定（§1-5 の典拠）

> §3 は本来 DE 台帳から機械生成できる。手で書き足さないこと。生成スクリプトが出来たら本節ごと差し替える。

## §4. 保留裁定（本線を塞いでいない）

- principal 統制語彙に CLAUDE_WEB を足すか（現状 content_provenance で回避中）
- CHG-0128（authority.POLICY 追加）の事後承認 / 次回からゲート追加も Qwen 経由か
- `submit.py:88` の決定論 ts 規約に裏付け DE 無し → **もう調べ直さない**（この行を典拠とする）
- 自律経路（select_and_create）に前提検査ゲートが無く、承認ゲート(CHG-0128)がその代役である件の明文化
- 今日の CC 監査 3 件（#5=HEAD反映済 / #2=runner 既定 ts で OPEN / 骨格A1逆）の **DE 化**（番号は Taka／台帳側で採番。anchor は反映済だが SoR 未記帳）

## §5. 回し方

1. 本書を貼る。「本書に従う。再発明禁止。仕様起草前に §1 と突き合わせる」
2. 作業は §2 の ★ から。飛ばすなら理由を DE に残す
3. 新しい教訓 → DE 化 → 本書更新 → **可能なら配線に埋める**（読む棚ではなく通る道へ）
4. **観測は節度条件で**: 判定は 2 点まで。成功なら 10 行で終える。失敗時のみ詳細を開く。観測外の発見は「観測外: 事実1行」で止める
5. 「前に決めたはず」と思ったら思い出させようとせず DE 番号を投げる
6. **halt したら halt を報告する。** 回避策を自分で発明しない

## §6. 廃止条件

§2/§3 が決定論で生成できた時点で本書は廃止する。**この文書が要らなくなることが、繋がったことの証明。**
