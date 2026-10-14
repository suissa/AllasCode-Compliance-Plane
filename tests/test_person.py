from __future__ import annotations
import json
import logging
from pathlib import Path
import pytest
from compliance.person import ComplianceDenied, LGPD_INTENTS, PersonService
from compliance.runtime import ComplianceEngine, Result
from compliance.telemetry import JsonEvidenceSink

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "compliance-registry.yaml"

def complete_evidence(result: str = "compliant"):
    return {intent_id: {"result": result,
        "evidence_refs": [f"evidence://privacy/{intent_id}/test"],
        "reason": "Test evidence reviewed"} for intent_id in LGPD_INTENTS}

def test_person_create_requires_all_lgpd_controls_and_emits_trace(caplog):
    service = PersonService(ComplianceEngine.from_yaml(MANIFEST), audit_sink=JsonEvidenceSink())
    caplog.set_level(logging.INFO, logger="allascode.compliance")
    person = service.create(tenant_id="tenant-a", name="Ada Example",
        purposes=("account_management",), legal_basis="contract",
        evidence=complete_evidence(), trace_id="trace-test-1")
    records = [json.loads(record.message) for record in caplog.records]
    evaluations = [item for item in records if item["event_type"] == "compliance.evaluated"]
    assert len(evaluations) == len(LGPD_INTENTS)
    assert {item["intent_id"] for item in evaluations} == set(LGPD_INTENTS)
    assert all(item["trace_id"] == "trace-test-1" for item in records)
    assert all("Ada Example" not in record.message for record in caplog.records)
    assert person.tenant_id == "tenant-a"

def test_person_create_blocks_when_lgpd_evidence_is_missing():
    service = PersonService(ComplianceEngine.from_yaml(MANIFEST))
    with pytest.raises(ComplianceDenied) as error:
        service.create(tenant_id="tenant-a", name="Ada Example",
            purposes=("account_management",), legal_basis="contract",
            evidence={}, trace_id="trace-denied")
    assert error.value.result.executed is False
    assert error.value.result.findings[0].decision.result is Result.INDETERMINATE
    assert service.interceptor.events[-1].event_type == "compliance.blocked"
    assert service.interceptor.events[-1].trace_id == "trace-denied"

def test_person_tenant_boundary_does_not_return_another_tenant_record():
    service = PersonService(ComplianceEngine.from_yaml(MANIFEST))
    person = service.create(tenant_id="tenant-a", name="Ada Example",
        purposes=("account_management",), legal_basis="contract", evidence=complete_evidence())
    with pytest.raises(KeyError):
        service.get(tenant_id="tenant-b", person_id=person.person_id, evidence=complete_evidence())

def test_person_rejects_missing_purpose_and_legal_basis():
    service = PersonService(ComplianceEngine.from_yaml(MANIFEST))
    with pytest.raises(ValueError):
        service.create(tenant_id="tenant-a", name="Ada Example", purposes=(),
            legal_basis="contract", evidence=complete_evidence())
    with pytest.raises(ValueError):
        service.create(tenant_id="tenant-a", name="Ada Example",
            purposes=("account_management",), legal_basis="", evidence=complete_evidence())
