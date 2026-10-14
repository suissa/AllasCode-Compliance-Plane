"""Person entity with mandatory LGPD checks at every data-access boundary.

This is an integration baseline, not a claim of automatic legal compliance:
trusted, versioned privacy evaluators must provide evidence for each applicable
control before an operation is allowed.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from .interceptor import ComplianceInterceptor, InterceptionResult
from .runtime import ComplianceEngine, EvaluationContext, Policy, Result
from .telemetry import JsonEvidenceSink

LGPD_INTENTS = tuple(f"PRIV-{number:03d}" for number in range(1, 21))

@dataclass(frozen=True)
class Person:
    """Minimal person record; collect only fields needed by the use case."""
    person_id: str
    tenant_id: str
    name: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    phone: str | None = None
    email: str | None = None
    purposes: tuple[str, ...] = ()
    legal_basis: str | None = None
    retention_until: str | None = None

    def __post_init__(self) -> None:
        if not self.person_id.strip() or not self.tenant_id.strip():
            raise ValueError("person_id and tenant_id are required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.purposes:
            raise ValueError("at least one explicit processing purpose is required")
        if not self.legal_basis:
            raise ValueError("legal_basis must identify the assessed LGPD legal basis")

class ComplianceDenied(PermissionError):
    def __init__(self, result: InterceptionResult) -> None:
        super().__init__("Person operation denied by LGPD compliance controls")
        self.result = result

class PersonService:
    """Example persistence boundary; replace the in-memory store with a repository."""
    def __init__(self, engine: ComplianceEngine, *, audit_sink: JsonEvidenceSink | None = None) -> None:
        self._people: dict[tuple[str, str], Person] = {}
        self.interceptor = ComplianceInterceptor(engine, audit_sink=audit_sink)
        # Person operations must not silently downgrade privacy checks to warn/audit.
        for intent_id in LGPD_INTENTS:
            engine.set_policy("intent_policy", intent_id, Policy(enforcement="block"))

    @staticmethod
    def _evaluator_resolver(evidence: Mapping[str, Any]):
        def resolve(intent_id: str):
            def evaluate(intent, context: EvaluationContext):
                item = evidence.get(intent_id)
                if not isinstance(item, Mapping):
                    return Result.INDETERMINATE, "No trusted privacy evidence was supplied for this control.", ()
                try:
                    result = Result(item.get("result"))
                except (ValueError, TypeError):
                    return Result.INDETERMINATE, "Evidence result is missing or invalid.", ()
                refs = item.get("evidence_refs", ())
                if not isinstance(refs, (list, tuple)) or any(
                    not isinstance(ref, str) or not ref.startswith("evidence://") for ref in refs
                ):
                    return Result.INDETERMINATE, "Evidence references are invalid.", ()
                if result in (Result.COMPLIANT, Result.NOT_APPLICABLE) and not refs:
                    return Result.INDETERMINATE, "A positive decision requires evidence references.", ()
                reason = str(item.get("reason", "Privacy control evaluated from supplied evidence."))
                return result, reason, tuple(refs)
            return evaluate
        return resolve

    def _run(self, *, person: Person, operation: str, execution_point: str,
             evidence: Mapping[str, Any], executor, trace_id: str | None = None) -> InterceptionResult:
        trace_id = trace_id or str(uuid4())
        result = self.interceptor.intercept(
            execution_point=execution_point, tenant_id=person.tenant_id,
            intent_ids=LGPD_INTENTS, executor=executor,
            evaluator_resolver=self._evaluator_resolver(evidence),
            action_id=f"Person.{operation}", agent_id="LGPDComplianceAgent",
            operation_id=f"person:{operation}:{uuid4()}",
            operation_class="personal_data_export" if operation == "export" else None,
            entity_type="Person",
            # Only non-PII metadata enters evaluation context and telemetry.
            attributes={
                "entity_type": "Person", "operation": operation,
                "data_categories": ["personal_data"], "purposes": list(person.purposes),
                "legal_basis_declared": bool(person.legal_basis),
                "retention_declared": bool(person.retention_until),
            },
            rule_versions={intent_id: "LGPD-2026-10" for intent_id in LGPD_INTENTS},
            trace_id=trace_id,
        )
        if not result.executed:
            raise ComplianceDenied(result)
        return result

    def create(self, *, tenant_id: str, name: str, purposes: tuple[str, ...],
               legal_basis: str, evidence: Mapping[str, Any], phone: str | None = None,
               email: str | None = None, retention_until: str | None = None,
               trace_id: str | None = None) -> Person:
        person = Person(person_id=str(uuid4()), tenant_id=tenant_id, name=name,
                        phone=phone, email=email, purposes=purposes,
                        legal_basis=legal_basis, retention_until=retention_until)
        self._run(person=person, operation="create", execution_point="on_ingress",
                  evidence=evidence, executor=lambda: self._people.__setitem__(
                      (tenant_id, person.person_id), person), trace_id=trace_id)
        return person

    def get(self, *, tenant_id: str, person_id: str, evidence: Mapping[str, Any],
            trace_id: str | None = None) -> Person:
        # Composite tenant key prevents cross-tenant retrieval.
        person = self._people[(tenant_id, person_id)]
        self._run(person=person, operation="read", execution_point="before_egress",
                  evidence=evidence, executor=lambda: person, trace_id=trace_id)
        return person

    def delete(self, *, tenant_id: str, person_id: str, evidence: Mapping[str, Any],
               trace_id: str | None = None) -> None:
        person = self._people[(tenant_id, person_id)]
        self._run(person=person, operation="delete", execution_point="between_actions",
                  evidence=evidence, executor=lambda: self._people.pop(
                      (tenant_id, person.person_id), None), trace_id=trace_id)
