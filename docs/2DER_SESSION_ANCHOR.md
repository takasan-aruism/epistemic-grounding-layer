# 2DER SESSION ANCHOR v2 — 毎セッション冒頭に貼る

- **これは何か:** 現在地の1枚。**履歴は書かない**（履歴は DE 台帳）。
- **サイズ上限: この文書は 1 画面。** §2 の各セルは「状態1行＋次の一手1行＋DE番号」まで。
  それ以上書きたくなったら DE を切って番号だけ置く。**v1 は 21KB まで肥大して読めなくなった。同じ轍を踏まない。**
- **序列: 台帳(DE) > 実測4部作 > MANAGER_ANCHOR > 本書 > 誰の記憶よりも。**
- **保存:** `egl/docs/2DER_SESSION_ANCHOR.md` / 更新はセッション末に依頼された側が行い Taka は保存のみ。
- last_updated: 2026-07-23 / 前版(21KB)を SUPERSEDE / CC 監査反映（death#5=HEAD反映済・#2=OPEN継続・骨格A1逆）＋ 仕様2本 pre-submit 監査（SEAM v0.2 / PROBE v0.3）

---

## §1. 不変の前提（変更は Taka 裁定のみ。再議論しない）

1. **Claude Code = 監査のみ。** 実装は Qwen（2DER 経由）のみ。例外議論は再開しない。
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
| ★3(A) | 恒久連結: GENERATE 段 = runner | 機構完備・§6 DONE 構造達成（DE-0513/0515）。骨格マーカー極性=仕様で補正済（SEAM v0.2 / PROBE v0.3）。**残=death#6 ＋ 発注側 conftest（`pkg_root`/`probe_env` 未存在・twoder に conftest.py 皆無=CC監査 07-23）** | (1) 発注側が conftest（`pkg_root`/`probe_env`）同梱=Web → (2) `SEAM_PKG_MIRROR_v0_2` submit→7/7（death#6） → (3) `CONFORMANCE_PROBE_v0_3` submit→走行 → (4) 実走で DONE |
| ★3(B) | token=authority 統合 | ts 完了(DE-0505) / provenance 完了(DE-0515)。残=token 統合 | TOKEN-GATE-01 起草済。**先に適合プローブで残破断を一括採取**してから1本の仕様で直す |
| 4 | SPR 抽出 | 仕様済・保留 | Taka 起動指示待ち |
| 5 | 台帳の家事（機械処分18／IDLE 8／DISPOSE 16内訳） | 未・裁定不要 | いつでも並行可 |
| 6 | 橋・JREV-0010r | 凍結 | 触らない |

**★3 の死因ラダー（1件ずつ直列に出ている＝これ自体が問題。→ 適合プローブで並列化する）**

| # | 死因 | 状態 |
|---|---|---|
| #1 | worker 自作テストの品質 | ✅ runner 方式で解決（DE-0497） |
| #2 | 固定 TS によるトークン永久消費 | ⚠️ **OPEN 継続。** runner `mint_token` に hardcoded 既定 ts 残存（`generate_via_runner.py:45`）→ authority の ISO 化では防げない。**gate1b（同一走行 2 回鋳造→`approval_id` 相異）で決着。**「DE-0505 で消えた」は族E（CC監査 07-23） |
| #3 | provenance 未渡し | ✅ DE-0515（live 実証済） |
| #4 | token 型不一致（str / dict） | 裁定済（修正は authority 側＝台帳照合）。実装未 |
| #5 | token 3フィールド不整合 | ✅ **HEAD に反映済**（`authority.py:133` ts込み hash / mint・validate 整合）。commit すべき diff 無し（CC監査 07-23） |
| #6 | 受入オラクルと artifact の分離 | **未。`SEAM_PKG_MIRROR_v0_2` で直す**（TOKEN-GATE-01 の仕様に逃がさない） |

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
