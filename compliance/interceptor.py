"""Execution-point interceptor for Agents and Actions.

The interceptor is deliberately transport/runtime agnostic. A host runtime wraps
Agent or Action execution with ``intercept`` and supplies trusted evaluators.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Iterable, Mapping

from .runtime import ComplianceEngine, Decision, EvaluationContext, Result


class Enforcement(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    AUDIT_ONLY = "audit_only"


@dataclass(frozen=True)
class ComplianceFinding:
    decision: Decision
    action_id: str | None
    agent_id: str | None
    operation_id: str | None


@dataclass(frozen=True)
class InterceptionResult:
    executed: bool
    quarantined: bool
    value: Any = None
    findings: tuple[ComplianceFinding, ...] = ()


@dataclass(frozen=True)
class ComplianceEvent:
    event_type: str
    execution_point: str
    tenant_id: str
    intent_id: str
    result: Result
    enforcement: str
    mandatory: bool
    evidence_refs: tuple[str, ...]
    operation_id: str | None = None
    action_id: str | None = None
    agent_id: str | None = None
    reason: str = ""
    trace_id: str | None = None


AuditSink = Callable[[ComplianceEvent], None]
EvaluatorResolver = Callable[[str], Callable[..., tuple[Result, str, tuple[str, ...]]]]
ApplicabilityResolver = Callable[[str], Callable[..., bool | None] | None]
Executor = Callable[[], Any]


@dataclass
class ComplianceInterceptor:
    """Reusable boundary around every Agent/Action execution point.

    ``execution_point`` is explicit, so the same interceptor can be installed at
    ingress, egress, Agent-to-Agent, Action-to-Action, scheduled, and state-change
    boundaries without coupling compliance to a particular message bus.
    """

    engine: ComplianceEngine
    audit_sink: AuditSink | None = None
    _events: list[ComplianceEvent] = field(default_factory=list, init=False)

    def _emit(self, event: ComplianceEvent) -> None:
        self._events.append(event)
        if self.audit_sink is not None:
            self.audit_sink(event)

    @property
    def events(self) -> tuple[ComplianceEvent, ...]:
        return tuple(self._events)

    @staticmethod
    def _should_stop(decision: Decision, operation_class: str | None) -> tuple[bool, bool]:
        """Return ``(block, quarantine)`` for a decision.

        Indeterminate is not treated as compliant. In addition to explicit policy
        enforcement, operation classes declared fail-closed by the manifest are
        blocked until a definitive result is available.
        """
        if decision.result in (Result.COMPLIANT, Result.NOT_APPLICABLE):
            return False, False
        if decision.enforcement == Enforcement.BLOCK:
            return True, False
        if decision.enforcement == Enforcement.QUARANTINE:
            return False, True
        return False, False

    def _fail_closed(self, operation_class: str | None, result: Result) -> bool:
        if result not in (Result.NON_COMPLIANT, Result.INDETERMINATE):
            return False
        fail_closed_for = set(self.engine.defaults.get("fail_closed_for", []))
        return operation_class in fail_closed_for

    def intercept(
        self,
        *,
        execution_point: str,
        tenant_id: str,
        intent_ids: Iterable[str],
        executor: Executor,
        evaluator_resolver: EvaluatorResolver,
        applicability_resolver: ApplicabilityResolver | None = None,
        action_id: str | None = None,
        agent_id: str | None = None,
        operation_id: str | None = None,
        operation_class: str | None = None,
        entity_type: str | None = None,
        attributes: Mapping[str, Any] | None = None,
        rule_versions: Mapping[str, str] | None = None,
        trace_id: str | None = None,
    ) -> InterceptionResult:
        """Evaluate all declared Intents before executing the wrapped operation."""
        context = EvaluationContext(
            tenant_id=tenant_id,
            execution_point=execution_point,
            entity_type=entity_type,
            attributes=attributes or {},
        )
        findings: list[ComplianceFinding] = []

        for intent_id in intent_ids:
            evaluator = evaluator_resolver(intent_id)
            applicability = applicability_resolver(intent_id) if applicability_resolver else None
            decision = self.engine.evaluate(
                intent_id,
                context,
                evaluator,
                applicability,
                action_id=action_id,
                agent_id=agent_id,
                operation_id=operation_id,
                rule_version=(rule_versions or {}).get(intent_id),
            )
            if decision is None:
                continue

            finding = ComplianceFinding(decision, action_id, agent_id, operation_id)
            findings.append(finding)
            self._emit(ComplianceEvent(
                event_type="compliance.evaluated",
                execution_point=execution_point,
                tenant_id=tenant_id,
                intent_id=intent_id,
                result=decision.result,
                enforcement=decision.enforcement,
                mandatory=decision.mandatory,
                evidence_refs=decision.evidence_refs,
                operation_id=operation_id,
                action_id=action_id,
                agent_id=agent_id,
                reason=decision.reason,
                trace_id=trace_id,
            ))

            block, quarantine = self._should_stop(decision, operation_class)
            if self._fail_closed(operation_class, decision.result):
                block = True

            if block:
                self._emit(ComplianceEvent(
                    event_type="compliance.blocked",
                    execution_point=execution_point,
                    tenant_id=tenant_id,
                    intent_id=intent_id,
                    result=decision.result,
                    enforcement=Enforcement.BLOCK,
                    mandatory=decision.mandatory,
                    evidence_refs=decision.evidence_refs,
                    operation_id=operation_id,
                    action_id=action_id,
                    agent_id=agent_id,
                    reason=decision.reason,
                    trace_id=trace_id,
                ))
                return InterceptionResult(False, False, findings=tuple(findings))

            if quarantine:
                self._emit(ComplianceEvent(
                    event_type="compliance.quarantined",
                    execution_point=execution_point,
                    tenant_id=tenant_id,
                    intent_id=intent_id,
                    result=decision.result,
                    enforcement=Enforcement.QUARANTINE,
                    mandatory=decision.mandatory,
                    evidence_refs=decision.evidence_refs,
                    operation_id=operation_id,
                    action_id=action_id,
                    agent_id=agent_id,
                    reason=decision.reason,
                ))
                return InterceptionResult(False, True, findings=tuple(findings))

        value = executor()
        self._emit(ComplianceEvent(
            event_type="compliance.execution_allowed",
            execution_point=execution_point,
            tenant_id=tenant_id,
            intent_id="__boundary__",
            result=Result.COMPLIANT,
            enforcement=Enforcement.ALLOW,
            mandatory=False,
            evidence_refs=(),
            operation_id=operation_id,
            action_id=action_id,
            agent_id=agent_id,
            reason="All enabled compliance checks permitted execution.",
            trace_id=trace_id,
        ))
        return InterceptionResult(True, False, value=value, findings=tuple(findings))
