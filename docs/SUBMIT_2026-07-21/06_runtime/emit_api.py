import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone


class EmitError(Exception):
    pass


class EventStore:
    PROTECTED_KEYS = {
        "kind", "lane", "retention_class", "segment_id",
        "sequence_in_segment", "previous_event_hash", "previous_segment_root",
        "schema_version", "producer_version", "ts", "record_hash"
    }
    VALID_LANES = {"real", "null_n", "null_b", "control"}
    SEGMENT_ID = "seg-000001"
    GENESIS_HASH = "0" * 64
    ZEROES_ROOT = "0" * 64

    def __init__(self, store_dir, registry: dict, producer_version: str):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.store_dir / "seg-000001.jsonl"
        self.registry = registry
        self.producer_version = producer_version

        self.sequence_in_segment = 0
        self.previous_event_hash = self.GENESIS_HASH

        if self.file_path.exists():
            self._load_existing()

    def _load_existing(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise EmitError("Invalid JSON in existing segment")
            if record.get("record_hash") != self._compute_hash(record):
                raise EmitError("Chain integrity check failed in existing segment")
            self.previous_event_hash = record["record_hash"]
            self.sequence_in_segment = record["sequence_in_segment"] + 1

    def _compute_hash(self, record: dict) -> str:
        record_without_hash = {k: v for k, v in record.items() if k != "record_hash"}
        return hashlib.sha256(
            json.dumps(record_without_hash, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

    def emit(self, kind: str, payload: dict, lane: str = "real") -> dict:
        if kind not in self.registry:
            raise EmitError(f"Kind '{kind}' not in registry")
        if lane not in self.VALID_LANES:
            raise EmitError(f"Invalid lane '{lane}'")
        if not isinstance(payload, dict):
            raise EmitError("Payload must be a dict")
        try:
            json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError):
            raise EmitError("Payload is not JSON serializable")
        if any(k in payload for k in self.PROTECTED_KEYS):
            raise EmitError("Payload contains protected keys")

        record = {
            "schema_version": "1",
            "segment_id": self.SEGMENT_ID,
            "sequence_in_segment": self.sequence_in_segment,
            "previous_event_hash": self.previous_event_hash,
            "previous_segment_root": self.ZEROES_ROOT,
            "kind": kind,
            "lane": lane,
            "retention_class": self.registry[kind]["retention_class"],
            "producer_version": self.producer_version,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "payload": payload,
            "record_hash": ""
        }

        record["record_hash"] = self._compute_hash(record)

        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        self.previous_event_hash = record["record_hash"]
        self.sequence_in_segment += 1

        return record

    def verify(self) -> tuple[bool, str]:
        if not self.file_path.exists():
            return (True, "ok")

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            return (True, "ok")

        expected_seq = 0
        expected_prev_hash = self.GENESIS_HASH

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                return (False, f"Invalid JSON at line {i+1}")

            if record.get("sequence_in_segment") != expected_seq:
                return (False, f"Sequence mismatch at line {i+1}: expected {expected_seq}, got {record.get('sequence_in_segment')}")

            if record.get("previous_event_hash") != expected_prev_hash:
                return (False, f"Previous hash mismatch at line {i+1}")

            computed = self._compute_hash(record)
            if record.get("record_hash") != computed:
                return (False, f"Record hash mismatch at line {i+1}")

            expected_prev_hash = computed
            expected_seq += 1

        return (True, "ok")