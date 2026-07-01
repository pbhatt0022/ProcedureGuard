"""
Deterministic mapping from IndustReal Assembly State Detection (ASD) 11-digit state codes
to ProcedureGuard's 6 checklist items (check-001 to check-006).

State Code order:
  0. base
  1. front chassis
  2. front chassis pin
  3. rear chassis (long)
  4. short rear chassis
  5. front-rear pin
  6. rear-rear pin
  7. front bracket
  8. bracket screw
  9. front wheel assembly
  10. rear wheel assembly
"""

def map_state_code_to_observed_items(state_code: str, confidence: float = 0.9) -> list[dict]:
    """
    Parse an 11-character binary state code and return observed checklist items.
    
    Returns a list of {"item_id": str, "confidence": float}.
    """
    if not isinstance(state_code, str) or len(state_code) != 11:
        # Invalid state code or general 'error_state' / 'background'
        return []

    # Helper to check if a component is correctly installed (character is '1')
    def is_ok(idx: int) -> bool:
        return state_code[idx] == '1'

    observed = []

    # check-001 (STEP 1: Short braces / Front chassis)
    # Complete if front chassis (1) and front chassis pin (2) are assembled.
    if is_ok(1) and is_ok(2):
        observed.append({"item_id": "check-001", "confidence": confidence})

    # check-002 (STEP 2: Long brace / Rear chassis)
    # Complete if long rear chassis (3) OR short rear chassis (4) is assembled.
    if is_ok(3) or is_ok(4):
        observed.append({"item_id": "check-002", "confidence": confidence})

    # check-003 (STEP 3: Secondary fastening / rear pins)
    # Complete if front-rear pin (5) and rear-rear pin (6) are assembled.
    if is_ok(5) and is_ok(6):
        observed.append({"item_id": "check-003", "confidence": confidence})

    # check-004 (STEP 4: Wing beam) and check-006 (STEP 6: Pulley) are NOT emitted:
    # the ASD model's 11-component ontology has no wing-beam class, and the pulley is
    # bundled into the "rear wheel assembly" component (10) so it can't be isolated.
    # Mapping check-004 -> front bracket or check-006 -> rear wheel would falsely confirm
    # the wrong part, so both fall through to honest "Unable to Verify" downstream.

    # check-005 (STEP 5: Wings and wheels / Front wheels)
    # Complete if front wheel assembly (9) is assembled.
    if is_ok(9):
        observed.append({"item_id": "check-005", "confidence": confidence})

    return observed
