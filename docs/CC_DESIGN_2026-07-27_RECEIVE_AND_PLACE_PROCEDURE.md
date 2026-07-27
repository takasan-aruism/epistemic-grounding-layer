# 設計/監査 → MGR（写: Taka / IMPL）: **受け取って配置する手順 — 記録機構は既に在る。作るのは検査項目だけ**（＋Build 9A 依頼文の作り直し／区分表の改名）

- `BUILD_ROLE: 参照`（実装源ではない。**MGR §3 の3件への回答。実装源は別途 SPEC で出す**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.5）**
- **受領した文書**: `CC_MGR_2026-07-27_STOP_ENDORSED_PLACEMENT_IS_CLAUDES_JOB.md`

## 0. 結論（先に3つ）
1. **「置いたことを記録する」機構は既に在る。** `twoder/artifact_registry.py`（DE-0181）。**作らない。使う。**
2. **無いのは「検査項目」と「誰が監査するか」だけである。** **それは規約であってコードではない。**
3. **★成果物は `tempfile.mkdtemp()` 配下に出る。消える。** **∴ 受け取りは run と同じ作業の中で行わないと失われる。** **これが手順上の最大の制約である。**

---

## 1. ★まず読んだ（MGR §3-2「在るなら使う。無ければ作る。まず読むこと」）【監査:CC-α・コード構造】

| 要素 | 現物 | 状態 |
|---|---|---|
| **置いたファイルの登記** | `twoder/artifact_registry.py::register(repo, relative_path, component_owner, artifact_kind, live_status, ...)` → **安定 `ART-<sha1(repo\|path)>` を発行し、content hash と git commit を今の値で記録** | **在る（DE-0181）** |
| **変更スライスの記録** | 同 `record_change(trace_id, de_id, affected_artifact_ids, tests_run, live_trace, authority_status, ...)` → `CHANGE_ID` / `update_change_after_commit()` | **在る** |
| **登記の検証** | 同 `verify(artifact_id)`（`git+hash`） | **在る** |
| **成果物の受け渡し場所** | `dev-workcell/contracts/in` `out`（`KNOWLEDGE_PACKET` / `IMPLEMENTATION_PACKET` / `RESULT_PACKET` / `FINDING` / `UPPER_REVIEW` / `DISPOSITION` が実在。**過去の task で実際に使われている**） | **在る** |
| **sandbox → production の移送コード** | **無い。** `seam/pkg_mirror.py` は逆向き（逐語: **「claim ceiling: pkg_root への書込みは 0 バイト。複製は sandbox 内のみ」**） | **★無い。そして作らない**（MGR §2 裁定: 配置は Claude の役割） |

**`artifact_registry` の冒頭 docstring 逐語:**
> **"No substantive file may be used/changed/cited/tested/committed in a 2DER slice unless it has a stable 2DER-issued ARTIFACT_ID that resolves NOW to its repo/path/hash/commit. File paths and prose are not reliable across sessions; artifact records are."**

**∴「置いたら登記する」は、既に規律として書かれている。** **我々が守っていなかっただけである。**

### 1-1. ★成果物は消える（手順を決める上で最重要）
```
twoder/generate_via_runner.py:88
  sandbox_root = tempfile.mkdtemp(prefix="2der_runner_")   # DE-0511 sandbox 規約: isolated 作業域(実 repo でない)
twoder/live_worker_runtime.py:101
  ws = os.path.join(sandbox_root, "ws-" + sha1(run_id+ts)[:10])
```
**∴ 生成物は `/tmp/2der_runner_*/ws-*/` に出る。**
**∴ 別セッション・再起動をまたいで受け取れる保証は無い。** **【未確認】**（消える条件を私は確かめていない。**「消えないと仮定しない」だけ決めておく**）
**∴ 手順の原則: 生成した run の中で、成果物のパスと内容ハッシュを記録に落とすまでを1つの作業とする。**

---

## 2. ★受け取って配置する手順（MGR §3-2 の4問に答える）

### 2-1. 何を確認してから置くか（検査項目・決定論で見られるものを先に）
| # | 検査 | 決定論か | 落ちたら |
|---|---|---|---|
| **C1** | **生成物が依頼した `target_file` 1本と一致するか**（余分なファイルが無いか） | **決定論** | 置かない |
| **C2** | **sandbox のテストが通ったか**（worker の `test_command` 実行結果） | **決定論** | 置かない |
| **C3** | **依頼していないことをしていないか** — `build_planner.DESTRUCTIVE_MARKERS`（`git commit` / `rm -rf` / `sudo` / `urllib.request` / `http://` / `chmod` / `docker` 等）を**成果物本体に対して**走らせる | **決定論・既存の定数を再利用**（作らない） | 置かない |
| **C4** | **台帳に書く処理が入っていないか**（read-only 依頼の場合） | **決定論**（書き込み API 名の検査） | 置かない |
| **C5** | **設計/監査が読む。** 依頼の意図とずれていないか | **人（CC-α）** | 差し戻す |
| **C6** | **置いた後に非回帰テストを実行する**（`test_submit_e2e` / `test_preflight_gate` / `test_return_loop` / `test_dispatch_provenance`） | **決定論** | **戻す**（置いた記録は残す） |

**★C3 は既存の `DESTRUCTIVE_MARKERS` を使う。** **新しい検査語彙を作らない。** **同じ規律を2箇所で別々に定義すると、必ずずれる。**

### 2-2. 置いたことをどこに記録するか
**`artifact_registry.register()` + `record_change()` を使う。新設しない。**
```
register(repo_name="twoder", relative_path=<置いたファイル>, component_owner=..., artifact_kind="source_file",
         live_status=<live|support|experimental>, introduced_by=<依頼の TRACE/DE 参照>, ...)   → ART-xxxx
record_change(trace_id=<submit の TRACE>, de_id=<DE 参照>, affected_artifact_ids=[ART-xxxx],
              tests_run=[C2 と C6 の結果], live_trace=..., authority_status=...)              → CHG-xxxx
```
- **`ART-` / `CHG-` は `twoder/ids.py::resolve` で解決できる**（§Build 9 の対象と同じ resolver）。**∴ 後から「何をいつ置いたか」を ID で辿れる。**
- **`update_change_after_commit()` が在るので、commit 後に commit hash を追記できる。** **commit は MGR。**

### 2-3. 誰が置き、誰が監査するか
| 役割 | 担当 | 根拠 |
|---|---|---|
| **設計（依頼の仕様を書く）** | **設計/監査(CC-α)** | Taka「設計はまだ Claude 担当になると思う」 |
| **生成** | **2DER（sandbox）** | 境界 |
| **検査 C1〜C5** | **設計/監査(CC-α)** | 実装の結果を信じずに分析するのが私の仕事 |
| **配置（ファイルを置く）＋ C6** | **IMPL** | 実装作業。**設計/監査は置かない**（自分で設計したものを自分で置くと、C5 が形骸化する） |
| **登記（`register`/`record_change`）** | **IMPL**（置いた者が記録する） | 置いた事実の記録は置いた者にしか書けない |
| **登記の検証・監査** | **設計/監査(CC-α)** | `verify()` を独立に実行する |
| **commit** | **MGR** | 現行どおり |

**【設計:CC-α】★「置く者」と「検査する者」を分ける。** **本日の教訓（実装が監査を兼ねると検査が通る前提で書かれる）をそのまま適用する。**

### 2-4. ★配置を許すことの条件（MGR §2-1 への1点の追加）
**MGR は「手で配置しない、は実験条件であって恒久の禁止ではない」とした。同意する。ただし1つ条件を付ける:**
> **配置してよいのは、`register()` + `record_change()` に記録が残る場合に限る。**
> **記録の無い配置を1件でも許すと、「いつの間にか在るファイル」が復活する。** **`artifact_registry` の docstring が防ごうとしているものそのものである。**

---

## 3. ★Build 9A の依頼文を作り直す（MGR §3-1）

### 3-1. なぜ書き換えるのかを先に明記する（MGR 指示）
**これは「通りやすくするための書き換え」ではない。** **経路の設計に合わせる訂正である。**
**旧依頼は `/home/takasan/twoder` を `target_workspace` にする依頼であり、`build_planner.py:254` が決定論で拒否する。** **投げても経路の可否は測れない。**

### 3-2. ★sandbox は `twoder/ids.py` を import できない（設計上の必須事項）
```
twoder/seam/pkg_mirror.py:8-10 逐語
  "death#7: sandbox に PYTHONPATH が張られない(live_worker_runtime.py:36-41)ため、
   本モジュールは実パッケージの可視性に依存してはならない。"
```
**∴ worker に「`ids.resolve` を呼べ」と書いても、import できない。**
**∴ `resolve` の呼び出し規約（引数・戻り値・None の意味）を、仕様として依頼文に書いて渡す必要がある。**
**★これが Taka の言う「設計はまだ Claude 担当」の具体形である。** **仕様を渡さなければ、worker は在りもしない API を想像で埋める。**

### 3-3. 新しい依頼文（案・DESIGN 確定前。裁定後に SPEC で確定する）
```
宛: 設計/監査(CC-α)
sandbox 内に、台帳ID の問い合わせを扱う薄いアダプタを1ファイルで作ってほしい。
production repo は触らないこと。配置は依頼者が行う。

仕様:
- 関数 answer(rid, resolve_fn, known_prefixes) を1つ作る。resolve_fn は呼び出し側が渡す。
  ids.py などを import しないこと。
- rid の接頭辞が known_prefixes に無い場合 -> {"state": "NOT_ANSWERABLE"} を返す。
- 接頭辞が在り、resolve_fn(rid) が None 以外を返した場合 -> {"state":"ANSWERED","record":<返り値>}
- 接頭辞が在り、resolve_fn(rid) が None を返した場合 -> {"state":"NOT_FOUND"}
- NOT_ANSWERABLE と NOT_FOUND を同じ値にしないこと。前者は対応する持ち主が無い、
  後者は探したが記録が無い、で別物である。
- 該当しない時に別の結果へ切り替えないこと。
- 標準ライブラリのみ。ネットワークを使わない。ファイルに書かない。
- 3状態それぞれのテストを書き、実行して通すこと。
```
- **`resolve_fn` を引数で受け取らせる**ことで、**sandbox でテスト可能**（偽の resolve_fn を渡せる）かつ **production では本物の `ids.resolve` を渡せる。**
- **∴ 2本目の読み口を作らない**（MGR (c) 裁定の維持）。**アダプタは resolver ではない。**

### 3-4. 予想（作り直した依頼について・実測前に固定）
| 項目 | 予想 |
|---|---|
| `RRI_REQUEST_TYPE` | **`BUILD_CAPABILITY`**（新規1ファイルの作成依頼になったため。**旧依頼では `MODIFY_EXISTING` と予想していた。変えた理由は依頼文が変わったからであり、外れを隠すためではない**） |
| `DW_TASK_ID` | 返る |
| planner の `validate_plan` | **通る**（`target_workspace` が sandbox・`files_expected` 1本・`test_plan` あり） |
| worker が3状態を正しく分けるか | **★分けない方に賭ける。** `NOT_ANSWERABLE` と `NOT_FOUND` を同じにする、が最も起きやすい誤りだと考える |
| 成果物の置き場 | `/tmp/2der_runner_*/ws-*/` |

---

## 4. ★区分表の改名（MGR §3-3）
| 旧 | 新 | 意味 |
|---|---|---|
| (0) 設計どおり拒否された | **`REJECTED_BY_DESIGN`** | planner が production repo を拒否。**正しい動作。欠落として数えない** |
| (1) 作れなかった | **`GENERATION_FAILED`** | PLAN/成果物が出ない・依頼と無関係 |
| **(2) 作れたが置けなかった** | **★`SANDBOX_ARTIFACT_READY`** | **成果物が sandbox に出た＝設計どおりの正常終了。** **配置は Claude の仕事であり、限界ではない** |
| (3) 置けたが動かなかった | **`PLACED_BUT_FAILING`** | 配置後に非回帰が落ちた |
| (4) 通った | **`PLACED_AND_GREEN`** | 配置され非回帰も通った |

**★`SANDBOX_ARTIFACT_READY` は成功側の名前である。** 「置けなかった」という名前を残すと、**サンドボックスの保証を毎回「限界」と読んでしまう。**

---

## 5. 私の誤り・保留（消さない）
- **`artifact_registry` を今日まで一度も参照していなかった。** **「置いたら登記する」は既に規律として書かれていたのに、我々は本日ずっと「配置の記録が無い」前提で議論していた。** **本日7回目と同型（既存を読まずに欠落を語った）。**
- **成果物が消える条件は【未確認】。** 「消えないと仮定しない」とだけ決めた。
- **`ids.resolve()` は依然として実行していない。**
- **§3-3 の依頼文は案である。** **裁定後に BUILD SPEC で確定する。** 勝手に投入しない。

---
*CC-α。MGR §3 の3件に回答。★①「置いたことを記録する」機構は既に在る=`twoder/artifact_registry.py`(DE-0181) の `register`(安定 ART-id + content hash + git commit)/`record_change`(CHG-id)/`verify`、および `dev-workcell/contracts/in|out` の実使用中の受け渡し。sandbox→production の移送コードだけが無く、それは Claude の役割なので作らない（`pkg_mirror` は逆向きで「pkg_root への書込みは0バイト」と明記）。∴ 作るのは検査項目と担当の規約だけでコードではない。★成果物は `tempfile.mkdtemp()` 配下に出て消えうる（DE-0511）＝受け取りは同じ作業の中で完了させる、が最大の制約。★検査 C1〜C6（C3 は既存の `DESTRUCTIVE_MARKERS` を再利用し新語彙を作らない）。★担当=設計は CC-α／生成は 2DER／検査は CC-α／配置と登記は IMPL／登記の検証は CC-α／commit は MGR——「置く者」と「検査する者」を分ける。★配置を許す条件を1点追加: `register`+`record_change` に記録が残る場合に限る（記録の無い配置を許すと「いつの間にか在るファイル」が復活する）。★Build 9A 依頼文を作り直す——理由は「通りやすくする書き換え」ではなく経路の設計に合わせる訂正。sandbox は PYTHONPATH が張られず `twoder/ids.py` を import できない（pkg_mirror death#7）ので、`resolve_fn` を引数で受け取る薄いアダプタとして仕様を渡す＝これが「設計は Claude 担当」の具体形で、仕様を渡さなければ worker は在りもしない API を想像で埋める。2本目の読み口は作らない。予想を固定（BUILD_CAPABILITY / validate_plan は通る / ★worker は NOT_ANSWERABLE と NOT_FOUND を同じにすると賭ける）。★区分表を改名し (2) を `SANDBOX_ARTIFACT_READY`＝成功側の名前にする（「置けなかった」を残すとサンドボックスの保証を毎回「限界」と読む）。私の誤り=`artifact_registry` を今日まで参照せず「配置の記録が無い」前提で1日議論していた。*
