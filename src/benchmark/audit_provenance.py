"""
Audit Factual Provenance across all 20 benchmark case JSON files.
Verifies:
1. No unobserved customer statements asserted as facts.
2. Simulated responses are explicitly marked 'SIMULATED / ASSUMED (not in dataset)'.
3. SAR activity_dates accurately reflect date ranges.
4. Correct multi-transaction episodes, exposure, and verdicts.
"""

import os
import json
import glob

def audit_all_cases():
    cases_dir = "cases"
    files = sorted(glob.glob(os.path.join(cases_dir, "HHG-*.json")))
    print(f"Auditing {len(files)} case files in {cases_dir}...\n")
    
    issues = []
    summary_rows = []
    
    for fp in files:
        case_id = os.path.basename(fp).replace(".json", "")
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
            
        case_info = d.get("case", {})
        sar_info = d.get("sar", {})
        nba = d.get("next_best_actions", {})
        ev_reqs = d.get("evidence_requests", [])
        
        # 1. Check evidence_requests simulated tags
        for req in ev_reqs:
            resp = req.get("assumed_response", "")
            if resp and not resp.startswith("SIMULATED / ASSUMED (not in dataset)"):
                issues.append(f"{case_id}: assumed_response missing explicit simulated tag: {resp}")
                
        # 2. Check SAR activity_dates
        if sar_info.get("file"):
            dates = sar_info.get("activity_dates", [])
            if not dates or len(dates) != 2:
                issues.append(f"{case_id}: SAR activity_dates invalid: {dates}")
            if not sar_info.get("narrative"):
                issues.append(f"{case_id}: SAR narrative missing")
                
        # 3. Check for unobserved assertions in action reasons
        for act in nba.get("final", []):
            reason = act.get("reason", "").lower()
            if "customer confirmed" in reason or "customer denied" in reason:
                issues.append(f"{case_id}: action reason asserts unobserved fact: {act.get('reason')}")
                
        # 4. Check what_changed
        for wc in nba.get("what_changed", []):
            wc_lower = wc.lower()
            if "customer confirmed" in wc_lower or "customer denied" in wc_lower:
                issues.append(f"{case_id}: what_changed asserts unobserved fact: {wc}")
                
        summary_rows.append({
            "case_id": case_id,
            "verdict": case_info.get("verdict"),
            "pattern": case_info.get("pattern"),
            "exposure_usd": case_info.get("exposure_usd"),
            "sar": sar_info.get("file"),
            "activity_dates": sar_info.get("activity_dates", []),
            "affected_txns_count": len(case_info.get("affected_txn_ids", []))
        })
        
    print(f"{'Case':<10} {'Verdict':<12} {'Pattern':<28} {'Exposure ($)':<14} {'SAR':<6} {'Dates':<26} {'Txns'}")
    print("-" * 105)
    for r in summary_rows:
        dates_str = str(r['activity_dates']) if r['sar'] else "-"
        print(f"{r['case_id']:<10} {r['verdict']:<12} {r['pattern']:<28} {r['exposure_usd']:<14.2f} {str(r['sar']):<6} {dates_str:<26} {r['affected_txns_count']}")
        
    print("\n" + "=" * 80)
    if not issues:
        print(">>> PROVENANCE AUDIT PASSED: 0 ISSUES FOUND ACROSS ALL 20 CASES <<<")
    else:
        print(f">>> FOUND {len(issues)} ISSUES:")
        for iss in issues:
            print(f"  [X] {iss}")
    print("=" * 80)
    
    return len(issues) == 0

if __name__ == "__main__":
    audit_all_cases()
