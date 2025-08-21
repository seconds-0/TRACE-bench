#!/usr/bin/env python3
"""
Test script for additional free models requested by user.
"""

import json
import time
from pathlib import Path
from steel_thread import SteelThreadTRACE

# Additional models to test
ADDITIONAL_MODELS = [
    "z-ai/glm-4.5-air:free",
    "openai/gpt-oss-20b:free", 
    "google/gemma-3-27b-it:free",
    "google/gemma-3-4b-it:free",
]

def test_model(model_name: str) -> dict:
    """Test a single model and return results."""
    print(f"\n🚀 Testing {model_name}")
    print("=" * 60)
    
    try:
        runner = SteelThreadTRACE()
        runner.config.model = model_name
        
        start_time = time.time()
        results = runner.run()
        end_time = time.time()
        
        # Add timing info
        results["test_duration"] = round(end_time - start_time, 2)
        
        # Print summary
        conservation_status = "✅ PASS" if results["conservation_held"] else "❌ FAIL"
        state_status = "✅ PASS" if results["state_correct"] else "❌ FAIL"
        
        print(f"Conservation: {conservation_status}")
        print(f"State Accuracy: {state_status}")
        print(f"Duration: {results['test_duration']}s")
        
        if not results["state_correct"]:
            print(f"Expected: {results['expected_state']}")
            print(f"Actual: {results['actual_state']}")
        
        return results
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            "model": model_name,
            "error": str(e),
            "conservation_held": False,
            "state_correct": False,
            "test_duration": 0
        }

def print_results_table(all_results: list):
    """Print a nice comparison table."""
    print("\n" + "=" * 80)
    print("ADDITIONAL MODELS PERFORMANCE")
    print("=" * 80)
    print(f"{'Model':<40} {'Conservation':<12} {'State':<12} {'Time':<8}")
    print("-" * 80)
    
    for result in all_results:
        model = result.get("model", "unknown")[:38]
        
        if "error" in result:
            conservation = "ERROR"
            state = "ERROR"
            duration = "N/A"
        else:
            conservation = "PASS" if result.get("conservation_held", False) else "FAIL"
            state = "PASS" if result.get("state_correct", False) else "FAIL"
            duration = f"{result.get('test_duration', 0):.1f}s"
        
        print(f"{model:<40} {conservation:<12} {state:<12} {duration:<8}")

def main():
    """Run tests on additional models."""
    print("🧪 TRACE Additional Models Test")
    print(f"Testing {len(ADDITIONAL_MODELS)} additional free models...")
    
    all_results = []
    
    for i, model in enumerate(ADDITIONAL_MODELS, 1):
        print(f"\n[{i}/{len(ADDITIONAL_MODELS)}]", end=" ")
        result = test_model(model)
        all_results.append(result)
        
        # Brief pause between models
        if i < len(ADDITIONAL_MODELS):
            time.sleep(2)
    
    # Print results table
    print_results_table(all_results)
    
    # Calculate stats
    total_models = len(all_results)
    successful_tests = len([r for r in all_results if "error" not in r])
    conservation_passes = len([r for r in all_results if r.get("conservation_held", False)])
    state_passes = len([r for r in all_results if r.get("state_correct", False)])
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Models Tested: {total_models}")
    print(f"Successful Tests: {successful_tests}")
    print(f"Conservation Pass Rate: {conservation_passes}/{total_models} ({conservation_passes/total_models*100:.1f}%)")
    print(f"State Accuracy Rate: {state_passes}/{total_models} ({state_passes/total_models*100:.1f}%)")
    
    # Save results
    output_file = "additional_models_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "models_tested": ADDITIONAL_MODELS,
            "summary": {
                "total_models": total_models,
                "successful_tests": successful_tests,
                "conservation_passes": conservation_passes,
                "state_passes": state_passes
            },
            "detailed_results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    print("🎉 Additional models test complete!")

if __name__ == "__main__":
    main()