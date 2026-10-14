from __future__ import annotations

from pathlib import Path

from compliance.interceptor import ComplianceInterceptor, Enforcement
from compliance.runtime import ComplianceEngine, Policy, Result


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "compliance-registry.yaml"


def evaluator(result: Result = Result.COMPLIANT):
    def _evaluate(intent, context):
        return result, f"{result.value} for {intent.id}", (f"evidence://{intent.id}/1",)

    return _evaluate


def resolver(result: Result = Result.COMPLIANT):
    return lambda intent_id: evaluator(result)


def test_interceptor_supports_all_execution_points() -> None:
    points = (
        "on_ingress",
        "before_egress",
        "between_agents",
        "between_actions",
        "scheduled",
        "on_state_change",
    )
    for point in points:
        engine = ComplianceEngine.from_yaml(MANIFEST)
        engine.set_policy("intent_policy", "SEC-001", Policy(execution={point: True}))
        interceptor = ComplianceInterceptor(engine)
        result = interceptor.intercept(
            execution_point=point,
            tenant_id="tenant-1",
            intent_ids=["SEC-001"],
            executor=lambda: "executed",
            evaluator_resolver=resolver(),
        )
        assert result.executed is True
        assert result.value == "executed"
        assert result.findings[0].decision.execution_point == point
        assert interceptor.events[-1].event_type == "compliance.execution_allowed"


def test_block_stops_action_and_emits_audit_event() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    engine.set_policy("intent_policy", "SEC-001", Policy(enforcement="block"))
    interceptor = ComplianceInterceptor(engine)
    executed = []

    result = interceptor.intercept(
        execution_point="between_actions",
        tenant_id="tenant-1",
        intent_ids=["SEC-001"],
        executor=lambda: executed.append(True),
        evaluator_resolver=resolver(Result.NON_COMPLIANT),
        action_id="CreateCustomer",
        agent_id="CustomerComplianceAgent",
        operation_id="op-1",
    )

    assert result.executed is False
    assert result.quarantined is False
    assert executed == []
    assert result.findings[0].decision.enforcement == "block"
    assert interceptor.events[-1].event_type == "compliance.blocked"


def test_quarantine_stops_execution_without_claiming_success() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    engine.set_policy("intent_policy", "SEC-001", Policy(enforcement="quarantine"))
    interceptor = ComplianceInterceptor(engine)

    result = interceptor.intercept(
        execution_point="between_agents",
        tenant_id="tenant-1",
        intent_ids=["SEC-001"],
        executor=lambda: "must-not-run",
        evaluator_resolver=resolver(Result.NON_COMPLIANT),
    )

    assert result.executed is False
    assert result.quarantined is True
    assert result.value is None
    assert interceptor.events[-1].event_type == "compliance.quarantined"


def test_fail_closed_operation_blocks_indeterminate_result() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    interceptor = ComplianceInterceptor(engine)

    result = interceptor.intercept(
        execution_point="before_egress",
        tenant_id="tenant-1",
        intent_ids=["PRIV-001"],
        executor=lambda: "must-not-export",
        evaluator_resolver=resolver(Result.INDETERMINATE),
        operation_class="personal_data_export",
    )

    assert result.executed is False
    assert result.quarantined is False
    assert interceptor.events[-1].event_type == "compliance.blocked"


def test_mandatory_control_remains_active_at_interceptor_boundary() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    engine.set_policy("company_default", "tenant-1", Policy(enabled=False))
    interceptor = ComplianceInterceptor(engine)

    result = interceptor.intercept(
        execution_point="between_actions",
        tenant_id="tenant-1",
        intent_ids=["PRIV-001"],
        executor=lambda: "executed",
        evaluator_resolver=resolver(),
    )

    assert result.executed is True
    assert result.findings[0].decision.mandatory is True
    assert "attempted disable ignored" in result.findings[0].decision.reason


def test_audit_sink_receives_evaluation_and_execution_events() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    received = []
    interceptor = ComplianceInterceptor(engine, audit_sink=received.append)

    interceptor.intercept(
        execution_point="on_ingress",
        tenant_id="tenant-1",
        intent_ids=["SEC-001"],
        executor=lambda: None,
        evaluator_resolver=resolver(),
    )

    assert [event.event_type for event in received] == [
        "compliance.evaluated",
        "compliance.execution_allowed",
    ]
    assert received[0].execution_point == "on_ingress"
    assert received[0].evidence_refs == ("evidence://SEC-001/1",)


def test_warn_allows_execution_but_preserves_finding() -> None:
    engine = ComplianceEngine.from_yaml(MANIFEST)
    engine.set_policy("intent_policy", "SEC-001", Policy(enforcement=Enforcement.WARN))
    interceptor = ComplianceInterceptor(engine)

    result = interceptor.intercept(
        execution_point="between_actions",
        tenant_id="tenant-1",
        intent_ids=["SEC-001"],
        executor=lambda: "executed",
        evaluator_resolver=resolver(Result.NON_COMPLIANT),
    )

    assert result.executed is True
    assert result.findings[0].decision.result is Result.NON_COMPLIANT
    assert interceptor.events[-1].event_type == "compliance.execution_allowed"
