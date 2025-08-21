from trace.core.state import GlobalState
from trace.core.verifier import ConservationVerifier


def test_verifier_new_resource_violation():
    # Baseline with only 'tokens'
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    state.add_entity("bob", {"tokens": 5})

    verifier = ConservationVerifier()
    verifier.set_baseline(state)

    # Introduce a new resource type 'gems'
    mutated = state.clone()
    mutated.get_entity("alice").set_resource("gems", 1)

    violations = verifier.verify(mutated)
    assert any(v.violation_type == "new_resource" for v in violations)

