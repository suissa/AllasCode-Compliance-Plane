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
