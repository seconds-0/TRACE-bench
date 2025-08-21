from trace.generation.scenario import ScenarioGenerator


def test_generation_determinism():
    seed = 123
    gen1 = ScenarioGenerator(seed)
    gen2 = ScenarioGenerator(seed)

    s1 = gen1.generate_simple(num_entities=3, num_tokens=10, num_actions=5)
    s2 = gen2.generate_simple(num_entities=3, num_tokens=10, num_actions=5)

    # Compare initial states
    assert s1.initial_state.calculate_totals() == s2.initial_state.calculate_totals()
    assert set(s1.initial_state.entities.keys()) == set(s2.initial_state.entities.keys())

    # Compare actions (descriptions should match)
    assert [a.description for a in s1.actions] == [a.description for a in s2.actions]

    # Final ground truth equality
    gt1 = s1.get_ground_truth()[-1]
    gt2 = s2.get_ground_truth()[-1]
    assert {
        name: e.resources for name, e in gt1.entities.items()
    } == {
        name: e.resources for name, e in gt2.entities.items()
    }


def test_generation_sequential_application():
    seed = 42
    gen = ScenarioGenerator(seed)
    scenario = gen.generate_simple(num_entities=3, num_tokens=10, num_actions=5)

    # Apply actions manually and compare to ground truth
    states = [scenario.initial_state]
    cur = scenario.initial_state
    for action in scenario.actions:
        cur = action.apply(cur)
        states.append(cur)

    gt_states = scenario.get_ground_truth()
    assert len(states) == len(gt_states)
    for s, gt in zip(states, gt_states):
        assert {
            n: e.resources for n, e in s.entities.items()
        } == {
            n: e.resources for n, e in gt.entities.items()
        }

