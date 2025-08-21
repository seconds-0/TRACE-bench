#!/usr/bin/env python3
"""
Test script to run TRACE steel thread across multiple free models.
Compares performance across different model providers and architectures.
"""

import json
import time
from pathlib import Path
from steel_thread import SteelThreadTRACE

# Free models to test
FREE_MODELS = [
    "openai/gpt-3.5-turbo",  # baseline comparison
    "thenlper/gte-large",  # GPT-OSS alternative
    "zhipuai/glm-4-air",  # GLM 4.5 air
    "qwen/qwen-2.5-coder-32b-instruct:free",  # Qwen Coder free
    "moonshotai/kimi-k2:free",  # Moonshot Kimi K2
    "deepseek/deepseek-r1-0528-qwen3-8b:free",  # DeepSeek
    "google/gemma-2b-it:free",  # Gemma 2B
    "mistralai/mistral-7b-instruct:free",  # Mistral free alternative
]

def test_model(model_name: str) -> dict:
    """Test a single model and return results."""
    print(f"\n🚀 Testing {model_name}")
    print("=" * 50)
    
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

def generate_summary(all_results: list) -> dict:
    """Generate summary statistics."""
    total_models = len(all_results)
    successful_tests = len([r for r in all_results if "error" not in r])
    conservation_passes = len([r for r in all_results if r.get("conservation_held", False)])
    state_passes = len([r for r in all_results if r.get("state_correct", False)])
    
    avg_duration = sum(r.get("test_duration", 0) for r in all_results) / total_models
    
    return {
        "summary": {
            "total_models": total_models,
            "successful_tests": successful_tests,
            "conservation_pass_rate": f"{conservation_passes}/{total_models} ({conservation_passes/total_models*100:.1f}%)",
            "state_accuracy_rate": f"{state_passes}/{total_models} ({state_passes/total_models*100:.1f}%)",
            "avg_duration": f"{avg_duration:.2f}s",
        },
        "detailed_results": all_results
    }

def print_comparison_table(all_results: list):
    """Print a nice comparison table."""
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE COMPARISON")
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
    """Run tests across all models."""
    print("🧪 TRACE Multi-Model Benchmark")
    print(f"Testing {len(FREE_MODELS)} free models...")
    
    all_results = []
    
    for i, model in enumerate(FREE_MODELS, 1):
        print(f"\n[{i}/{len(FREE_MODELS)}]", end=" ")
        result = test_model(model)
        all_results.append(result)
        
        # Brief pause between models to be nice to the API
        if i < len(FREE_MODELS):
            time.sleep(2)
    
    # Generate summary
    summary_data = generate_summary(all_results)
    
    # Print results table
    print_comparison_table(all_results)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    summary = summary_data["summary"]
    print(f"Total Models Tested: {summary['total_models']}")
    print(f"Successful Tests: {summary['successful_tests']}")
    print(f"Conservation Pass Rate: {summary['conservation_pass_rate']}")
    print(f"State Accuracy Rate: {summary['state_accuracy_rate']}")
    print(f"Average Duration: {summary['avg_duration']}")
    
    # Save detailed results
    output_file = "multi_model_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\n💾 Detailed results saved to {output_file}")
    print("🎉 Multi-model benchmark complete!")

if __name__ == "__main__":
    main()