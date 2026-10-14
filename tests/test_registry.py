from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "catalog" / "compliance-registry.yaml"
SCHEMA_PATH = ROOT / "schemas" / "compliance-registry.schema.json"


def load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)
    assert isinstance(value, dict), "registry root must be a YAML mapping"
    return value


def load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict), "schema root must be a JSON object"
    return value


def test_registry_matches_json_schema() -> None:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(load_registry()),
        key=lambda error: list(error.absolute_path),
    )
    assert not errors, "\n".join(
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in errors
    )


def test_intent_ids_and_names_are_unique() -> None:
    intents = load_registry()["intents"]
    ids = [intent["id"] for intent in intents]
    names = [intent["name"] for intent in intents]
    assert len(ids) == len(set(ids)), "duplicate Intent IDs found"
    assert len(names) == len(set(names)), "duplicate Intent names found"


def test_default_points_are_declared_execution_points() -> None:
    registry = load_registry()
    allowed = set(registry["execution_points"])
    for intent in registry["intents"]:
        assert set(intent.get("default_points", [])).issubset(allowed), intent["id"]


def test_all_intents_have_category_and_sequence_id() -> None:
    registry = load_registry()
    assert registry["intents"]
    for intent in registry["intents"]:
        category, number = intent["id"].split("-", maxsplit=1)
        assert category.isalpha() and category.isupper(), intent["id"]
        assert len(number) == 3 and number.isdigit(), intent["id"]


def test_critical_operations_fail_closed_by_default() -> None:
    critical = {
        "personal_data_export",
        "payment",
        "tax_filing",
        "credential_change",
    }
    configured = set(load_registry()["defaults"]["fail_closed_for"])
    assert critical.issubset(configured)


def test_unknown_rules_cannot_be_marked_compliant_by_default() -> None:
    gate = load_registry()["production_gate"]
    assert gate["unknown_rule_result"] == "indeterminate"
    assert gate["never_assume_not_applicable"] is True
    assert gate["require_official_source"] is True
    assert gate["require_effective_from"] is True
    assert gate["require_last_reviewed_at"] is True
    assert gate["require_rule_owner"] is True


def test_catalog_registry_has_no_duplicate_agents_or_actions() -> None:
    registry = load_registry()
    assert len(registry["agents"]) == len(set(registry["agents"]))
    assert len(registry["actions"]) == len(set(registry["actions"]))


def test_mandatory_intents_cannot_be_marked_user_disableable() -> None:
    for intent in load_registry()["intents"]:
        assert intent["mandatory"] is (not intent["user_can_disable"]), intent["id"]
        if intent["mandatory"]:
            assert intent.get("default_points"), intent["id"]


def test_health_receipt_intents_exist_and_are_mandatory() -> None:
    intents = {item["id"]: item for item in load_registry()["intents"]}
    for intent_id in ("FISC-011", "FISC-012", "FISC-013"):
        assert intent_id in intents
        assert intents[intent_id]["mandatory"] is True
        assert intents[intent_id]["user_can_disable"] is False


def test_mandatory_lgpd_and_tax_controls_are_visible_in_manifest() -> None:
    intents = {item["id"]: item for item in load_registry()["intents"]}
    for intent_id in ("PRIV-001", "PRIV-002", "TAX-001", "TAX-005", "TAX-016"):
        assert intents[intent_id]["mandatory"] is True
        assert intents[intent_id]["user_can_disable"] is False


def test_complete_definitions_match_registry_and_schema() -> None:
    definitions_path = ROOT / "catalog" / "compliance-definitions.json"
    definitions_schema_path = ROOT / "schemas" / "compliance-definitions.schema.json"
    with definitions_path.open(encoding="utf-8") as stream:
        definitions = json.load(stream)
    with definitions_schema_path.open(encoding="utf-8") as stream:
        definitions_schema = json.load(stream)

    Draft202012Validator.check_schema(definitions_schema)
    errors = sorted(
        Draft202012Validator(definitions_schema).iter_errors(definitions),
        key=lambda error: list(error.absolute_path),
    )
    assert not errors, "\\n".join(
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in errors
    )

    registry = load_registry()
    assert set(registry["agents"]) == {item["id"] for item in definitions["agents"]}
    assert set(registry["actions"]) == {item["id"] for item in definitions["actions"]}
    assert {item["id"] for item in registry["intents"]} == {item["id"] for item in definitions["intents"]}

    agent_ids = {item["id"] for item in definitions["agents"]}
    action_ids = {item["id"] for item in definitions["actions"]}
    for intent in definitions["intents"]:
        assert intent["owner_agent"] in agent_ids, intent["id"]
        assert set(intent["actions"]).issubset(action_ids), intent["id"]


def test_definition_ids_are_unique() -> None:
    with (ROOT / "catalog" / "compliance-definitions.json").open(encoding="utf-8") as stream:
        definitions = json.load(stream)
    for key in ("agents", "actions", "intents"):
        ids = [item["id"] for item in definitions[key]]
        assert len(ids) == len(set(ids)), f"duplicate {key} IDs"
