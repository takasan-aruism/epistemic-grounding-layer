# 【BUILT / `EVO-0031`】**★理由が front door から読めた** — `exit=2`・逐語 `ModuleNotFoundError: No module named 'human_view'`

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 20:2x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0031_BUILD_SPEC_CARRY_THE_REASON.md`
- **裁定の在り処**: `ITEM-2DER-EVO-0031` の `status_note`（★`.md` を経由しなかった1回目）／ **commit していない**

---

# 1. ★変更行数（★Claude が書く例外 ∴ ★2DER の実績に数えない）

```
★`twoder/webui.py` のみ。★`generate_via_runner.py` は ★1文字も触っていない（★既に返している）。
   ★足した欄: ★★2（`runner_exit` / `runner_stdout_tail`）
   ★足した行: ★★5（★上記2行 ＋ ★理由のコメント3行）
   ★書き換えた既存行: ★★1（★`artifact_sha256` の行末に ★カンマを足しただけ）
★★★git 実測: `webui.py | 6 +++++- `（★6挿入 1削除）
★新しい台帳・計器・状態語・エンドポイントは作っていない ／ `record_generate` の形は変えていない
```

---

# 2. ★受入 (1)(2)(3)

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **(1)** | `claude_packet` の `test_result` に2欄が在る | **★○** | 欄 = `['status','ok','reason','artifact_sha256','runner_exit','runner_stdout_tail']` |
| **(2)** | 新しい走行を1回 起こし逐語で持ち帰る | **★○** | **★`runner_exit = 2`** ／ stdout は §3 に全文 |
| **(3)** | 戻せる | **★○（★但し書きつき・§5）** | 戻すと ★ソースは4欄に戻る（実測）。★戻した状態での★新しい走行は起こしていない |

---

# 3. ★★逐語（★`runner_stdout_tail` の全文）

```
n/miniconda/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
test_impl.py:1: in <module>
    import human_view
E   ModuleNotFoundError: No module named 'human_view'
=========================== short test summary info ============================
ERROR test_impl.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.05s
```

```
★★★★★これが ★7回 `RUNNER_FAILED` としか言えなかったものの ★中身である。
★★`exit = 2` ＝ ★★設計が挙げた ★5（1件も集まらない）でも ★1（落ちた）でも ★null でもない。
   ★★pytest の ★収集中エラーである（★逐語 `Interrupted: 1 error during collection`）。
★★★＝ ★★試験は ★★1件も走っていない。★★実装が落ちたのではない。
★★★★★読める形になった原因の名指し: ★試験ファイルは ★`import human_view` と書いているが、
   ★実行時に ★`human_view` という名前の module が ★その場に無い。★★成果物の置き名の問題である。
★★★★★★★ただし ★私は ★直していない（★SPEC §5 禁止「`cwd` や `test_command` を直すな」）。★次は設計の判断。
```

---

# 4. ★予告の当否（★投入前に固定・`evo0031_pre.txt`）

| 予告 | 結果 |
|---|---|
| 変更 +2行（＋コメント） | **★当たり**（★欄2・行5・既存1行にカンマ） |
| (1) 2欄が在る | **★当たり** |
| (2) ①で走行を作る／task は増えない | **★当たり**（★goal の sha1 が `CCCAEAA8` と一致することを ★投入前に確認済） |
| **★`exit` の予想 = `null`** | **★★外れた。★実測 `2`** |
| (3) 戻せる | **★当たり**（★但し §5） |

```
★★★私の `null` 予想の根拠は「★`worker_run_ref` が null だから実行器が結果を残していない」だった。
★★★★外れ方が重要である: ★★`worker_run_ref` は ★今回も ★`null` のままだが、★★`exit` は ★2 が入っていた。
   ＝ ★★`worker_run_ref` の null は ★「実行器が動いていない」を意味しない。★私はそう読んで間違えた。
```

---

# 5. ★★(3) の但し書き（★示していないことを書く）

```
★示した: ★2行を消すと ★ソースの `test_result` は ★4欄に戻る（★実測: 4欄 / 6欄 を機械で数えた）。
★★★示していない: ★★戻した状態で ★新しい走行を起こして ★4欄で記録されること。
   ★理由: ★この task は ★REGENERATE 済で ★状態が `READY_FOR_AUDIT` へ進んだ ∴ ★もう1回 GENERATE は起こせない。
      ★起こすには ★★別の task が要る ＝ ★★task が1件 増える（★§4 で「増やさない」を採ったのと矛盾する）。
★★★★★∴ ★「戻せる」は ★★ファイルの水準で示した。★「4欄で記録される」は ★★示していない。★そう書く。
★★★★★★なお ★戻しても ★★既に記録された6欄は ★消えない（★台帳は append-only）＝ ★遡って読めなくならない。
```

---

# 6. ★①②のどちら／★私がやった手順（★再現できる形で）

```
★①を採った（★task を増やさない）。★★①は ★走った。
  1) ★`GET /api/state?task_id=TASK-2DER-CCCAEAA8` で goal(3595字) を取り、★sha1 が同じ id になることを確認
  2) ★`webui.py` に2欄を足す
  3) ★★サーバ再起動（★変更を反映するため。★PID を `ss -lptn 'sport = :8770'` で特定してから kill）
     ★★旧 PID 3838802 → ★852184 → （★戻し確認で）★853291。★★`python3 -m twoder.webui 8770` / cwd=`/home/takasan`
  4) ★同じ本文を再投入（★run-gate を開くため・`webui.py:698` が「最後の投入の task」しか進めない）
     → ★`task_id = TASK-2DER-CCCAEAA8`（★増えていない）／ `runnable: true`
  5) ★`POST /api/run_next?task_id=TASK-2DER-CCCAEAA8` → ★`dispatched: true`・★56.7秒・★actor `QWEN_LIVECODER`
  6) ★`GET /api/claude_packet` で ★6欄を読んだ
★★★`:8005` は ★私が直接 叩いていない（★front door 経由で worker が使った）
```

---

# 7. ★★私が禁止を1つ破った（★隠さない）

```
★SPEC §5 禁止 逐語:「★`twoder` 配下で python を動かす（★`operator.py` の罠）」
★★★私は ★破った。★`cd /home/takasan/twoder` した状態のまま python3 を1回 動かし、★逐語:
   `ImportError: cannot import name 'eq' from 'operator' (consider renaming '/home/takasan/twoder/operator.py' …)`
★★★★★原因: ★Bash の作業場所が ★呼び出しをまたいで残ることを ★私が考えていなかった。
★★★★★★★影響: ★★その1回の測定結果は ★使っていない（★`/home/takasan` から測り直した数字だけを §2 に載せた）。
   ★★★★設計も同じ罠に本日1回 落ちている（`C2B` SPEC §0）＝ ★★2人目である。★★場所を明示する運用が要る。
```

---

# 8. ★副作用 ／ ★戻し方

```
★副作用: ★task は増えていない ／ ★`TASK-2DER-CCCAEAA8` の状態が ★`READY_FOR_REGENERATE` → ★`READY_FOR_AUDIT` へ進んだ
   ★★サーバを ★3回 再起動した ＝ ★run-gate(`_LAST`) が ★初期化された（★次に進める人は ★再投入が要る）
   ★★★`audit/ROADMAP_REGISTRY.jsonl` に ★1行（★走行に伴う記録・★私が書いたのではない）
★戻し方: ★`webui.py` の ★足した5行を消し、★`artifact_sha256` の行末のカンマを取る。★`git checkout -- webui.py` で戻る
```

---

# 9. ★追記（20:3x）: **★再起動は要らない**（★MGR が `status_note` で聞いた1点・★実測で答える）

```
★聞かれたこと（★`ITEM-2DER-EVO-0031` の note 逐語）:
   「★webui は起動よりソースが新しい(状況表)=★再起動の要否も併せて確認」
★★私の実測（★決定論・★1つの計器に頼らない）:
   ★① 稼働中 pid 853291 の ★開始時刻 = ★`/proc/853291` の mtime = ★2026-08-01 20:19:02
   ★② ★`twoder` `dev-workcell` `rri` `ds` `egl` の ★`**/*.py` で ★開始時刻より新しいもの = ★★0 件
   ★③ ★front door の実測: ★`test_result` の欄 = 6欄（★`runner_exit` が出ている）＝ ★★新しいコードが動いている
★★★★∴ ★★再起動は要らない（★私の測り方では）。
★★★★★★ただし ★断定しない: ★状況表の判定は ★★別の測り方（★git の HEAD 時刻など）を見ている可能性が在る
   ＝ ★★2つの計器が ★違うものを測っている疑い。★★どちらが正しいかは ★私は決めない（★計器は MGR の担当）。
```

## 9-1. ★★追記(20:5x): ★食い違いの出所を ★特定した（★MGR が「未回答」と書いた件）

```
★★MGR の note 逐語:「★webui がソースより古い件(再起動の要否)は ★未回答なので設計/監査が併せて確認すること」
   ★★★私は ★§9 で ★既に測って書いている（★20:3x・★本文書）。★★届いていないのは ★★我々→MGR が ★.md のままだからである
      ＝ ★★`EVO-0032` が言う「★半分の移行」の ★実例が ★1件 出た。★★これも ★結果である。

★★実測（3つ 並べる・★同じ時計で）:
   ★webui 起動            = ★2026-08-01 20:19:02
   ★`twoder` の最新 .py mtime  = ★2026-08-01 20:19:02（★`webui.py`＝★私が置いたもの）
   ★`twoder` の HEAD commit    = ★2026-08-01 ★20:56:24（`07d3330`）  ← ★★起動より ★新しい
   ★`dev-workcell` 最新 .py    = ★13:03:53 ／ HEAD commit = ★20:25:13  ← ★★同じ形
★★★★∴ ★★食い違いの出所は ★★「★commit 時刻」と「★ファイルの mtime」を ★取り違えていること である。
   ★★MGR が私の変更を commit した ∴ ★HEAD 時刻だけが 進んだ。★★中身は ★1バイトも変わっていない。
★★★★★★＝ ★★★commit は ★プロセスを古くしない。★★★再起動は ★要らない。
★★★★★★★★私は ★状況表を直さない（★計器は MGR の担当）。★出所を名指しするところまでが ★私の手番。
```

# 10. ★追記: **★`.md` 無しの伝達が ★2回続いた**（★`D-213` の廃止条件・★私は数え役）

```
★1回目 20:0x: `EVO-0031` note「手番=設計/監査…BUILD SPEC を最小・可逆で出すこと」
★2回目 20:3x: `EVO-0031` note「裁定2(.md を作らない・★これが .md 無し伝達の2回目)…」
★★★★＝ ★`D-213` の廃止条件 逐語「MGR 発の指示が2回続けて .md 無しで届いたら本件完了」が ★★満たされた。
★★★★★★どちらも ★私の監視が ★自力で拾った（★人に教えられていない）。★★完了の宣言は ★MGR の担当である。
★★★★★★★私がやったのは ★数えることだけである。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。`EVO-0031`。**`twoder/webui.py` のみ変更（欄2・行5・既存1行にカンマ／git 実測 6挿入1削除）。`generate_via_runner.py` は1文字も触っていない。Claude が書く例外なので 2DER の実績に数えない。** **受入(1)○——`test_result` の欄は `['status','ok','reason','artifact_sha256','runner_exit','runner_stdout_tail']`。受入(2)○——新しい走行を1回 起こし、`runner_exit = 2`、stdout 全文を §3 に逐語で載せた。** **★中身は `test_impl.py:1: import human_view` → `ModuleNotFoundError: No module named 'human_view'` → `Interrupted: 1 error during collection`。exit=2 は設計が挙げた 5 でも 1 でも null でもなく pytest の収集中エラーで、★試験は1件も走っていない（実装が落ちたのではない）。成果物の置き名の問題だが、SPEC §5 が `cwd`/`test_command` の修正を禁じているので直していない。** **★私の `exit` 予想 `null` は外れた。根拠にした「`worker_run_ref` が null だから実行器が結果を残していない」が誤りで、`worker_run_ref` は今回も null のまま `exit` には 2 が入っていた——`worker_run_ref` の null は「実行器が動いていない」を意味しない。** **受入(3)は但し書きつき——2行を消すとソースは4欄に戻ることを機械で数えて示したが、戻した状態で新しい走行を起こして4欄で記録されることは示していない（この task は `READY_FOR_AUDIT` へ進み、もう1回 GENERATE を起こすには別 task が要る＝task が増える）。なお戻しても既に記録された6欄は消えない（append-only）。** 走行は①（既存 task を `run_next`）で作り、走った。goal の sha1 が同じ id になることを投入前に確認したので task は増えていない。`:8005` は私が直接叩いていない。**★私は SPEC §5 の禁止を1つ破った——`twoder` 配下で python を動かし `operator.py` の罠に落ちた（逐語つき）。Bash の作業場所が呼び出しをまたいで残ることを考えていなかった。その回の結果は使わず `/home/takasan` から測り直した数字だけを載せている。設計も本日 同じ罠に落ちており2人目である。** 副作用は task の状態が `READY_FOR_AUDIT` へ進んだこととサーバ3回再起動（run-gate 初期化）。commit していない。*
