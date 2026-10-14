from __future__ import annotations
from pathlib import Path
from compliance.catalog import ComplianceCatalog
from compliance.person import LGPD_INTENTS, PersonService
from compliance.runtime import ComplianceEngine

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "compliance-registry.yaml"
DEFINITIONS = ROOT / "catalog" / "compliance-definitions.json"

def test_large_json_catalog_loads_and_resolves_cross_references():
    catalog = ComplianceCatalog.load(DEFINITIONS)
    assert len(catalog.agents) == 64
    assert len(catalog.actions) == 80
    assert len(catalog.intents) == 137
    assert len(catalog.lgpd_intents) == 20
    assert all(catalog.intent(intent_id)["mandatory"] for intent_id in LGPD_INTENTS)

def test_person_lgpd_intents_are_shared_by_json_and_yaml():
    catalog = ComplianceCatalog.load(DEFINITIONS)
    engine = ComplianceEngine.from_yaml(MANIFEST)
    assert set(catalog.lgpd_intents) <= set(engine.intents)
    service = PersonService(engine, catalog=catalog)
    assert service.lgpd_intents == catalog.lgpd_intents
