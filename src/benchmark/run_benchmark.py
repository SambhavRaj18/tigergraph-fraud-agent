"""
Batch Benchmark Runner for TigerGraph Fraud Investigation Agent.
Runs all 20 benchmark cases from case_pack.csv, validates schema and policy compliance,
and writes individual JSON files to cases/<case_id>.json.
"""

import os
import json
import time
import pandas as pd
from typing import Dict, Any, List
from src.agent.investigation_agent import FraudInvestigationAgent

CASES_DIR = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/cases")
CASE_PACK_PATH = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/case_pack.csv")


def run_all_benchmarks():
    os.makedirs(CASES_DIR, exist_ok=True)
    df_pack = pd.read_csv(CASE_PACK_PATH)
    agent = FraudInvestigationAgent()
    
    results: List[Dict[str, Any]] = []
    summary_table: List[Dict[str, Any]] = []
    
    print("=" * 100)
    print(f"STARTING BATCH INVESTIGATION RUN ACROSS ALL {len(df_pack)} BENCHMARK CASES")
    print("=" * 100)
    
    total_start = time.time()
    
    for idx, row in df_pack.iterrows():
        case_id = str(row["case_id"])
        print(f"\n[{idx+1}/{len(df_pack)}] Processing {case_id} (Trigger: {row['trigger_type']})...")
        
        try:
            case_output = agent.investigate_case(case_id)
            
            # Remove internal audit trail before saving official deliverable
            audit_trail = case_output.pop("_audit_trail", [])
            
            # Save deliverable JSON to cases/<case_id>.json
            case_file_path = os.path.join(CASES_DIR, f"{case_id}.json")
            with open(case_file_path, "w", encoding="utf-8") as f:
                json.dump(case_output, f, indent=2)
            
            results.append(case_output)
            
            summary_table.append({
                "Case": case_id,
                "Trigger": row["trigger_type"],
                "Verdict": case_output["case"]["verdict"],
                "Pattern": case_output["case"]["pattern"],
                "Prob": case_output["case"]["fraud_probability"],
                "Exposure ($)": case_output["case"]["exposure_usd"],
                "SAR": "YES" if case_output["sar"]["file"] else "NO",
                "Actions": " -> ".join([a["action"] for a in case_output["next_best_actions"]["final"]]),
                "ToolCalls": case_output["tool_calls"],
                "Latency (s)": case_output["latency_s"]
            })
            
            print(f"  -> {case_id}: Verdict={case_output['case']['verdict']}, Pattern={case_output['case']['pattern']}, Prob={case_output['case']['fraud_probability']}, SAR={case_output['sar']['file']}, Latency={case_output['latency_s']}s")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {case_id}: {str(e)}")
            import traceback
            traceback.print_exc()

    total_latency = round(time.time() - total_start, 2)
    
    print("\n" + "=" * 120)
    print(f"BATCH INVESTIGATION SUMMARY (Total Time: {total_latency}s)")
    print("=" * 120)
    df_sum = pd.DataFrame(summary_table)
    print(df_sum.to_string(index=False))
    
    # Validation checklist across all generated files
    print("\n" + "=" * 100)
    print("VERIFYING DELIVERABLES INTEGRITY")
    print("=" * 100)
    
    for case_id in df_pack["case_id"]:
        fp = os.path.join(CASES_DIR, f"{case_id}.json")
        assert os.path.exists(fp), f"Missing JSON file for {case_id}"
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
            assert d["case_id"] == case_id
            assert "case" in d and "sar" in d and "next_best_actions" in d
            assert "initial" in d["next_best_actions"] and "final" in d["next_best_actions"]
            if d["sar"]["file"]:
                assert len(d["sar"]["narrative"]) > 20, f"SAR narrative empty for {case_id}"
                assert len(d["sar"]["subjects"]) > 0, f"SAR subjects empty for {case_id}"
            else:
                assert d["sar"]["narrative"] == "", f"SAR narrative should be empty when file=false for {case_id}"
                assert d["sar"]["subjects"] == [], f"SAR subjects should be empty when file=false for {case_id}"
    
    print(f"All {len(df_pack)} cases successfully generated and verified against the official specification!")


if __name__ == "__main__":
    run_all_benchmarks()
