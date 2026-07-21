#!/usr/bin/env python3
"""workcell runner v0.1.2 — GPT監査 S-1..S-8 対応版 + DE-0449 修正。

v0.1.2 (Claude Code 実装。ハーネス層修正権限の Taka 裁定 2026-07-20 に基づく):
- EMPTY_RESPONSE 時に last_test を上書きせず追記する。空応答は修正情報を
  持たないため、上書きすると直前の pytest 出力が失われ収束性を損なう
  (Claude Code の監査所見(b))。連続空応答での無制限増大は末尾一致で抑止。
- 2DER システムコード(status_views.py 等)は D-2 のまま。本変更はハーネス層のみ。

v0.1.1 (DE-0449 由来、Claude web 起票):
- call_vllm が message.content の型を検査。None/空は EmptyModelResponse。
  → terminal にせず反復を消費してフィードバック(reasoning で max_tokens
    到達した場合に run 全体を潰さないため)。恒久的に空なら BUDGET_EXHAUSTED。
- max_tokens を packet から可変化(既定 16384)。
- model_fn 注入経路で非文字列応答が来た場合も MODEL_PROTOCOL_ERROR。

v0 からの構造変更(GPT 監査裁定):
S-1  implementation_files / immutable_test_files を分離。テストは packet 側
     資材(workspace 外)から毎反復コピーし、テスト実行後に sha 照合。
     変化 = TEST_TAMPERED で即時終了。モデルがテストパスへ書こうとしたら
     REJECTED_SCOPE_VIOLATION。
S-2  sandbox 前提検査: WORKCELL_SANDBOXED=1(systemd ユニットが付与)が
     無ければ起動拒否(--unsafe-dev で明示バイパス、ログに残る)。
     ※ runner は sandbox の「存在検査」までしか出来ない。防止は OS 層。
S-3  毎 run 新規 workspace(run_id 配下)。既存・非空は WORKSPACE_CONTAMINATED。
S-4  テスト前後 + 終了時に disk から再読込した sha を記録。
     テスト中の実装自己変更 = IMPL_MODIFIED_DURING_TEST。
S-5  run log は workspace 外(run_dir 直下)。run_id / seq / prev_hash /
     record_hash の hash chain。runner_sha256 / packet_sha256 を先頭記録。
     ※ chain は改竄の「検出」であり「防止」ではない(同一 UID なら書ける)。
S-6  厳格 parse: file block 外の残余テキスト・重複 path・必須ファイル未提出は
     FORMAT/INCOMPLETE 違反として反復消費(フィードバック)。
S-7  全例外を terminal status へ変換し、必ず RESULT_PACKET を書く。
     (KeyboardInterrupt / SIGKILL までは保証しない)
S-8  攻撃テストを test_runner.py に追加。

claim ceiling(GPT 裁定採用):
  DETERMINISTIC_GENERATE_WRITE_TEST_RETRY_LOOP_DEMONSTRATED_ON_UNIT_FIXTURES
禁止: DRIFT_STRUCTURALLY_IMPOSSIBLE / FIXED_TESTS_ENFORCED(OS層なしでは
  「改変検出付き」まで)/ ALLOWED_FILES_ONLY_WRITABLE /
  APPEND_ONLY_RUN_LOG_PROVEN / QWEN_IMPLEMENTATION_PATH_READY
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# R2-1: 記録機構は M1 成果物の EventStore。runner.py と同ディレクトリに
# 配備されている emit_api.py を使う(sys.path に自ディレクトリを足すのは
# unit 経由でも pytest 経由でも同じ経路で解決させるため)。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emit_api import EmitError, EventStore  # noqa: E402

FILE_BLOCK = re.compile(
    r"<file\s+path=\"(?P<path>[^\"]+)\">\n(?P<body>.*?)\n</file>", re.DOTALL
)

SYSTEM_PROMPT = """あなたは実装 worker である。以下を厳守せよ。
1. 出力は <file path="相対パス">…</file> ブロックのみ。ブロック外に一切の文字を出力しない。
2. implementation_files に列挙されたパスのみ出力できる。テストファイルは出力禁止。
3. spec の合格条件(同梱テスト)を満たす完全なファイル内容を出力する。全文であること。
4. spec にない機能を追加しない。
5. テスト結果について何も主張しない(結果は runner が実測する)。"""

TERMINAL = {"PASSED", "BUDGET_EXHAUSTED", "REJECTED_SCOPE_VIOLATION",
            "TEST_TAMPERED", "IMPL_MODIFIED_DURING_TEST", "PACKET_INVALID",
            "WORKSPACE_CONTAMINATED", "MODEL_TIMEOUT", "MODEL_PROTOCOL_ERROR",
            "TEST_TIMEOUT", "TEST_EXEC_ERROR", "SANDBOX_NOT_VERIFIED",
            "INTERNAL_RUNNER_ERROR",
            "LEDGER_UNAVAILABLE"}   # R2-11: 記録できない実行はしない

REQUIRED_KEYS = {"task_id", "spec_file", "implementation_files",
                 "immutable_test_files", "test_cmd", "max_iterations"}


def sha256b(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256f(path: Path) -> str:
    return sha256b(path.read_bytes())


def confined(root: Path, rel: str) -> Path:
    p = (root / rel).resolve()
    if not str(p).startswith(str(root.resolve()) + os.sep):
        raise ValueError(f"path escape rejected: {rel}")
    return p


# --- R2: 記録機構は EventStore(emit_api.py / M1 の Qwen 成果物)------------
# v0.1 の自前 ChainLog / verify_chain は廃止した。workcell はもはや独自の
# 記録機構を持たず、2DER の帳簿機構(registry 封入 / retention_class /
# sealed field / chain)の上に乗る。emit_api.py は D-2 対象につき改変禁止。

# R2-6 / R2-7: registry は runner の外の pin 可能な artifact。ここに
# ハードコードすると retention_class の変更がコード差分になり、LG-R3
# (クラス変更は承認済み policy 経由のみ)に反する。runner は読むだけ。
REGISTRY_PATH = Path(os.environ.get("WORKCELL_EVENT_REGISTRY",
                                    "/srv/workcell/registry/workcell_events.json"))


class RegistryUnavailable(Exception):
    """registry が読めない/壊れている/必要な kind を欠く。R2-11 で停止する。"""


def load_registry(path: Path | str | None = None) -> dict:
    """registry ファイルから kinds を読む。疑わしければ例外(fail-closed)。"""
    p = Path(path) if path else REGISTRY_PATH
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise RegistryUnavailable(f"registry unreadable at {p}: {e!r}")
    if not isinstance(obj, dict) or not isinstance(obj.get("kinds"), dict):
        raise RegistryUnavailable(f"registry malformed at {p}: no 'kinds' object")
    kinds = obj["kinds"]
    missing = sorted(k for k in REQUIRED_KINDS if k not in kinds)
    if missing:
        raise RegistryUnavailable(f"registry missing kinds: {missing}")
    bad = sorted(k for k in REQUIRED_KINDS
                 if not isinstance(kinds[k], dict)
                 or not kinds[k].get("retention_class"))
    if bad:
        raise RegistryUnavailable(f"registry entries without retention_class: {bad}")
    return kinds

# v0.1 の呼び出し名 -> (registry kind, kind_detail)。制御フローを触らずに
# 記録機構だけを差し替えるため(NG-3)、呼び出し側の語彙は据え置き、
# ここで 2DER 語彙へ写像する。
_KIND_MAP = {
    "PACKET_START":         ("WORKCELL_PACKET_START", None),
    "SANDBOX_CHECK":        ("WORKCELL_SANDBOX_CHECK", None),
    "MODEL_REPLY":          ("WORKCELL_MODEL_REPLY", None),
    "EMPTY_RESPONSE":       ("WORKCELL_EMPTY_RESPONSE", None),
    "FILE_WRITTEN":         ("WORKCELL_FILE_WRITTEN", None),
    "PRE_TEST_SNAPSHOT":    ("WORKCELL_PRE_TEST_SNAPSHOT", None),
    "TEST_RUN":             ("WORKCELL_TEST_RUN", None),
    "MODEL_ERROR":          ("WORKCELL_MODEL_ERROR", None),
    "RESULT_PACKET":        ("WORKCELL_RESULT_PACKET", None),
    # kind_detail は略記でなく v0.1 の呼び出し名そのものを残す。5種の違反が
    # WORKCELL_VIOLATION 1 kind に畳まれるため、どの違反だったかは記録側に
    # 保持されないと失われる(略記だと元の語彙へ戻せない)。
    "SCOPE_VIOLATION":      ("WORKCELL_VIOLATION", "SCOPE_VIOLATION"),
    "FORMAT_VIOLATION":     ("WORKCELL_VIOLATION", "FORMAT_VIOLATION"),
    "INCOMPLETE_SUBMISSION": ("WORKCELL_VIOLATION", "INCOMPLETE_SUBMISSION"),
    "TEST_TAMPERED":        ("WORKCELL_VIOLATION", "TEST_TAMPERED"),
    "IMPL_MODIFIED":        ("WORKCELL_VIOLATION", "IMPL_MODIFIED"),
}

# runner が emit しうる kind。registry がこれを欠けば記帳できないので停止する。
REQUIRED_KINDS = sorted({kind for kind, _ in _KIND_MAP.values()})


class _EventLog:
    """呼び出し側の append(kind, **fields) を EventStore.emit へ写像する薄い層。

    runner 固有フィールドは**すべて payload の中**に置く(R2-4)。
    retention_class は registry からのみ決まるので emit には渡さない(R2-7)。
    lane は常に "real"(R2-5)。
    """

    def __init__(self, store, run_id: str):
        self.store, self.run_id = store, run_id

    def append(self, kind: str, **fields):
        mapped = _KIND_MAP.get(kind)
        if mapped is None:                      # registry 外は握りつぶさない
            raise EmitError(f"unmapped event kind: {kind}")
        registry_kind, kind_detail = mapped
        payload = {"run_id": self.run_id, **fields}
        if kind_detail is not None:
            payload["kind_detail"] = kind_detail
        return self.store.emit(registry_kind, payload, lane="real")


class EmptyModelResponse(Exception):
    """HTTP/JSON の形は正しいが本文が空(reasoning で max_tokens 到達等)。
    プロトコル異常ではないので terminal にせず、反復を消費して再試行する。"""

    def __init__(self, finish_reason: str, note: str = "", reasoning: str = ""):
        super().__init__(f"empty content (finish_reason={finish_reason}) {note}".strip())
        self.finish_reason = finish_reason
        self.reasoning = reasoning          # v0.2.1: 予算を消費した思考本文(DE-0461)


def _reasoning_of(message: dict) -> str:
    """思考本文。フィールド名は serving 実装で割れる(vLLM 0.23 は 'reasoning'、
    他は 'reasoning_content')ので両方見る。DE-0461: 片方だけ見て『観測不能』と
    誤断定した実害があるため、ここで一元化する。"""
    for k in ("reasoning", "reasoning_content"):
        v = message.get(k)
        if isinstance(v, str) and v:
            return v
    return ""


def call_vllm(endpoint: str, model: str, messages: list[dict],
              timeout: int = 600, max_tokens: int = 16384,
              enable_thinking: bool | None = None) -> tuple[str, str]:
    """戻り: (content, reasoning)。v0.2.1 で reasoning を捨てなくなった(DE-0461)。

    v0.2.2(DE-0464): enable_thinking=False で思考を停止させる。暴走時の思考は
    与えた予算をちょうど使い切る(思考字数÷予算が予算に依らず 3.2〜3.9 で一定)ため、
    予算側では制御できない。None のときは何も渡さず serving 既定に従う。
    """
    payload = {"model": model, "messages": messages,
               "temperature": 0.2, "max_tokens": max_tokens}
    if enable_thinking is not None:
        payload["chat_template_kwargs"] = {"enable_thinking": bool(enable_thinking)}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(endpoint, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    choice = data["choices"][0]          # 形が違えば例外 → MODEL_PROTOCOL_ERROR
    reasoning = _reasoning_of(choice["message"])
    content = choice["message"].get("content")
    if not isinstance(content, str) or not content.strip():
        note = ""
        if reasoning:
            note = ("(reasoning present: budget likely exhausted before output; "
                    f"reasoning_chars={len(reasoning)})")
        raise EmptyModelResponse(str(choice.get("finish_reason")), note,
                                 reasoning=reasoning)
    return content, reasoning


def parse_strict(text: str, impl_allowed: set[str]) -> dict[str, str]:
    """厳格 parse。戻り: files。例外:
    PermissionError = スコープ違反(terminal相当) / ValueError = 形式違反(反復消費)"""
    out: dict[str, str] = {}
    spans = []
    for m in FILE_BLOCK.finditer(text):
        path, body = m.group("path"), m.group("body")
        spans.append(m.span())
        if path not in impl_allowed:
            raise PermissionError(f"disallowed path: {path}")
        if path in out:
            raise ValueError(f"duplicate file block: {path}")
        out[path] = body
    residue = text
    for a, b in reversed(spans):
        residue = residue[:a] + residue[b:]
    if residue.strip():
        raise ValueError(f"prose outside file blocks: {residue.strip()[:80]!r}")
    if not out:
        raise ValueError("no file blocks in reply")
    return out


def sandbox_check(unsafe_dev: bool) -> tuple[bool, str]:
    if os.environ.get("WORKCELL_SANDBOXED") == "1":
        return True, "env WORKCELL_SANDBOXED=1"
    if unsafe_dev:
        return True, "SANDBOX_BYPASSED (--unsafe-dev)"
    return False, "sandbox marker absent; refuse to start"


def run_packet(packet: dict, runs_root: Path, model_fn=None,
               unsafe_dev: bool = False, run_id: str | None = None) -> dict:
    run_id = run_id or time.strftime("%Y%m%dT%H%M%SZ-",
                                     time.gmtime()) + secrets.token_hex(4)
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    events_dir = run_dir / "events"
    result: dict = {"task_id": packet.get("task_id", "?"), "run_id": run_id,
                    "status": "INTERNAL_RUNNER_ERROR", "iterations_used": 0,
                    "files": [], "needs_human": True,
                    "events_path": str(events_dir), "chain_ok": None}

    def write_result_json() -> dict:
        (run_dir / "RESULT_PACKET.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    # R2-11: 帳簿が使えないなら packet を実行しない。registry が読めない場合も
    # 壊れた既存 segment(EventStore.__init__ が EmitError)も同じ扱い。
    # モデルは一度も呼ばない。
    try:
        registry = load_registry()
        store = EventStore(events_dir, registry, producer_version="runner-v0.2")
    except Exception as e:
        result.update(status="LEDGER_UNAVAILABLE", needs_human=True,
                      chain_ok=False, detail=repr(e))
        return write_result_json()

    log = _EventLog(store, run_id)

    def finish(status: str, **extra) -> dict:
        result.update(status=status, needs_human=(status != "PASSED"), **extra)
        # R2-9: 正典はイベント、JSON は導出ビュー。まずイベントへ記帳する。
        # events_path / chain_ok は JSON 側の導出フィールドなので payload から外す
        # (chain_ok は下の verify() で初めて確定するため循環も避けられる)。
        log.append("RESULT_PACKET", **{k: v for k, v in result.items()
                                       if k not in ("events_path", "chain_ok")})
        ok, why = store.verify()                                    # R2-10
        result["chain_ok"] = ok
        if not ok:
            result["chain_detail"] = why
        return write_result_json()

    try:
        ok, why = sandbox_check(unsafe_dev)
        log.append("SANDBOX_CHECK", ok=ok, detail=why, uid=os.getuid())
        if not ok:
            return finish("SANDBOX_NOT_VERIFIED", detail=why)

        missing = REQUIRED_KEYS - set(packet)
        if missing:
            return finish("PACKET_INVALID", detail=f"missing keys: {sorted(missing)}")
        impl_files = list(packet["implementation_files"])
        test_files = {rel: Path(src) for rel, src in
                      packet["immutable_test_files"].items()}
        overlap = set(impl_files) & set(test_files)
        if overlap:
            return finish("PACKET_INVALID", detail=f"impl/test overlap: {sorted(overlap)}")
        try:
            spec = Path(packet["spec_file"]).read_text(encoding="utf-8")
            test_manifest = {rel: sha256f(src) for rel, src in test_files.items()}
        except OSError as e:
            return finish("PACKET_INVALID", detail=f"unreadable input: {e}")

        workspace = run_dir / "ws"
        if workspace.exists() and any(workspace.iterdir()):
            return finish("WORKSPACE_CONTAMINATED", detail=str(workspace))
        workspace.mkdir(exist_ok=True)

        log.append("PACKET_START", task_id=packet["task_id"],
                   packet_sha256=sha256b(json.dumps(
                       packet, sort_keys=True, ensure_ascii=False).encode()),
                   runner_sha256=sha256f(Path(__file__)),
                   spec_sha256=sha256b(spec.encode()),
                   implementation_files=impl_files,
                   immutable_test_manifest=test_manifest,
                   max_iterations=int(packet["max_iterations"]))

        files: dict[str, str] = {}
        last_test: str | None = None
        test_timeout = int(packet.get("test_timeout_s", 300))
        # v0.2.3(DE-0467): 同一フィードバック → 同一 reply の不動点を、既往記録の
        # 注入で解く。照合は直前だけでなく **当該 run の全既往反復** に対して行う
        # (周期2以上の不動点も捕まえるため)。reply_sha256 -> {iteration, outcome}。
        seen_replies: dict[str, dict] = {}
        dup_record: str | None = None

        for it in range(1, int(packet["max_iterations"]) + 1):
            result["iterations_used"] = it
            parts = [f"# SPEC\n{spec}",
                     f"# implementation_files\n{json.dumps(impl_files)}"]
            if files:
                parts.append("# 現在の実装ファイル\n" + "\n".join(
                    f'<file path="{p}">\n{c}\n</file>' for p, c in files.items()))
            if last_test is not None:
                parts.append(f"# 直前のフィードバック(修正せよ)\n{last_test}")
            if dup_record is not None:      # v0.2.3: 訓戒でなく記録のみを注入する
                parts.append(f"# 既往記録(事実)\n{dup_record}")
            user = "\n\n".join(parts)
            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user}]
            reasoning = ""
            try:
                reply = (model_fn(messages) if model_fn is not None else
                         call_vllm(packet["endpoint"], packet["model"], messages,
                                   max_tokens=int(packet.get("max_tokens", 16384)),
                                   enable_thinking=packet.get("enable_thinking")))
                if isinstance(reply, tuple):        # call_vllm 経路(content, reasoning)
                    reply, reasoning = reply
            except EmptyModelResponse as e:
                # 形は正しいが本文が空。terminal にせず反復を消費して促す。
                # v0.1.2: 直前のフィードバック(pytest 出力)を破棄せず追記する。
                # 空応答は「何を直すか」の情報を持たないため、上書きすると
                # 実装者は次反復で修正対象を見失う。連続空応答で無制限に
                # 伸びないよう、同一注記が末尾にある場合は重ねない。
                # v0.2.1(DE-0461): 予算を消費した思考を本文ごと残す。空応答は
                # 他に証拠が無いため、ここで捨てると「何に尽きたか」が失われる。
                log.append("EMPTY_RESPONSE", iteration=it, detail=str(e),
                           finish_reason=e.finish_reason,
                           reasoning_chars=len(e.reasoning),
                           reasoning_sha256=sha256b(e.reasoning.encode()),
                           reasoning=e.reasoning)
                note = ("(応答本文が空だった。思考を短く切り上げ、"
                        "<file>ブロックのみを直ちに出力せよ)")
                if last_test is None:
                    last_test = note
                elif not last_test.endswith(note):
                    last_test = f"{last_test}\n{note}"
                continue
            except (TimeoutError, urllib.error.URLError) as e:
                log.append("MODEL_ERROR", iteration=it, detail=str(e))
                return finish("MODEL_TIMEOUT", detail=str(e))
            except Exception as e:
                log.append("MODEL_ERROR", iteration=it, detail=str(e))
                return finish("MODEL_PROTOCOL_ERROR", detail=str(e))
            if not isinstance(reply, str):   # model_fn 注入経路の防御
                log.append("MODEL_ERROR", iteration=it, detail="non-str reply")
                return finish("MODEL_PROTOCOL_ERROR", detail="non-str reply")
            reply_sha = sha256b(reply.encode())
            prior = seen_replies.get(reply_sha)      # v0.2.3: 全既往反復との照合
            log.append("MODEL_REPLY", iteration=it,
                       prompt_sha256=sha256b(user.encode()),
                       reply_sha256=reply_sha, reply=reply,
                       # v0.2.1(DE-0461): 思考は本文でなく長さと sha で残す
                       # (SUMMARIZABLE。予算配分を後から検算できれば足りる)。
                       reasoning_chars=len(reasoning),
                       reasoning_sha256=sha256b(reasoning.encode()),
                       # v0.2.3: 新 kind を作らず payload で表す(registry 不変)。
                       duplicate_of_iteration=(prior["iteration"] if prior else None))
            if prior is not None:
                dup_record = (f"この応答(reply sha256={reply_sha})は iteration "
                              f"{prior['iteration']} で提出済みであり、{prior['outcome']}。")
            else:
                dup_record = None
            # 重複反復も iteration を消費する(採点スキップの最適化は入れない)。
            entry = seen_replies.setdefault(
                reply_sha, {"iteration": it, "outcome": "結果は記録されていない"})

            try:
                new_files = parse_strict(reply, set(impl_files))
            except PermissionError as e:
                log.append("SCOPE_VIOLATION", iteration=it, detail=str(e))
                return finish("REJECTED_SCOPE_VIOLATION", detail=str(e))
            except ValueError as e:
                log.append("FORMAT_VIOLATION", iteration=it, detail=str(e))
                last_test = f"(形式違反: {e}。<file>ブロックのみで再出力せよ)"
                entry["outcome"] = f"形式違反 {e} で失敗した"
                continue

            files.update(new_files)
            for rel, content in new_files.items():
                p = confined(workspace, rel)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                log.append("FILE_WRITTEN", iteration=it, path=rel,
                           sha256=sha256b(content.encode()))
            absent = [p for p in impl_files if not (workspace / p).exists()]
            if absent:
                log.append("INCOMPLETE_SUBMISSION", iteration=it, missing=absent)
                last_test = f"(未提出の必須ファイル: {absent}。全て出力せよ)"
                entry["outcome"] = f"必須ファイル {absent} 未提出で失敗した"
                continue

            # 採点表を毎回、部屋の外の原本から敷き直す
            for rel, src in test_files.items():
                dst = confined(workspace, rel)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            pre = {p: sha256f(workspace / p) for p in
                   list(impl_files) + list(test_files)}
            log.append("PRE_TEST_SNAPSHOT", iteration=it, sha256=pre)

            for pyc in workspace.rglob("__pycache__"):
                shutil.rmtree(pyc, ignore_errors=True)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            try:
                proc = subprocess.run(packet["test_cmd"], cwd=workspace,
                                      capture_output=True, text=True,
                                      timeout=test_timeout, env=env)
            # NOTE(R2 registry gap): v0.1 はここで TEST_ERROR を記録していたが、
            # R2-6 の registry 10 種に該当 kind が無い。registry は spec 固定
            # (R2-7)なので勝手に 11 種目を作らず、iteration を detail に畳んで
            # WORKCELL_RESULT_PACKET(PERMANENT)へ残す。R2.1 で要裁定。
            except subprocess.TimeoutExpired:
                return finish("TEST_TIMEOUT",
                              detail=f"iteration {it}: >{test_timeout}s")
            except OSError as e:
                return finish("TEST_EXEC_ERROR", detail=f"iteration {it}: {e}")
            tail = (proc.stdout + proc.stderr)[-4000:]

            post = {p: sha256f(workspace / p) if (workspace / p).exists()
                    else "DELETED" for p in pre}
            log.append("TEST_RUN", iteration=it, exit_code=proc.returncode,
                       output_tail=tail, post_sha256=post)
            tampered = [p for p in test_files if post[p] != pre[p]]
            if tampered:
                # R2-6: tamper / impl_modified も WORKCELL_VIOLATION に含める
                # (v0.1 では専用イベントを残していなかった)。
                log.append("TEST_TAMPERED", iteration=it,
                           detail=f"tests changed: {tampered}")
                return finish("TEST_TAMPERED", detail=f"tests changed: {tampered}")
            self_mod = [p for p in impl_files if post[p] != pre[p]]
            if self_mod:
                log.append("IMPL_MODIFIED", iteration=it,
                           detail=f"impl changed during test: {self_mod}")
                return finish("IMPL_MODIFIED_DURING_TEST",
                              detail=f"impl changed during test: {self_mod}")

            if proc.returncode == 0:
                final = [{"path": p, "final_disk_sha256": sha256f(workspace / p),
                          "model_reply_sha256": sha256b(files[p].encode())}
                         for p in sorted(impl_files)]
                return finish("PASSED", files=final)
            # v0.2.3: 既往記録に残す事実。pytest の FAILED 行があればそれを、
            # 無ければ終了コードを記録する(散文の訓戒は入れない)。
            # 色つき出力(環境依存)でも拾えるよう ANSI を落としてから照合する。
            plain = re.sub(r"\x1b\[[0-9;]*m", "", tail)
            failed = [ln.strip() for ln in plain.splitlines()
                      if ln.lstrip().startswith("FAILED ")]
            entry["outcome"] = (f"テストが {failed[-1].strip()} で失敗した" if failed
                                else f"テストが exit={proc.returncode} で失敗した")
            last_test = tail

        return finish("BUDGET_EXHAUSTED")
    except Exception as e:  # S-7 catch-all (R2-12: 維持)
        # NOTE(R2 registry gap): INTERNAL_ERROR も registry 10 種に無い。
        # 勝手に kind を増やさず、終端は WORKCELL_RESULT_PACKET に記録する。
        # finish 自体が失敗する場合(帳簿が死んでいる)は JSON だけ残す。
        try:
            return finish("INTERNAL_RUNNER_ERROR", detail=repr(e))
        except Exception as e2:
            result.update(status="INTERNAL_RUNNER_ERROR", needs_human=True,
                          detail=f"{e!r}; ledger unavailable: {e2!r}",
                          chain_ok=False)
            return write_result_json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("packet")
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--unsafe-dev", action="store_true")
    a = ap.parse_args()
    packet = json.loads(Path(a.packet).read_text(encoding="utf-8"))
    r = run_packet(packet, Path(a.runs_root), unsafe_dev=a.unsafe_dev)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r["status"] == "PASSED" else 1)


if __name__ == "__main__":
    main()
