#!/usr/bin/env python3
"""
BYOM Performance Benchmark Script

Sprint 2.10 - Track B Phase 2: Production Agent Testing

This script runs the same agent task with all 3 providers and compares:
- Response time
- Token usage
- Estimated cost

Usage:
    python scripts/byom_performance_benchmark.py

Requirements:
    - Set environment variables: OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY
    - Database must be running (uses test database by default)

Output:
    - Prints comparison table to console
    - Saves detailed results to: ./benchmark_results_{timestamp}.json
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage

from app.services.agent.llm_factory import LLMFactory

# ============================================================================
# Configuration
# ============================================================================

BENCHMARK_PROMPTS = [
    {
        "name": "Simple Question",
        "prompt": "What is the capital of France? Answer in one word.",
        "expected_tokens": 50
    },
    {
        "name": "Crypto List",
        "prompt": "List 5 popular cryptocurrencies with a brief one-sentence description for each.",
        "expected_tokens": 200
    },
    {
        "name": "Technical Explanation",
        "prompt": "Explain how blockchain consensus mechanisms work in 3 paragraphs.",
        "expected_tokens": 500
    }
]

# Approximate costs per 1M tokens (as of January 2025)
COST_PER_1M_TOKENS = {
    "openai": {
        "model": "gpt-4o-mini",
        "input": 0.15,
        "output": 0.60
    },
    "google": {
        "model": "gemini-1.5-flash",
        "input": 0.075,
        "output": 0.30
    },
    "anthropic": {
        "model": "claude-3-haiku-20240307",
        "input": 0.25,
        "output": 1.25
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def check_api_keys() -> dict[str, bool]:
    """Check which API keys are available"""
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "google": bool(os.getenv("GOOGLE_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY"))
    }


def create_llm_for_provider(provider: str) -> Any:
    """Create LLM instance for a provider using direct API key"""
    api_keys: dict[str, str | None] = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY")
    }

    api_key = api_keys.get(provider)
    if not api_key:
        return None

    # Cast cost model to str to satisfy mypy
    model_name = str(COST_PER_1M_TOKENS[provider]["model"])

    return LLMFactory.create_llm_from_api_key(
        provider=provider,
        api_key=api_key,
        model_name=model_name
    )


def benchmark_llm(llm: Any, provider: str, prompt: str) -> dict[str, Any]:
    """Run benchmark for a single LLM"""

    start_time = time.time()

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        end_time = time.time()

        response_time = end_time - start_time
        response_content = response.content
        response_length = len(response_content)

        # Extract token usage
        token_usage = {}
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if "token_usage" in metadata:
                token_usage = metadata["token_usage"]
                input_tokens = token_usage.get("prompt_tokens", 0)
                output_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = token_usage.get("total_tokens", 0)
            elif "usage_metadata" in metadata:
                token_usage = metadata["usage_metadata"]
                input_tokens = token_usage.get("input_tokens", 0)
                output_tokens = token_usage.get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens

        # Calculate cost
        costs = COST_PER_1M_TOKENS[provider]
        input_cost = (input_tokens / 1_000_000) * float(costs["input"]) # type: ignore
        output_cost = (output_tokens / 1_000_000) * float(costs["output"]) # type: ignore
        total_cost = input_cost + output_cost


        return {
            "provider": provider,
            "model": COST_PER_1M_TOKENS[provider]["model"],
            "success": True,
            "response_time": response_time,
            "response_length": response_length,
            "response_preview": response_content[:100],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "error": None
        }

    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time

        return {
            "provider": provider,
            "model": COST_PER_1M_TOKENS[provider]["model"],
            "success": False,
            "response_time": response_time,
            "error": str(e)
        }


def print_comparison_table(results: list[dict[str, Any]], _prompt_name: str) -> None:
    """Print formatted comparison table"""

    # Filter successful results
    successful = [r for r in results if r["success"]]

    if not successful:
        return

    # Print header

    # Print results sorted by response time
    for result in sorted(successful, key=lambda x: x["response_time"]):
        result["provider"].capitalize()
        result["model"][:28]
        f"{result['response_time']:.2f}"
        f"{result['total_tokens']}" if result["total_tokens"] > 0 else "N/A"
        f"{result['total_cost']:.6f}" if result["total_cost"] > 0 else "N/A"


    # Print response previews
    for _result in successful:
        pass


def save_results(all_results: dict[str, list[dict[str, Any]]], output_file: str) -> None:
    """Save results to JSON file"""
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)



# ============================================================================
# Main Benchmark Function
# ============================================================================

def run_benchmark() -> None:
    """Run the complete benchmark suite"""

    # Check available API keys
    available_keys = check_api_keys()
    for _provider, _available in available_keys.items():
        pass

    providers_to_test = [p for p, available in available_keys.items() if available]

    if not providers_to_test:
        sys.exit(1)

    # Create LLM instances
    llms = {}
    for provider in providers_to_test:
        llm = create_llm_for_provider(provider)
        if llm:
            llms[provider] = llm

    # Run benchmarks
    all_results = {}

    for benchmark in BENCHMARK_PROMPTS:
        prompt_name = str(benchmark["name"])
        prompt = str(benchmark["prompt"])


        results = []
        for provider, llm in llms.items():
            result = benchmark_llm(llm, provider, prompt)
            results.append(result)
            time.sleep(1)  # Rate limiting

        all_results[prompt_name] = results
        print_comparison_table(results, prompt_name)

    # Print summary

    # Calculate averages
    for provider in providers_to_test:
        provider_results = []
        for prompt_results in all_results.values():
            for result in prompt_results:
                if result["provider"] == provider and result["success"]:
                    provider_results.append(result)

        if provider_results:
            sum(r["response_time"] for r in provider_results) / len(provider_results)
            sum(r["total_tokens"] for r in provider_results) / len(provider_results)
            sum(r["total_cost"] for r in provider_results) / len(provider_results)


    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"benchmark_results_{timestamp}.json"
    save_results(all_results, output_file)



# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
