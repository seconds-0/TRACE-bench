"""
TRACE command-line interface.
"""

from __future__ import annotations

import argparse

from .evaluation.executor import Evaluator
from .evaluation.suite import BenchmarkSuite
from .generation.scenario import ScenarioGenerator
from .generation.prompt_builder import PromptBuilder
from .models.openrouter import OpenRouterModel
from .models.mock import MockModel


def main():
    parser = argparse.ArgumentParser(description="TRACE Benchmark CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_quick = sub.add_parser("quick", help="Run a single scenario")
    p_quick.add_argument("--model", default="openai/gpt-3.5-turbo")
    p_quick.add_argument("--mode", default="final", choices=["final", "per_turn"]) 
    p_quick.add_argument("--seed", type=int, default=42)

    p_suite = sub.add_parser("suite", help="Run a suite of scenarios")
    p_suite.add_argument("--model", default="openai/gpt-3.5-turbo")
    p_suite.add_argument("--mode", default="final", choices=["final", "per_turn"]) 
    p_suite.add_argument("--difficulty", default="easy", choices=["trivial", "easy", "medium"]) 
    p_suite.add_argument("--scenarios", type=int, default=5)
    p_suite.add_argument("--output", default="results.json")

    p_test = sub.add_parser("test", help="Run with mock model")
    p_test.add_argument("--mode", default="final", choices=["final", "per_turn"]) 

    args = parser.parse_args()

    if args.cmd == "quick":
        model = OpenRouterModel(args.model)
        gen = ScenarioGenerator(args.seed)
        scenario = gen.generate_simple()
        res = Evaluator(model).evaluate(scenario, mode=args.mode)
        print("Conservation:", "PASS" if res.conservation_held else "FAIL")
        print("State:", "PASS" if res.state_correct else "FAIL")
        return

    if args.cmd == "suite":
        model = OpenRouterModel(args.model)
        suite = BenchmarkSuite(model)
        results = suite.run_suite(args.difficulty, args.scenarios, mode=args.mode)
        suite.save_results(results, args.output)
        print("Saved:", args.output)
        return

    if args.cmd == "test":
        model = MockModel(mode=args.mode, perfect=True)
        gen = ScenarioGenerator(42)
        scenario = gen.generate_simple()
        res = Evaluator(model).evaluate(scenario, mode=args.mode)
        assert res.conservation_held and res.state_correct
        print("Mock test passed.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()

