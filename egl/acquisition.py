"""Phase 1b — Semantic Acquisition Boundary(docs/phase-1b-acquisition-boundary.md §6-13,§18)。

flow: (RD 提案 plan) → code が immutable LegIntent 実体化 → Adapter → AcquisitionRun
(transport_status + content_status, adapter が付す) → SearchResultSnapshot(実行した探索を記録)
→ content_status=OBSERVED なら RawObservation + Source Qualification(observed_source_kind)
→ Policy Matcher(required vs observed)。

受入 ACQ-1(RD は leg を COMPLETED にできない=満足は primitive から計算)/ ACQ-3(plan_id・
required_source_kind は immutable LegIntent から解決)/ ACQ-3b(required≠observed、AB-1)/
ACQ-4(transport 失敗は coverage 不可)/ ACQ-4b(content≠OBSERVED は evidence-eligible でない、AB-2)/
ACQ-4c(source kind でなく search operation の実行+snapshot、AB-3)。
"""
import hashlib
from . import core, source_policy as SP, etb as ETB

# §8 AB-2: 通信の成否と、取れた中身が観測に足るか を分ける。
TRANSPORT_STATUSES = {"SUCCESS", "NOT_RETRIEVABLE", "ACCESS_DENIED", "AUTH_REQUIRED", "RATE_LIMITED",
                      "ROBOTS_DISALLOWED", "NOT_FOUND_REMOTE", "TIMEOUT", "NETWORK_ERROR",
                      "PARSER_FAILED", "UNSUPPORTED_CONTENT", "ADAPTER_ERROR"}
CONTENT_STATUSES = {"OBSERVED", "CHALLENGE_PAGE", "AUTH_WALL", "PLACEHOLDER", "EMPTY",
                    "UNEXPECTED_CONTENT", "UNSUPPORTED"}

# §6 first slice adapters(実 fetch は adapter 実装が担う。runner は adapter_result を受ける形にして
# テストを hermetic に保つ = adapter が status を付す事実は変えず、ネットワーク非決定性をテストから排除)。
ADAPTERS = {"ACQ_GITHUB", "ACQ_HTTP_STATIC", "ACQ_MANUAL"}


def content_hash(raw_bytes):
    if raw_bytes is None:
        return None
    if isinstance(raw_bytes, str):
        raw_bytes = raw_bytes.encode("utf-8")
    return "sha256:" + hashlib.sha256(raw_bytes).hexdigest()


# ---------- §7 LegIntent(immutable, code が実体化)----------
def mk_leg_intent(run, plan_id, task_id, required_source_kind, target_locator, adapter_class,
                  source_policy_id, source_policy_version, expected_entity=None, purpose="",
                  search_method=None, query=None, scope_locator=None, revision=None,
                  pagination_policy=None):
    """RD は plan を提案してよいが leg completed を宣言できない。code がここで immutable な
    LegIntent を作る。required_source_kind は AB-1: *要求* であって観測事実ではない。"""
    if required_source_kind not in SP.SOURCE_KINDS:
        raise ValueError(f"unknown required_source_kind {required_source_kind!r}")
    if adapter_class not in ADAPTERS:
        raise ValueError(f"unknown adapter_class {adapter_class!r}")
    return core.append_event(run, "CREATE", "LegIntent", None, {
        "id": core.SELF, "leg_id": core.SELF, "plan_id": plan_id, "task_id": task_id,
        "required_source_kind": required_source_kind,        # AB-1: 要求(観測事実でない)
        "target_locator": target_locator, "adapter_class": adapter_class,
        "expected_entity": expected_entity, "purpose": purpose,
        "source_policy_id": source_policy_id, "source_policy_version": source_policy_version,  # ACQ-8
        "search_method": search_method, "query": query or [],                # AB-3: どう探したか
        "scope_locator": scope_locator, "revision": revision,
        "pagination_policy": pagination_policy,
    }, new_prefix="LEG")


# ---------- §6 acquire: adapter dispatch(実 fetch or injected/manual)----------
def acquire(run, leg_id, injected=None):
    """leg の adapter_class に応じて実 adapter を呼ぶ(or injected を使う)。
    injected: テスト/ACQ_MANUAL 用に adapter_result を直接与える(hermetic)。
    実 adapter(ACQ_HTTP_STATIC/ACQ_GITHUB)は egl.adapters が transport/content status を付す。"""
    leg = core.get_state(leg_id)
    if not leg:
        raise ValueError(f"unknown leg {leg_id}")
    if injected is not None:
        result = injected
    elif leg["adapter_class"] == "ACQ_MANUAL":
        raise ValueError("ACQ_MANUAL は injected content を要求する(手動投入)")
    else:
        from . import adapters
        result = adapters.fetch(leg)
    return run_acquisition(run, leg_id, result)


# ---------- §8 AcquisitionRun(adapter が terminal status を付す)----------
def run_acquisition(run, leg_id, adapter_result):
    """adapter_result = adapter が付けた終端状態。RD は付けない(ACQ-1)。
    plan/required は AcquisitionRun payload でなく immutable LegIntent から解決(ACQ-3)。"""
    leg = core.get_state(leg_id)
    if not leg:
        raise ValueError(f"unknown leg {leg_id}")
    ts = adapter_result.get("transport_status")
    cs = adapter_result.get("content_status")
    if ts not in TRANSPORT_STATUSES:
        raise ValueError(f"AB-2: bad transport_status {ts!r}")
    if ts == "SUCCESS" and cs not in CONTENT_STATUSES:
        raise ValueError(f"AB-2: SUCCESS transport requires content_status in {sorted(CONTENT_STATUSES)}")
    raw = adapter_result.get("raw_bytes")
    taint = ETB.scan_content(raw) if raw else []       # ETB-4: 取得時に data を走査
    return core.append_event(run, "CREATE", "AcquisitionRun", None, {
        "id": core.SELF, "acquisition_run_id": core.SELF, "leg_id": leg_id,
        "adapter": leg["adapter_class"], "adapter_version": adapter_result.get("adapter_version", "0"),
        "target_locator": leg["target_locator"],                # locator も LegIntent 由来
        "transport_status": ts, "content_status": cs,           # AB-2: adapter が付す
        "http_status": adapter_result.get("http_status"),
        "content_type": adapter_result.get("content_type"),
        "raw_content_hash": content_hash(raw),
        "taint_flags": taint,                                   # ETB-4/5: 以降へ伝播
        "adapter_provenance": adapter_result.get("adapter_provenance", {}),
    }, new_prefix="ARUN")


# ---------- §9/§15 SearchResultSnapshot(AB-3: 実行した探索操作を記録)----------
def mk_search_result_snapshot(run, leg_id, acquisition_run_id, result_count, result_refs=None):
    """『どう探したか』を LegIntent の search_* から写し、返った result set(0 件含む)を記録。
    JREV-0005 Probe D: snapshot は実 AcquisitionRun に **束縛**する(未束縛だと『searched の self-report』に
    退化する)。acquisition_run_id は同一 leg の run でなければならない=coverage(ACQ-4c)は『この leg の
    実取得を伴う search operation を実行し snapshot を保存した』で見る。"""
    leg = core.get_state(leg_id)
    if not leg:
        raise ValueError(f"unknown leg {leg_id}")
    arun = core.get_state(acquisition_run_id)
    if not arun or arun.get("leg_id") != leg_id:
        raise ValueError(f"ACQ-4c: snapshot は同一 leg の AcquisitionRun に束縛必須 "
                         f"(got acquisition_run leg={arun.get('leg_id') if arun else None} != {leg_id})")
    return core.append_event(run, "CREATE", "SearchResultSnapshot", None, {
        "id": core.SELF, "snapshot_id": core.SELF, "leg_id": leg_id, "executed": True,
        "acquisition_run_id": acquisition_run_id,               # Probe D: 実取得への束縛
        "search_method": leg.get("search_method"), "query": leg.get("query"),
        "scope_locator": leg.get("scope_locator"), "revision": leg.get("revision"),
        "pagination_policy": leg.get("pagination_policy"),
        "result_count": result_count, "result_refs": result_refs or [],
    }, new_prefix="SNAP")


# ---------- §10/§11 evidence-eligible Observation + Source Qualification ----------
def emit_observation_if_eligible(run, acquisition_run_id):
    """AB-2: content_status=OBSERVED の時のみ evidence-eligible な RawObservation を作り、
    その source を Source Qualification で observed_source_kind 評価(AB-1)。
    非 OBSERVED(challenge/auth wall 等)は None を返す(Observation も Source も作らない)。"""
    arun = core.get_state(acquisition_run_id)
    if not arun:
        raise ValueError(f"unknown acquisition_run {acquisition_run_id}")
    if arun.get("transport_status") != "SUCCESS" or arun.get("content_status") != "OBSERVED":
        return None                                          # ACQ-4b: evidence-eligible でない
    observed_kind, entity = SP.qualify_locator(arun.get("target_locator"), arun.get("adapter"),
                                               arun.get("adapter_provenance"))
    src = core.append_event(run, "CREATE", "Source", None, {
        "id": core.SELF, "source_id": core.SELF, "name": arun.get("target_locator"),
        "locator": arun.get("target_locator"),
        "source_class": SP.source_class_for(observed_kind),  # PRIMARY/SECONDARY(UNKNOWN は非 PRIMARY)
        "observed_source_kind": observed_kind, "entity": entity,   # AB-1: 取得 provenance からの評価
        "qualification": "CODE_CANDIDATE", "qualified_from_acquisition": acquisition_run_id,
    }, new_prefix="SRC")
    obs = core.append_event(run, "CREATE", "RawObservation", None, {
        "id": core.SELF, "observation_id": core.SELF, "acquisition_run_id": acquisition_run_id,
        "source_id": src, "raw_content_hash": arun.get("raw_content_hash"),
        "raw_blob_ref": f"blob://{arun.get('raw_content_hash')}" if arun.get("raw_content_hash") else None,
        "content_type": arun.get("content_type"), "normalization_status": "NOT_NORMALIZED",
        "taint_flags": arun.get("taint_flags", []),          # ETB-5: acquisition から継承
        "evidence_eligible": True,
    }, new_prefix="OBS")
    return {"observation_id": obs, "source_id": src, "observed_source_kind": observed_kind}


# ---------- §13 Extraction Run(Raw Observation → NormalizedObservation → Evidence Fragment)----------
# 正しく fetch ≠ 正しく fragment 選択 ゆえ Acquisition Run とは *別 Run*。取得境界(Phase 1b)と
# 既存 curation spine(Phase 1a)の橋: NormalizedObservation の observation_kind を acquired Source の
# observed_source_kind から provenance-assisted で導出(§12)。以降は既存 gate1..gate5 が変更なしで動く。
def extract_fragment(run, raw_observation_id, blocks, block_index, excerpt,
                     section_heading="", mentions=None, extractor_model="claude",
                     extractor_version="0", prompt_version="ext-1a.0"):
    from . import pipeline as P
    rawobs = core.get_state(raw_observation_id)
    if not rawobs or not rawobs.get("evidence_eligible"):
        raise ValueError(f"extract: {raw_observation_id} は evidence-eligible な RawObservation でない(ACQ-4b)")
    src = core.get_state(rawobs["source_id"])
    obs_kind = SP.observation_kind_for(src.get("observed_source_kind"))    # §12 provenance-assisted
    # ETB-5/EF-4: RawObservation の taint を継承し、抽出 block/excerpt の再走査分を加算
    taint = ETB.merge_taint(rawobs.get("taint_flags", []),
                            ETB.scan_content("\n".join(str(b) for b in (blocks or []))),
                            ETB.scan_content(excerpt))
    nobs = core.append_event(run, "CREATE", "NormalizedObservation", None, {
        "id": core.SELF, "norm_obs_id": core.SELF, "raw_observation_id": raw_observation_id,
        "source_id": rawobs["source_id"], "section_heading": section_heading,
        "observation_kind": obs_kind, "blocks": blocks, "normalized_by_run": run,
        "taint_flags": taint, "extractor_model": extractor_model, "extractor_version": extractor_version,
        "prompt_version": prompt_version,           # §13 extraction lineage
    }, new_prefix="NOBS")
    frag = P.mk_fragment(run, nobs, block_index, excerpt, mentions, taint=taint)   # ETB-5: fragment へ
    return {"fragment_id": frag, "norm_obs_id": nobs, "observation_kind": obs_kind,
            "source_id": rawobs["source_id"], "taint_flags": taint}


# ---------- §18 leg requirement 評価(ACQ-1/3/3b/4b/4c を1関数で強制)----------
def evaluate_leg_requirement(con, leg_id):
    """leg の required_source_kind が満たされたか。**満足は RD の宣言でなく primitive から計算**(ACQ-1)。
    required は immutable LegIntent から読む(AcquisitionRun payload からでない=ACQ-3)。
    条件を全て満たした時のみ satisfied:
      ACQ-4c: 実行済み SearchResultSnapshot が在る
      ACQ-4b: content_status=OBSERVED な evidence-eligible RawObservation が在る
      ACQ-3b: その Observation の Source の observed_source_kind が required に policy 一致(AB-1)"""
    leg = core.get(con, leg_id)
    if not leg:
        return {"leg_id": leg_id, "satisfied": False, "reasons": ["unknown leg"]}
    required = leg.get("required_source_kind")               # ACQ-3: LegIntent が根
    reasons = []

    # ACQ-4c(Probe D 修正): snapshot は同一 leg の実 AcquisitionRun に束縛されていなければならない
    # (未束縛の executed=True は『searched の self-report』ゆえ coverage を満たさせない)。
    snaps = []
    for s in core.by_type(con, "SearchResultSnapshot"):
        if s.get("leg_id") != leg_id or not s.get("executed"):
            continue
        ar = core.get(con, s.get("acquisition_run_id"))
        if ar and ar.get("leg_id") == leg_id:
            snaps.append(s)
    if not snaps:
        reasons.append("ACQ-4c: no executed SearchResultSnapshot bound to this leg's AcquisitionRun")

    obs = [o for o in core.by_type(con, "RawObservation")
           if o.get("evidence_eligible")
           and core.get(con, o.get("acquisition_run_id"))
           and core.get(con, o["acquisition_run_id"]).get("leg_id") == leg_id]
    if not obs:
        reasons.append("ACQ-4b: no evidence-eligible (content=OBSERVED) observation for leg")

    matched = []
    for o in obs:
        src = core.get(con, o.get("source_id"))
        ok = src.get("observed_source_kind") if src else None
        if SP.policy_match(required, ok):
            matched.append(ok)
    if obs and not matched:
        observed = [core.get(con, o.get("source_id")).get("observed_source_kind")
                    for o in obs if core.get(con, o.get("source_id"))]
        reasons.append(f"ACQ-3b: observed_source_kind {observed} != required {required} "
                       "(acquisition succeeded but requirement UNSATISFIED)")

    return {"leg_id": leg_id, "required_source_kind": required,
            "matched_observed_kinds": matched, "satisfied": not reasons, "reasons": reasons}
