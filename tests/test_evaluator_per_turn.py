from trace.core.actions import TransferAction
from trace.core.state import GlobalState
from trace.generation.scenario import Scenario
from trace.evaluation.executor import Evaluator
from trace.models.mock import MockModel


def build_simple_scenario() -> Scenario:
    # Build a deterministic scenario: 3 turns, totals 10
    st = GlobalState()
    st.add_entity("entity_0", {"tokens": 5})
    st.add_entity("entity_1", {"tokens": 3})
    st.add_entity("entity_2", {"tokens": 2})
    actions = [
        TransferAction(1, "e0->e1 1", "entity_0", "entity_1", "tokens", 1),
        TransferAction(2, "e2->e1 1", "entity_2", "entity_1", "tokens", 1),
        TransferAction(3, "e1->e2 1", "entity_1", "entity_2", "tokens", 1),
    ]
    return Scenario(initial_state=st, actions=actions, total_resources={"tokens": 10}, seed=123)


def test_per_turn_perfect():
    scenario = build_simple_scenario()
    model = MockModel(mode="per_turn", perfect=True)
    res = Evaluator(model).evaluate(scenario, mode="per_turn")
    assert res.conservation_held is True
    assert res.state_correct is True
    assert res.conservation_accuracy == 1.0
    assert res.state_accuracy == 1.0
    assert all(x == 1.0 for x in res.conservation_accuracy_per_turn)
    assert all(x == 1.0 for x in res.entity_accuracy_per_turn)


def test_per_turn_failing():
    scenario = build_simple_scenario()
    model = MockModel(mode="per_turn", perfect=False)
    res = Evaluator(model).evaluate(scenario, mode="per_turn")
    assert res.conservation_held is False
    assert res.state_correct is False
    assert res.conservation_accuracy < 1.0
    assert res.state_accuracy < 1.0


def test_per_turn_turn_count_mismatch():
    scenario = build_simple_scenario()

    class FewTurnsModel:
        name = "few-turns-mock"

        def generate(self, prompt: str, **kwargs) -> str:
            return (
                '{"turns": ['
                '{"entities": {"entity_0": {"tokens": 4}}, "totals": {"tokens": 10}},'
                '{"entities": {"entity_0": {"tokens": 3}}, "totals": {"tokens": 10}}'
                ']}'
            )

    res = Evaluator(FewTurnsModel()).evaluate(scenario, mode="per_turn")
    assert any(v.violation_type == "turn_count_mismatch" for v in res.violations)
    # Arrays should be length of expected turns (3)
    assert len(res.conservation_accuracy_per_turn) == 3
    assert len(res.entity_accuracy_per_turn) == 3
    assert res.conservation_held is False
    assert res.state_correct is False

