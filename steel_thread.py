"""
Steel Thread for TRACE Benchmark (strict JSON, final-state only).

This script demonstrates the minimal end-to-end benchmark:
- Builds a deterministic prompt for a simple conservation scenario
- Calls an LLM via OpenRouter with low-variance params
- Requires the model to return strict JSON; validates and parses
- Checks conservation and state correctness; writes results JSON

Usage:
  export OPENROUTER_API_KEY=...  # required for live call
  python steel_thread.py

Notes:
- Set MOCK_STEEL_THREAD=1 to bypass API and use a deterministic mock response
  for local validation without network calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Tuple

import requests


TRACE_SCHEMA_VERSION = "0.1.0"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Exceptions
class SteelThreadError(Exception):
    """Base exception for steel thread errors."""


class MissingAPIKeyError(ValueError, SteelThreadError):
    """Raised when an API key is required but missing."""


class ResponseNotJSONError(ValueError, SteelThreadError):
    """Raised when the model response is not valid JSON matching the schema."""


@dataclass
class SteelThreadConfig:
    model: str = "openai/gpt-3.5-turbo"
    temperature: float = 0.0
    top_p: float = 1.0
    timeout: int = 30
    retries: int = 3


class SteelThreadTRACE:
    """Minimal end-to-end implementation of TRACE benchmark (strict JSON)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.config = SteelThreadConfig()

    def call_model(self, prompt: str) -> str:
        """Call OpenRouter API and return the text content.

        Retries with exponential backoff on failures and rate limits (429).
        """
        if not self.api_key:
            raise MissingAPIKeyError(
                "Need OPENROUTER_API_KEY environment variable for live calls"
            )

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "trace-benchmark/0.1 (+https://example.org)"
        }

        backoff = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.config.retries):
            try:
                resp = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout,
                )
                if resp.status_code == 429:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                data = resp.json()
                # Capture provider request id if any
                self._last_request_id = (
                    resp.headers.get("x-request-id")
                    or resp.headers.get("x-openai-request-id")
                    or None
                )
                return data["choices"][0]["message"]["content"]
            except Exception as e:  # noqa: BLE001
                last_exc = e
                if attempt == self.config.retries - 1:
                    break
                time.sleep(backoff)
                backoff *= 2
        assert last_exc is not None
        raise SteelThreadError(f"Failed calling model after retries: {last_exc}")

    @staticmethod
    def parse_json_state(response: str) -> Tuple[Dict[str, int], int]:
        """Parse strict JSON response into final state and total tokens.

        Expected schema:
          {
            "entities": {"Alice": {"tokens": int}, ...},
            "totals": {"tokens": int}
          }
        Entity names are normalized to lowercase in the returned dict.
        """
        try:
            obj = json.loads(response)
        except json.JSONDecodeError as e:  # noqa: TRY003
            raise ResponseNotJSONError(f"Response was not valid JSON: {e}")

        if not isinstance(obj, dict) or "entities" not in obj or "totals" not in obj:
            raise ResponseNotJSONError(
                "Response JSON missing required keys 'entities' and 'totals'"
            )

        entities = obj["entities"]
        totals = obj["totals"]
        if not isinstance(entities, dict) or not isinstance(totals, dict):
            raise ResponseNotJSONError("'entities' and 'totals' must be objects")
        if "tokens" not in totals or not isinstance(totals["tokens"], int):
            raise ResponseNotJSONError("'totals.tokens' must be an integer")

        state: Dict[str, int] = {}
        for name, res in entities.items():
            if not isinstance(res, dict) or "tokens" not in res or not isinstance(res["tokens"], int):
                raise ResponseNotJSONError(f"Entity '{name}' missing integer 'tokens'")
            state[name.lower()] = int(res["tokens"])

        return state, int(totals["tokens"])

    @staticmethod
    def verify_conservation(state: Dict[str, int], expected_total: int) -> bool:
        return sum(state.values()) == expected_total

    def run(self, save_prompt: bool = False, save_prefix: str = "steel_thread") -> Dict:
        """Run the steel thread (final-state only). Returns results dict."""

        # Initial setup
        initial_state = {"alice": 5, "bob": 3, "charlie": 2}
        total_tokens = sum(initial_state.values())

        # Build strict prompt
        prompt = f"""
You are tracking a system with 3 entities and a conserved resource 'tokens'.

CRITICAL RULES:
1) Tokens cannot be created or destroyed, only transferred.
2) The total number of tokens must ALWAYS equal {total_tokens}.

Initial state:
  - Alice: tokens={initial_state['alice']}
  - Bob: tokens={initial_state['bob']}
  - Charlie: tokens={initial_state['charlie']}
  - Total: tokens={total_tokens}

Actions (apply in order):
  1. Alice gives Bob 2 tokens.
  2. Charlie gives Alice 1 token.
  3. Bob gives Charlie 3 tokens.

Respond ONLY with a single JSON object of this exact schema and nothing else:
{{
  "entities": {{
    "Alice": {{"tokens": <int>}},
    "Bob": {{"tokens": <int>}},
    "Charlie": {{"tokens": <int>}}
  }},
  "totals": {{"tokens": <int>}}
}}
""".strip()

        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        print(f"\n🚀 Running steel thread with {self.config.model}")
        print(f"📊 Initial total: {total_tokens} tokens")

        started_at = _iso_now()

        # Optionally save prompt early
        if save_prompt:
            with open(f"{save_prefix}_prompt.txt", "w", encoding="utf-8") as pf:
                pf.write(prompt)

        # Call the model (or use mock)
        if os.getenv("MOCK_STEEL_THREAD"):
            response = json.dumps(
                {
                    "entities": {
                        "Alice": {"tokens": 4},
                        "Bob": {"tokens": 2},
                        "Charlie": {"tokens": 4},
                    },
                    "totals": {"tokens": total_tokens},
                }
            )
        else:
            # First attempt
            response = self.call_model(prompt)

        ended_at = _iso_now()

        print(f"\n📝 Model response:\n{response}\n")

        # Parse and verify (with one strict retry on non-JSON)
        try:
            final_state, reported_total = self.parse_json_state(response)
        except ValueError:
            strict_reminder = (
                prompt
                + "\n\nSTRICT REMINDER: Respond only with a single JSON object matching the schema. No prose."
            )
            response = self.call_model(strict_reminder)
            print("🔁 Retried with strict reminder.")
            final_state, reported_total = self.parse_json_state(response)

        # Optionally save response
        if save_prompt:
            with open(f"{save_prefix}_response.txt", "w", encoding="utf-8") as rf:
                rf.write(response)
        print(f"📈 Parsed state: {final_state}; reported_total={reported_total}")

        # Ground truth
        ground_truth = {
            "alice": 4,  # 5 - 2 + 1 = 4
            "bob": 2,    # 3 + 2 - 3 = 2
            "charlie": 4 # 2 + 3 - 1 = 4
        }

        conservation_held = self.verify_conservation(final_state, total_tokens)
        state_correct = final_state == ground_truth

        results = {
            "trace_schema_version": TRACE_SCHEMA_VERSION,
            "model": self.config.model,
            "params": {"temperature": self.config.temperature, "top_p": self.config.top_p},
            "prompt_hash": prompt_hash,
            "timestamps": {"started_at": started_at, "ended_at": ended_at},
            "request_id": getattr(self, "_last_request_id", None),
            "conservation_held": conservation_held,
            "state_correct": state_correct,
            "expected_total": total_tokens,
            "actual_total": sum(final_state.values()),
            "reported_total": reported_total,
            "reported_total_matches": reported_total == sum(final_state.values()),
            "expected_state": ground_truth,
            "actual_state": final_state,
            "raw_response": response,
        }

        # Print summary
        print("\n" + "=" * 50)
        print("STEEL THREAD RESULTS")
        print("=" * 50)
        print(f"✓ Conservation: {'PASS ✅' if conservation_held else 'FAIL ❌'}")
        print(f"✓ State Accuracy: {'PASS ✅' if state_correct else 'FAIL ❌'}")

        return results


def main() -> int:
    parser = argparse.ArgumentParser(description="TRACE steel thread")
    parser.add_argument("--model", default="openai/gpt-3.5-turbo")
    parser.add_argument("--save-prompt", action="store_true")
    parser.add_argument("--save-prefix", default="steel_thread")
    parser.add_argument("--timeout", type=int, default=None, help="HTTP timeout seconds")
    args = parser.parse_args()

    runner = SteelThreadTRACE()
    runner.config.model = args.model
    if args.timeout is not None:
        runner.config.timeout = args.timeout
    try:
        results = runner.run(save_prompt=args.save_prompt, save_prefix=args.save_prefix)
    except Exception as e:  # noqa: BLE001
        print(f"\n❌ Steel thread failed: {e}", file=sys.stderr)
        return 1

    # Persist results
    with open("steel_thread_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    if results["conservation_held"] and results["state_correct"]:
        print("\n🎉 STEEL THREAD COMPLETE - Core concept validated!")
        return 0
    else:
        print("\n⚠️  STEEL THREAD ISSUES DETECTED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
