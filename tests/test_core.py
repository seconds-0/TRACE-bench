from trace.core.state import EntityState, GlobalState
from trace.core.actions import TransferAction
from trace.core.verifier import ConservationVerifier


def test_entity_state():
    entity = EntityState("alice")
    entity.set_resource("tokens", 5)
    assert entity.get_resource("tokens") == 5

    entity.modify_resource("tokens", -2)
    assert entity.get_resource("tokens") == 3


def test_transfer_action():
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    state.add_entity("bob", {"tokens": 3})

    action = TransferAction(
        turn=1,
        description="Alice gives Bob 2 tokens",
        from_entity="alice",
        to_entity="bob",
        resource_type="tokens",
        amount=2,
    )

    new_state = action.apply(state)
    assert new_state.get_entity("alice").get_resource("tokens") == 3
    assert new_state.get_entity("bob").get_resource("tokens") == 5


def test_transfer_missing_entity_raises():
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    # 'carol' does not exist
    action = TransferAction(1, "bad", "alice", "carol", "tokens", 1)
    try:
        action.apply(state)
    except ValueError as e:
        assert "Entity not found" in str(e)
    else:
        raise AssertionError("Expected ValueError for missing entity")


def test_transfer_negative_amount_raises():
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    state.add_entity("bob", {"tokens": 0})
    action = TransferAction(1, "bad", "alice", "bob", "tokens", -1)
    try:
        action.apply(state)
    except ValueError as e:
        assert "negative" in str(e)
    else:
        raise AssertionError("Expected ValueError for negative transfer amount")


def test_conservation():
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    state.add_entity("bob", {"tokens": 3})

    verifier = ConservationVerifier()
    verifier.set_baseline(state)

    # Valid transfer
    action = TransferAction(1, "transfer", "alice", "bob", "tokens", 2)
    new_state = action.apply(state)
    violations = verifier.verify(new_state)
    assert len(violations) == 0

    # Invalid state (tokens created)
    bad_state = new_state.clone()
    bad_state.get_entity("alice").set_resource("tokens", 10)
    violations = verifier.verify(bad_state)
    assert len(violations) == 1
    assert violations[0].violation_type == "conservation"
