"""
CLI Runner for Fraud Investigation Agent.
Usage:
    python -m src.agent.run_case --case-id HHG-001
    python -m src.agent.run_case --case-id HHG-006 --provider deterministic
"""

import sys
import json
import argparse
from src.agent.investigation_agent import FraudInvestigationAgent
from src.agent.llm_provider import get_llm_provider


def main():
    parser = argparse.ArgumentParser(description="Run Agentic Fraud Investigation on a target case.")
    parser.add_argument("--case-id", type=str, default="HHG-001", help="Case ID from case_pack.csv (e.g. HHG-001)")
    parser.add_argument("--provider", type=str, default="deterministic", choices=["deterministic", "mock", "gemini", "openai"], help="LLM Provider type")
    parser.add_argument("--save-output", action="store_true", help="Save output JSON to cases/<case-id>.json")
    
    args = parser.parse_args()

    provider = get_llm_provider(args.provider)
    agent = FraudInvestigationAgent(llm_provider=provider)

    try:
        result = agent.investigate_case(args.case_id)
        print("\n=======================================================")
        print(f"  INVESTIGATION RESULT: {args.case_id}")
        print("=======================================================")
        print(json.dumps(result, indent=2))
        print("=======================================================\n")

        if args.save_output:
            import os
            os.makedirs("cases", exist_ok=True)
            out_file = os.path.join("cases", f"{args.case_id}.json")
            with open(out_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"[SUCCESS] Saved result to {out_file}")

    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
