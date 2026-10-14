from __future__ import annotations

from pathlib import Path

from compliance.runtime import ComplianceEngine, EvaluationContext, Policy, Result


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "compliance-registry.yaml"


def compliant_evaluator(intent, context):
    return Result.COMPLIANT, "test evaluator accepted evidence", ("evidence://test/1",)


def test_mandatory_intent_cannot_be_disabled_by_company_policy() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    context = EvaluationContext("tenant-123", "between_actions")
    engine.set_policy("company_default", "tenant-123", Policy(enabled=False))
    decision = engine.evaluate("PRIV-001", context, compliant_evaluator)
    assert decision is not None
    assert decision.result is Result.COMPLIANT
    assert decision.mandatory is True
    assert "attempted disable ignored" in decision.reason


def test_mandatory_control_can_be_not_applicable_after_assessment() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    context = EvaluationContext("tenant-bar", "between_actions", attributes={"company_profile": "MEI"})
    decision = engine.evaluate(
        "FISC-011",
        context,
        compliant_evaluator,
        applicability=lambda intent, ctx: False,
    )
    assert decision is not None
    assert decision.result is Result.NOT_APPLICABLE
    assert decision.mandatory is True


def test_unknown_applicability_returns_indeterminate() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    context = EvaluationContext("tenant-health", "between_actions")
    decision = engine.evaluate(
        "FISC-011",
        context,
        compliant_evaluator,
        applicability=lambda intent, ctx: None,
    )
    assert decision is not None
    assert decision.result is Result.INDETERMINATE


def test_non_mandatory_intent_can_be_disabled() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    context = EvaluationContext("tenant-123", "on_ingress")
    engine.set_policy("company_default", "tenant-123", Policy(enabled=False))
    assert engine.evaluate("SEC-001", context, compliant_evaluator) is None


def test_policy_precedence_prefers_operation_override() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    context = EvaluationContext("tenant-123", "between_actions")
    engine.set_policy("intent_policy", "PRIV-001", Policy(enforcement="warn"))
    engine.set_policy("operation_override", "op-7", Policy(enforcement="block"))
    decision = engine.evaluate(
        "PRIV-001", context, compliant_evaluator, operation_id="op-7"
    )
    assert decision is not None
    assert decision.enforcement == "block"
