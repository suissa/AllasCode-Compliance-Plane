# Person entity and LGPD evidence workflow

The `compliance/catalog.py` loader reads `catalog/compliance-definitions.json` at service startup, indexes Agents/Actions/Intents, and validates owner/action references. The large JSON is declarative metadata; it is not a request payload and should not be resent for every operation. The YAML manifest configures runtime defaults and policies. `PersonService` obtains its LGPD Intent IDs from the JSON catalog and verifies that those IDs also exist in the YAML runtime manifest.\n\nThe PersonService is the reference integration boundary for personal data. It is
not a claim that importing this module makes an application legally compliant.
Production compliance requires reviewed, versioned evaluators and evidence from
authorization, purpose, legal-basis, retention, security, processor and data-rights
subsystems.

## Usage

```python
from pathlib import Path
from compliance.person import PersonService, LGPD_INTENTS
from compliance.runtime import ComplianceEngine, Result
from compliance.telemetry import JsonEvidenceSink

engine = ComplianceEngine.from_yaml(Path("catalog/compliance-registry.yaml"))
people = PersonService(engine, audit_sink=JsonEvidenceSink())

# Contract example only: production references must point to real evidence.
evidence = {
    intent_id: {
        "result": Result.COMPLIANT.value,
        "evidence_refs": [f"evidence://privacy-case/CASE-123/{intent_id}"],
        "reason": "Verified by the corresponding versioned control",
    }
    for intent_id in LGPD_INTENTS
}
person = people.create(
    tenant_id="tenant-123", name="Example Person",
    purposes=("account_management",), legal_basis="contract",
    evidence=evidence, trace_id="trace-req-123",
)
```

Do not mechanically mark every control compliant in production. Each evidence
reference must resolve to a real, access-controlled evidence record. Missing or
malformed evidence becomes indeterminate and Person operations are blocked.
not_applicable must be assessed and supported by evidence.

## Execution and evidence

- create checks PRIV-001 through PRIV-020 at on_ingress.
- get checks them at before_egress.
- delete checks them at between_actions.
- The interceptor emits compliance.evaluated per control and a terminal event
  such as compliance.blocked or compliance.execution_allowed.
- trace_id correlates events for one request; operation_id, rule version, intent
  ID, result and hashes of evidence references provide audit context.
- JsonEvidenceSink emits structured JSON logs and excludes names, phone numbers,
  email addresses, raw attributes, free-text reasons, or raw evidence references.
- Keep logs access-controlled and append-only where appropriate; define retention
  and protect evidence references against unauthorized resolution.

The 20 Intents are the control inventory, not twenty universal legal obligations
applicable identically in every situation. Evaluators must distinguish compliant,
non_compliant, indeterminate and not_applicable according to facts, applicable
law and current guidance. LGPD-2026-10 is a correlation label in this starter
implementation, not a claim that every rule has been legally reviewed as of that date.
