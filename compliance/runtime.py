"""Small, deterministic compliance-policy runtime.

This module evaluates declared controls; it does not itself interpret legislation.
Legal applicability and rule evaluation must be supplied by trusted, versioned adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml


class Result(StrEnum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    INDETERMINATE = "indeterminate"
    NOT_APPLICABLE = "not_applicable"


EXECUTION_POINTS = frozenset({
    "on_ingress", "before_egress", "between_agents",
    "between_actions", "scheduled", "on_state_change",
})
ENFORCEMENT_MODES = frozenset({"block", "quarantine", "warn", "audit_only"})
PRECEDENCE = ("operation_override", "action_policy", "agent_policy", "intent_policy", "company_default")


@dataclass(frozen=True)
class IntentDefinition:
    id: str
    name: str
    mandatory: bool
    user_can_disable: bool
    conditional: bool = False
    default_points: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "IntentDefinition":
        intent = cls(
            id=str(item["id"]),
            name=str(item["name"]),
            mandatory=bool(item["mandatory"]),
            user_can_disable=bool(item["user_can_disable"]),
            conditional=bool(item.get("conditional", False)),
            default_points=frozenset(item.get("default_points", [])),
        )
        if intent.mandatory and intent.user_can_disable:
            raise ValueError(f"{intent.id}: mandatory intents cannot be user-disableable")
        invalid = intent.default_points - EXECUTION_POINTS
        if invalid:
            raise ValueError(f"{intent.id}: unsupported execution points: {sorted(invalid)}")
        return intent


@dataclass(frozen=True)
class Policy:
    enabled: bool | None = None
    enforcement: str | None = None
    execution: Mapping[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.enforcement is not None and self.enforcement not in ENFORCEMENT_MODES:
            raise ValueError(f"unsupported enforcement mode: {self.enforcement}")
        unknown = set(self.execution) - EXECUTION_POINTS
        if unknown:
            raise ValueError(f"unsupported execution points: {sorted(unknown)}")


@dataclass(frozen=True)
class EvaluationContext:
    tenant_id: str
    execution_point: str
    entity_type: str | None = None
    jurisdiction: str = "BR"
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.execution_point not in EXECUTION_POINTS:
            raise ValueError(f"unsupported execution point: {self.execution_point}")


@dataclass(frozen=True)
class Decision:
    intent_id: str
    result: Result
    enforcement: str
    tenant_id: str
    execution_point: str
    mandatory: bool
    rule_version: str | None
    reason: str
    evidence_refs: tuple[str, ...] = ()


Applicability = Callable[[IntentDefinition, EvaluationContext], bool | None]
Evaluator = Callable[[IntentDefinition, EvaluationContext], tuple[Result, str, tuple[str, ...]]]


class ComplianceEngine:
    """Policy precedence and mandatory-control guardrail for one loaded manifest."""

    def __init__(self, manifest: Mapping[str, Any]) -> None:
        self.defaults = manifest["defaults"]
        self.intents = {
            item["id"]: IntentDefinition.from_mapping(item)
            for item in manifest["intents"]
        }
        self.policies: dict[str, dict[str, Policy]] = {}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ComplianceEngine":
        with Path(path).open(encoding="utf-8") as stream:
            manifest = yaml.safe_load(stream)
        if not isinstance(manifest, dict):
            raise ValueError("compliance manifest must be a mapping")
        return cls(manifest)

    def set_policy(self, level: str, key: str, policy: Policy) -> None:
        if level not in PRECEDENCE:
            raise ValueError(f"unsupported policy level: {level}")
        self.policies.setdefault(level, {})[key] = policy

    def _resolve(self, intent: IntentDefinition, context: EvaluationContext,
                 action_id: str | None, agent_id: str | None,
                 operation_id: str | None) -> tuple[bool, str, bool]:
        keys = {
            "operation_override": operation_id,
            "action_policy": action_id,
            "agent_policy": agent_id,
            "intent_policy": intent.id,
            "company_default": context.tenant_id,
        }
        chosen: Policy | None = None
        for level in PRECEDENCE:
            key = keys[level]
            if key is not None and key in self.policies.get(level, {}):
                chosen = self.policies[level][key]
                break

        point_enabled = context.execution_point in intent.default_points
        enabled = point_enabled
        enforcement = str(self.defaults["enforcement"])
        if chosen is not None:
            if context.execution_point in chosen.execution:
                enabled = chosen.execution[context.execution_point]
            if chosen.enabled is not None:
                enabled = chosen.enabled
            if chosen.enforcement is not None:
                enforcement = chosen.enforcement

        # Mandatory means the check itself cannot be disabled by tenant policy.
        # Applicability is still evaluated separately; mandatory != universally applicable.
        forced_on = intent.mandatory and not enabled
        if forced_on:
            enabled = True
        return enabled, enforcement, forced_on

    def evaluate(
        self,
        intent_id: str,
        context: EvaluationContext,
        evaluator: Evaluator,
        applicability: Applicability | None = None,
        *,
        action_id: str | None = None,
        agent_id: str | None = None,
        operation_id: str | None = None,
        rule_version: str | None = None,
    ) -> Decision | None:
        try:
            intent = self.intents[intent_id]
        except KeyError as exc:
            raise KeyError(f"intent not registered: {intent_id}") from exc

        enabled, enforcement, forced_on = self._resolve(
            intent, context, action_id, agent_id, operation_id
        )
        if not enabled:
            return None

        forced_note = (
            "Mandatory control: attempted disable ignored; applicability remains independently evaluated. "
            if forced_on else ""
        )
        if applicability is not None:
            applies = applicability(intent, context)
            if applies is False:
                return Decision(
                    intent.id, Result.NOT_APPLICABLE, enforcement, context.tenant_id,
                    context.execution_point, intent.mandatory, rule_version,
                    forced_note + "Applicability predicate established that this rule does not apply.",
                )
            if applies is None:
                return Decision(
                    intent.id, Result.INDETERMINATE, enforcement, context.tenant_id,
                    context.execution_point, intent.mandatory, rule_version,
                    forced_note + "Applicability could not be established from available evidence.",
                )

        result, reason, evidence_refs = evaluator(intent, context)
        if not isinstance(result, Result):
            raise TypeError("evaluator must return a Result enum value")
        return Decision(
            intent.id, result, enforcement, context.tenant_id, context.execution_point,
            intent.mandatory, rule_version, forced_note + reason, tuple(evidence_refs),
        )
