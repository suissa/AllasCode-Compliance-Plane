"""Structured compliance telemetry with trace correlation and PII minimization."""
from __future__ import annotations
import json
import logging
import hashlib
from typing import Any
from .interceptor import ComplianceEvent

logger = logging.getLogger("allascode.compliance")

class JsonEvidenceSink:
    """Emit one JSON evidence record per compliance event to a configured logger."""
    def __init__(self, logger_instance: logging.Logger | None = None) -> None:
        self.logger = logger_instance or logger

    def __call__(self, event: ComplianceEvent) -> None:
        # Explicit allowlist: never serialize arbitrary entity attributes or payloads.
        record: dict[str, Any] = {
            "schema": "allascode.compliance-evidence.v1",
            "event_type": event.event_type,
            "trace_id": event.trace_id,
            "operation_id": event.operation_id,
            "tenant_id": event.tenant_id,
            "execution_point": event.execution_point,
            "intent_id": event.intent_id,
            "result": event.result.value,
            "enforcement": event.enforcement,
            "mandatory": event.mandatory,
            "evidence_ref_hashes": [hashlib.sha256(ref.encode("utf-8")).hexdigest() for ref in event.evidence_refs],
            "action_id": event.action_id,
            "agent_id": event.agent_id,
        }
        self.logger.info(json.dumps(record, sort_keys=True, separators=(",", ":")))
