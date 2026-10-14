"""Runtime loader for the large declarative compliance definitions catalog."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

DEFAULT_DEFINITIONS_PATH = Path(__file__).resolve().parents[1] / "catalog" / "compliance-definitions.json"

@dataclass(frozen=True)
class ComplianceCatalog:
    version: str
    jurisdiction: str
    agents: Mapping[str, Mapping[str, Any]]
    actions: Mapping[str, Mapping[str, Any]]
    intents: Mapping[str, Mapping[str, Any]]

    @classmethod
    def load(cls, path: str | Path = DEFAULT_DEFINITIONS_PATH) -> "ComplianceCatalog":
        with Path(path).open(encoding="utf-8") as stream:
            raw = json.load(stream)
        if not isinstance(raw, dict):
            raise ValueError("compliance definitions must be a JSON object")
        agents = cls._index(raw, "agents")
        actions = cls._index(raw, "actions")
        intents = cls._index(raw, "intents")
        known_agents, known_actions = set(agents), set(actions)
        for intent_id, intent in intents.items():
            owner = intent.get("owner_agent")
            if owner and owner not in known_agents:
                raise ValueError(f"{intent_id}: unknown owner_agent {owner}")
            missing = set(intent.get("actions", [])) - known_actions
            if missing:
                raise ValueError(f"{intent_id}: unknown actions {sorted(missing)}")
        return cls(
            version=str(raw.get("version", "unknown")),
            jurisdiction=str(raw.get("jurisdiction", "unknown")),
            agents=agents, actions=actions, intents=intents,
        )

    @staticmethod
    def _index(raw: Mapping[str, Any], key: str) -> dict[str, Mapping[str, Any]]:
        items = raw.get(key)
        if not isinstance(items, list):
            raise ValueError(f"catalog field {key!r} must be an array")
        indexed: dict[str, Mapping[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ValueError(f"{key} entries must be objects with string IDs")
            item_id = item["id"]
            if item_id in indexed:
                raise ValueError(f"duplicate {key} ID: {item_id}")
            indexed[item_id] = item
        return indexed

    @property
    def lgpd_intents(self) -> tuple[str, ...]:
        return tuple(sorted(
            intent_id for intent_id, item in self.intents.items()
            if item.get("domain") == "privacy_lgpd" or intent_id.startswith("PRIV-")
        ))

    def intent(self, intent_id: str) -> Mapping[str, Any]:
        try:
            return self.intents[intent_id]
        except KeyError as exc:
            raise KeyError(f"intent not registered in definitions catalog: {intent_id}") from exc
