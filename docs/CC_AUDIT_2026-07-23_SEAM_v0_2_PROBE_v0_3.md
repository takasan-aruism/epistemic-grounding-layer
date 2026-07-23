# CC 投入前監査（生データ・relay 用）— SEAM_PKG_MIRROR_v0_2 / CONFORMANCE_PROBE_v0_3

- 監査者: Claude Code（監査のみ）/ 日付: 2026-07-23
- 用途: Claude Web への relay。**要約せず生のまま渡す。** 事実と `file:line` のみ。
- 職掌: 修正案・優先順位付け・評価語は含めない（それは Qwen/Web の仕事）。
- anchor に載るのは E 由来の *状態*（conftest 不在）だけ。監査本体は本書が置き場。

---

## Web が名指しした 2 点（先出し）

- **A5/A6 → 区間割りの作り直しは不要。** FILL は1ファイルに複数可（A5）、位置制約なし＝関数本体・ファイル末尾どこでも可（A6）。骨格2本の複数 FILL 使用は分割器と整合。
- **C1〜C3** は §C のとおり。

---

## A. FILL マーカー規約（正本 = `generate_via_runner.py:49-60`）

```python
def _skeleton_fixed_segments(skeleton):
    for line in (skeleton or "").splitlines(keepends=True):
        if "<<<FILL" in line:      # ← 判定はこの部分文字列のみ
```

```
A1 / 判定は部分文字列 "<<<FILL"。`<<<FILL>>>` は一致する / generate_via_runner.py:53
A2 / ラベル可（`<<<FILL:body>>>` は "<<<FILL" を含み一致）。※`<<<QWEN_FILL` は不一致（"<<<F"≠"<<<Q"） / generate_via_runner.py:53
A3 / 行単位。"<<<FILL" を含む行は全体が固定区間から除外される＝実質マーカー専用行 / generate_via_runner.py:52-57
A4 / マーカー行の前置き空白は任意（行ごと除外なので無関係）。固定区間は各行 bytes 保存 / generate_via_runner.py:52-55
A5 / 複数 FILL 可。各 FILL 行で分割、空セグメントは除去 / generate_via_runner.py:54-60
A6 / 位置制約なし。固定区間は非FILL行の連続塊で、artifact 内に順序どおり find() で存在すれば可 / generate_via_runner.py:68-73
```

## B. 参照行の実在確認

```
B generate_via_runner.py:45   / 実在。`k.get("ts", "2026-07-11T09:00:00")` = mint_token の hardcoded 既定 ts / generate_via_runner.py:45
B generate_via_runner.py:49   / 実在。`def _skeleton_fixed_segments` = FILL 分割器（正本） / generate_via_runner.py:49
B generate_via_runner.py:93-94/ 実在するが「受入テスト実行」ではない。93=task_packet の test_file/test_body、94=test_command 定義。実行は run_minimal_slice 内 / generate_via_runner.py:93-94
B authority.py:133            / 実在。`approval_id = sha1(task_id|operation_class|action_type|ts)` = ts込み hash / authority.py:133
B authority.py:141-144        / 実在するが「GRANT 照合」ではない。`def approval_consumed` = CONSUMED 事象の存否検査。GRANT 発行は grant_approval(129-138) / authority.py:141-144
B authority.py:147-162        / 実在。`def validate_approval` = token gate の期待値元 / authority.py:147-162
B live_worker_runtime.py:94   / 実在。`val = AUTH.validate_approval(approval_token, action, task_id, op, ts)` = token gate 呼び出し側 / live_worker_runtime.py:94
```

## C. 完全修飾シンボル名

```
C1 / twoder.live_worker_runtime.run_minimal_slice / live_worker_runtime.py:57（import 実証 generate_via_runner.py:24）
C2 / twoder.authority.validate_approval / authority.py:147
C3 / twoder.generate_via_runner.verify_skeleton_preserved / generate_via_runner.py:63
```

## D. 配置先

```
D1 / twoder/seam/ 未存在（新規作成になる） / -
D2 / twoder/probe/ 未存在（新規作成になる） / -
D3 / パッケージ名 twoder 正しい。__init__.py 実在。import 規約 `from twoder.X import ...` / generate_via_runner.py:24
```

## E. テスト fixture の所在

```
E1 / twoder に conftest.py は 1 件も存在しない（find 空） / -
E2 / fixture は各テストモジュール内に @pytest.fixture() で定義。共有 conftest 無し / test_runner_invocation_spec.py:62-63
E3 / pkg_root / probe_env fixture は未存在（grep 空）。隔離は module 冒頭 os.environ.update({"EGL_DATA_DIR": tempfile.mkdtemp(...)}) 方式 / regression/test_live_coder_backend.py:8
```

E2 逐語:

```python
@pytest.fixture()
def harness(monkeypatch):
```

## F. 既存機構の所在

```
F1 / EGL_DATA_DIR throwaway = 名前付きヘルパ無し。inline os.environ.update({"EGL_DATA_DIR": tempfile.mkdtemp(prefix=...)})。setup+teardown 例 counterfactual_runner.py:21-25 / regression/test_preflight_gate.py:5
F2 / canonical 台帳パス解決 = control_surface_read.py:21（ROOT/"egl"/"DESIGN_EVIDENCE_LEDGER.jsonl"）。token GRANT/CONSUMED は authority が _ds() 経由で DS 事象流へ / control_surface_read.py:21
F3 / :8005 は hardcode 既定。DEFAULT_ENDPOINT="http://127.0.0.1:8005/v1/chat/completions"。endpoint 引数 / chat_fn 注入で差替可。既定は env-var でない / qwen_worker.py:12,16
```

## G. 骨格の受入可否（読むのみ）

```
G1 / FILL 置き位置の違反なし。A6=位置制約なし、`<<<FILL>>>` は A1 一致。両仕様の骨格は分割器と整合 / generate_via_runner.py:49-73
G2 / 両仕様の固定区間に構文誤りは観測せず（固定のみは FILL 本体を欠くため単体 compile 不可＝視認確認） / -
```

## 観測外

```
観測外: gate1b が通す「実 mint 経路」mint_token は _REAL_MINTER を action="USE_VLLM_INFERENCE"/op="DW_MACHINE_OP" で呼ぶ（LIVE_WORKER 値でない） / generate_via_runner.py:42-45
```

---

## 進行への含意（事実のみ。判断は Web）

- **E だけで進めても骨格は弾かれない** — G1 のとおり骨格2本は分割器と整合済み。
- 往復増の要因になり得るのは 2 つ:
  1. E（conftest 未同梱）— `pkg_root`/`probe_env` fixture が未存在。発注側が同梱しなければ collection error。
  2. B の行ラベル 2 件のズレ — `authority.py:141-144` は GRANT 照合でなく `approval_consumed`／`generate_via_runner.py:93-94` は test_command 定義で実行でない。ゲート期待値の出所を指し直すか否かは Web 判断。
