# 【BUILT / `EVO-0031`】欄は付いた — **★しかし今回の走行は `SKELETON_VIOLATION` にならず ★★試験が走って落ちた（1 failed / ★6 passed）**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 23:3x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0031_BUILD_SPEC_NAME_THE_MISSING_SEGMENT.md`
- **commit していない** ／ **骨格を推測で直していない** ／ **`twoder` 配下で python を動かしていない（★今回は守った）**

---

# 1. ★変更行数（★Claude が書く例外 ∴ ★2DER の実績に数えない）

```
★`twoder/generate_via_runner.py`  ★+21 / -2（★新関数 14行[docstring 4含む]＋枝の書き換え 5行）
★`twoder/webui.py`                ★+2 / -1（★欄1行＋既存行末のカンマ）
★★合計 ★23挿入 3削除。★新しい状態語・台帳・計器・エンドポイントは作っていない
★★★`verify_skeleton_preserved` は ★1文字も触っていない（★消していない・緩めていない）
```

---

# 2. ★呼び出し元の全数走査 → **★「足す形」を採った**（★報告項目4）

| 参照元 | 件数 | 種類 |
|---|---|---|
| `generate_via_runner.py:219` | **1** | ★production の呼び出し |
| `twoder/test_runner_invocation_spec.py` | **5** | ★試験が ★直接 呼ぶ |
| `twoder/probe/conformance_probe.py:285` | **1** | ★文字列 `"twoder.generate_via_runner.verify_skeleton_preserved"` を `bind_real` で解決 |
| `egl/docs/audit_*.py` 4本 | 4 | ★同名の**別定義**（コピー）＝ ★呼び出し元ではない |

```
★★★∴ ★production は1箇所だが ★★試験と probe が ★名指しで参照している ∴ ★★置換しない・★足した。
★★★★（★SPEC §2-1 は「1箇所だけなら置き換えてよい」だが、★★消せば試験と probe が壊れる ∴ ★安全側に倒した）
```

---

# 3. ★受入 (1)〜(4)

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **(1)** | `test_result` に `skeleton_missing_segment` が在り読める | **★○** | 欄 = `['status','ok','reason','artifact_sha256','runner_exit','runner_stdout_tail','skeleton_missing_segment']` |
| **(2)** | `0E5E8675` で ★逐語を持ち帰る | **★★示せない** | ★今回の走行は **`SKELETON_VIOLATION` にならなかった** ∴ 値は **`None`**（★正しい None）。★§4 |
| **(3)** | 400字で切れ、切ったと分かる | **★○（★純関数で確認・★front door ではない）** | ★616字 → **★412字**・末尾 **`…(truncated)`**。★§5 |
| **(4)** | 戻せる | **★○（★但し `git checkout` では戻らない）** | ★手で戻した版が ★変更前の commit と **★バイト一致**。★§6 |

---

# 4. ★★(2) が示せない理由 ＝ **★今回 起きたことの方が大きい**

```
★★走行は起きた（`run_next` → `dispatched: true`・★268.8秒・actor `QWEN_LIVECODER`）。
★★★しかし ★結果は ★`SKELETON_VIOLATION` ではなかった:
   ★`reason` = ★`RUNNER_FAILED` ／ ★`runner_exit` = ★★1 ／ ★`skeleton_missing_segment` = ★`None`
★★★★★＝ ★★骨格は ★保たれていた ∴ ★`None` は ★★正しい（★欄が働いていないのではない）。
★★★★★★★そして ★`exit = 1` は ★★「試験は走って落ちた」である。★逐語:

    E           AssertionError: item_id:
    E           assert 'item_id:' in {'Alpha', 'I1', 'P1', 'item_id', 'phase_id', 'status_ja', ...}
    test_impl.py:33: AssertionError
    FAILED test_impl.py::test_summary_and_full_are_derived_not_invented - Asserti...
    ★★★★1 failed, ★★6 passed in 0.02s

★★★★★★★★★＝ ★★★7本のうち ★6本 通り、★1本だけ落ちた。★★★どれが落ちたかも ★名前で分かる。
   ★★これは ★`EVO-0031` の受入(4)（★「7本のうち どれが通り どれが落ちたか」）が ★★front door から満たされた形である。
★★★★★★★★★★ただし ★これは ★★私の受入(2) ではない ∴ ★★(2) は「示せない」と書く（★通ったと書かない）。
```

---

# 5. ★(3) の確かめ方（★純関数・★投入していない・★出所を明記する）

```
★front door からは示せない（★`SKELETON_VIOLATION` が起きていないため）∴ ★純関数で確かめた。
★★（★監査が C-2 訂正で「純関数で示せないか先に見る」と書いた形に倣った）
★実測（★`/home/takasan` から実行・★`twoder` 配下では動かしていない）:
   ★この task の skeleton = ★616字 ／ ★`<<<FILL` = ★0件 ∴ ★固定区間は1つ＝全文
   ★① `skeleton_missing_segment(sk, "")` → ★616字 の断片 → ★`:219` と同じ式で切ると ★412字・末尾 `…(truncated)`
      ★逐語(先頭)：`# impl.py` / `def render(roadmap, control, asof, only_incomplete=False):` …
   ★② `skeleton_missing_segment(sk, 骨格を含む文字列)` → ★`None`（★誤検出しない）
   ★③ `skeleton_missing_segment(sk, None)` → ★`'(artifact is not a string)'`（★SPEC どおり）
```

---

# 6. ★★(4) で分かったこと: **★`git checkout --` では もう戻らない**（★運用の事実）

```
★私は ★SPEC どおり ★「戻して確かめ、また足す」をやろうとして ★`git checkout -- ` を打った。
★★★戻らなかった。★理由: ★★MGR が ★私の変更を ★★既に commit していた（`65c4ecf`「IMPL's change in flight」）
   ＝ ★★HEAD が ★私の変更を含む ∴ ★checkout は ★変更を ★復元する。
★★★★正しく確かめ直した（★手で3箇所を戻した版を作り ★変更前と比べた）:
   ★`git show 65c4ecf~1:generate_via_runner.py` と ★★バイト一致 → ★★True
   ★`git show 65c4ecf~1:webui.py`               と ★★バイト一致 → ★★True
★★★★★∴ ★★可逆である。★★ただし ★戻し方は ★★「`git checkout`」ではなく ★★「3箇所を消す」と書くこと。
★★★★★★★★これは ★私が ★本日 ★他の BUILT に ★★「`git checkout -- ` で戻る」と ★書いてきたものにも ★当たる
   ＝ ★★commit された後は ★その一行が ★★嘘になる。★★以後 そう書かない。
```

---

# 7. ★予告の当否（★投入前に固定・`evo0031b_pre.txt`）

| 予告 | 結果 |
|---|---|
| 呼び出し元を走査し「足す形」を採る | **★当たり**（★production 1 ＋ 試験5 ＋ probe 1） |
| 変更 14行前後 | **★★外れ（★過少）**。★実測 ★23挿入3削除（★docstring と枝の整形で増えた） |
| (1) 欄が在る | **★当たり** |
| (2) `0E5E8675` を再投入＋`run_next` で走らせる／task は増えない | **★当たり**（★走った・★id 一致・★増えていない） |
| **(3) truncated が付く** | **★当たり**（★616→412字）。★ただし ★front door ではなく ★純関数で示した |
| (4) 戻せる | **★当たり**。★ただし ★戻し方の書き方が ★誤っていた（★§6） |
| **★`SKELETON_VIOLATION` が再現する（★暗黙の前提）** | **★★外れた**。★★今回は ★骨格が保たれ ★試験が走った |

---

# 8. ★副作用 ／ ★戻し方 ／ ★やっていないこと

```
★副作用: ★task は増えていない（★`0E5E8675` の sha1 一致を投入前に確認）
   ★`0E5E8675` の状態が ★REGENERATE 1回分 進んだ ／ ★サーバを1回 再起動（★pid 853291 → 885989・run-gate 初期化）
   ★★REGENERATE で worker が ★`:8005` を使った（★front door 経由・★私が直接 叩いたのではない）
★戻し方（★正しい書き方）: ★① `generate_via_runner.py` の ★`skeleton_missing_segment` 関数を消す
   ★② 同ファイルの枝を ★`if artifact is not None and not verify_skeleton_preserved(skeleton, artifact):` に戻す
   ★③ `webui.py` の ★`"skeleton_missing_segment": …` の1行を消し ★前行の末尾カンマを取る
★やっていないこと: ★骨格を推測で直していない ／ ★契約を書き直していない ／ ★commit していない
   ★★測っていない: ★★`SKELETON_VIOLATION` が実際に起きた時の ★front door での見え方（★★起きなかった）
```

---

# 9. ★追記(00:4x): 「`test_result` が task によって在ったり無かったりする条件」 — **★条件は ★task ではない。★口である**（★構造で答える）

```
★MGR の note 逐語:「★GET /api/state の test_result が空({})。★0E5E8675 では読めたのに 816D6F68 では読めない
   ＝ ★同じ症状の2回目。…★3値でなく ★構造で答えること」
```

**★実測（★2 task × 2口・★いま）**

| task | `dw_state` | `GET /api/state` | `GET /api/claude_packet` |
|---|---|---|---|
| `TASK-2DER-816D6F68` | READY_FOR_REGENERATE | **★キー自体が無い** | **★7欄**（`…, skeleton_missing_segment`） |
| `TASK-2DER-0E5E8675` | READY_FOR_AUDIT | **★キー自体が無い** | **★7欄** |

```
★★★★∴ ★★「0E5E8675 では読めた」は ★★`/api/state` ではない（★★いま測ると ★どちらも ★キーが無い）。
★★★★★★★★★`816D6F68` の値は ★★読める。★★★止まる必要は無かった。

★★構造（★ソースで示す・★推測しない）:
   ★① `test_result` を出しているのは ★★`claude_packet()` の ★1行だけ（`webui.py:223` 逐語）:
         `"test_result": (gen["payload"].get("test_result") if gen else None)`
      ★`gen` = ★最後の GENERATE / REGENERATE の記録。★★無ければ ★`None`。
   ★② `build_state()`（`/api/state` の中身・`webui.py:124-140`）が返すキーに ★★`test_result` は ★★無い。
      ★`work` のキーは ★`['next_information_need','acquisition_method','dw_task_id']` の ★3つだけ（★実測）。
★★★★★★∴ ★★条件は ★★「どの task か」ではなく ★★★「どの口を叩いたか」である。
   ★`/api/state` → ★★構造上 ★常に 無い（★task によらない）
   ★`/api/claude_packet` → ★★GENERATE/REGENERATE が1回でも記録されていれば ★在る／★無ければ `None`
★★★★★★★★★＝ ★9項目の ★#1「置いたなら、どこから読めるか」に ★私が半分しか答えていなかった。
   ★★私は ★`claude_packet` に出して ★「読める」と書いたが、★★読む側が ★`/api/state` を見ることを ★確かめていない。
   ★★★★どちらの口に出すか（★あるいは両方か）は ★★設計の判断である。★★私は決めない。
```**変更は `generate_via_runner.py` +21/-2 と `webui.py` +2/-1（計 23挿入3削除）。`verify_skeleton_preserved` は1文字も触っていない。Claude が書く例外なので 2DER の実績に数えない。** **呼び出し元は全数走査して「足す形」を採った——production の呼び出しは `:219` の1箇所だが、`test_runner_invocation_spec.py` が5箇所で直接呼び、`conformance_probe.py:285` が文字列で名指し解決しているので、置換すれば壊れる。** **受入(1)○——`test_result` に `skeleton_missing_segment` の欄が在る。(3)○——616字の断片が412字＋`…(truncated)` に切れる（ただし front door ではなく純関数で確認。理由は下記）。(4)○——手で3箇所戻した版が変更前の commit とバイト一致。** **★(2) は示せない——走行は起きた（268.8秒・`QWEN_LIVECODER`）が `SKELETON_VIOLATION` にならず、`skeleton_missing_segment` は `None` だった（骨格が保たれていた＝正しい None）。★代わりに大きいことが起きた: `runner_exit = 1` で「試験が走って落ちた」——逐語 `AssertionError: item_id:` / `test_impl.py:33` / ★`1 failed, 6 passed`。7本のうち6本が通り、落ちた1本の名前まで front door から分かる。これは `EVO-0031` の受入(4) が満たされた形だが、私の受入(2) ではないので「示せない」と書く。** **★(4) で運用の事実が1つ出た——`git checkout --` ではもう戻らない。MGR が私の変更を既に commit していた（`65c4ecf`）ので HEAD が変更を含み、checkout は逆に変更を復元する。∴ 戻し方は「3箇所を消す」と書くべきで、私が本日 他の BUILT に書いた「`git checkout -- ` で戻る」は commit 後には嘘になる。以後そう書かない。** 予告は行数を過少に見積もり（14→実測23）、`SKELETON_VIOLATION` の再現という暗黙の前提も外れた。副作用は task 増なし・状態が1回分進行・サーバ1回再起動。骨格は推測で直していない。commit していない。*
