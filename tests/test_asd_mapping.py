"""
Unit tests for src/ingestion/asd_mapping.py.
"""
from src.ingestion.asd_mapping import map_state_code_to_observed_items

def test_map_initial_state():
    # Only base plate is placed
    observed = map_state_code_to_observed_items("10000000000")
    assert observed == []

def test_map_front_chassis_installed():
    # Base, front chassis, front chassis pin
    observed = map_state_code_to_observed_items("11100000000")
    ids = {item["item_id"] for item in observed}
    assert ids == {"check-001"}

def test_map_chassis_and_pins_installed():
    # Base, front chassis + pin, rear chassis, rear pins
    observed = map_state_code_to_observed_items("11110110000")
    ids = {item["item_id"] for item in observed}
    assert ids == {"check-001", "check-002", "check-003"}

def test_map_clean_build_procedure_a():
    # Complete Procedure A assembly. check-004 (wing beam) and check-006 (pulley) are
    # NOT verifiable by this model's ontology, so they are intentionally absent here.
    observed = map_state_code_to_observed_items("11110111111")
    ids = {item["item_id"] for item in observed}
    assert ids == {"check-001", "check-002", "check-003", "check-005"}
    assert "check-004" not in ids and "check-006" not in ids

def test_map_missing_wheel():
    # Front wheels assembly is missing (digit 9 = 0)
    observed = map_state_code_to_observed_items("11110111101")
    ids = {item["item_id"] for item in observed}
    assert ids == {"check-001", "check-002", "check-003"}
    assert "check-005" not in ids

def test_map_procedure_b_upgrade():
    # Uses short rear chassis (digit 4 = 1) instead of long rear chassis (digit 3 = 1)
    observed = map_state_code_to_observed_items("11101111111")
    ids = {item["item_id"] for item in observed}
    assert ids == {"check-001", "check-002", "check-003", "check-005"}

def test_map_invalid_states():
    assert map_state_code_to_observed_items("error_state") == []
    assert map_state_code_to_observed_items("background") == []
    assert map_state_code_to_observed_items("111") == []
    assert map_state_code_to_observed_items("") == []
    assert map_state_code_to_observed_items(None) == []
