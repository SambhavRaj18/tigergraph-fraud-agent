"""
Autonomous Fraud Investigation Agent for TigerGraph × Hacker House Goa.
Integrates LLM-driven multi-step tool selection, dynamic reasoning, state tracking,
and deterministic PolicyDecisionEngine guardrails.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional

from src.agent.tools import InvestigationTools, TOOL_DEFINITIONS
from src.agent.agent_state import InvestigationState, ToolCallRecord
from src.agent.llm_provider import LLMProvider, get_llm_provider, ToolSelection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("InvestigationAgent")


class FraudInvestigationAgent:
    def __init__(
        self,
        tools: Optional[InvestigationTools] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        self.tools = tools or InvestigationTools()
        self.llm_provider = llm_provider or get_llm_provider()

    def investigate_case(self, case_id: str) -> Dict[str, Any]:
        """
        Executes autonomous multi-step investigation for a given case_id.
        Iteratively selects tools via LLM reasoning while enforcing strict deterministic
        policy rules for executable actions, exposure calculation, and SAR generation.
        """
        start_time = time.time()
        logger.info(f"=== Starting Agentic Investigation for Case: {case_id} ===")

        # Step 0: Initialize State and Retrieve Trigger
        t0 = time.time()
        case_meta = self.tools.retrieve_case_trigger(case_id)
        state = InvestigationState(
            case_id=case_id,
            trigger=case_meta,
            flagged_txn_id=case_meta.get("flagged_txn_id", "")
        )
        state.add_tool_call(
            tool_name="retrieve_case_trigger",
            arguments={"case_id": case_id},
            summary=f"Trigger: {case_meta['trigger_type']}, Flagged Txn: {case_meta['flagged_txn_id']}, Customer: {case_meta['customer_id']}",
            rationale="Initial alert ingestion and metadata retrieval.",
            duration_s=time.time() - t0
        )

        # Iterative ReAct Reasoning Loop
        while not state.is_complete and state.iteration < state.max_iterations:
            state.iteration += 1

            # Prepare state summary for LLM tool selection
            raw_data_dict = state.raw_graph_data if isinstance(state.raw_graph_data, dict) else {}
            state_summary = {
                "iteration": state.iteration,
                "has_raw_graph_data": state.raw_graph_data is not None,
                "has_analyzed_evidence": state.analyzed_evidence is not None,
                "has_policy_decision": state.policy_decision is not None,
                "related_closed_cases": [
                    c if isinstance(c, str) else c.get("v_id")
                    for c in raw_data_dict.get("related_closed_cases", [])
                ],
                "evidence_requests_count": len(state.evidence_requests)
            }

            tool_history = [t.to_dict() for t in state.tool_calls]

            # LLM chooses next tool action
            selection: ToolSelection = self.llm_provider.select_next_action(
                case_id=case_id,
                trigger=state.trigger,
                available_tools=TOOL_DEFINITIONS,
                state_summary=state_summary,
                tool_history=tool_history
            )

            logger.info(f"[Iteration {state.iteration}] Selected Tool: {selection.tool_name} | Rationale: {selection.rationale}")

            if selection.is_terminal or selection.tool_name == "stop_investigation":
                state.is_complete = True
                state.stop_reason = selection.stop_reason or "sufficient_evidence"
                break

            # Execute Selected Tool
            t_exec = time.time()
            tool_name = selection.tool_name
            args = selection.arguments
            summary_str = ""

            try:
                if tool_name == "investigate_transaction":
                    txn_id = args.get("transaction_id") or state.flagged_txn_id
                    raw_data = self.tools.investigate_transaction(txn_id)
                    state.raw_graph_data = raw_data
                    state.target_transaction = raw_data.get("target_transaction")
                    summary_str = (
                        f"Retrieved target txn, customer profile, "
                        f"{len(raw_data.get('customer_transactions', []))} historical txns, "
                        f"{len(raw_data.get('related_closed_cases', []))} closed cases"
                    )

                elif tool_name == "analyze_evidence":
                    analyzed = self.tools.analyze_evidence(state.raw_graph_data)
                    state.analyzed_evidence = analyzed
                    geo = analyzed.get("geographic_analysis", {})
                    base = analyzed.get("customer_baseline_statistics", {})
                    summary_str = (
                        f"Baseline computed: {base.get('total_transactions', 0)} txns, "
                        f"target region '{geo.get('target_billing_region')}' (count={geo.get('target_region_historical_count', 0)})"
                    )

                elif tool_name in ["get_similar_closed_cases", "retrieve_historical_case_details"]:
                    case_ids = args.get("case_ids", [])
                    details = self.tools.get_similar_closed_cases(case_ids)
                    state.historical_cases = details
                    summary_str = f"Retrieved details for {len(details)} closed cases from historical memory"

                elif tool_name == "get_policy_rule":
                    rule_id = args.get("rule_id", "R1")
                    rule_info = self.tools.get_policy_rule(rule_id)
                    summary_str = f"Consulted policy rule {rule_info.get('rule_id')}: {rule_info.get('description')}"

                elif tool_name == "request_customer_validation":
                    q = args.get("question", "Verify flagged transaction")
                    ch = args.get("channel", "SMS")
                    req = self.tools.request_customer_validation(q, ch)
                    state.evidence_requests.append(req)
                    summary_str = f"Queued customer validation via {ch}: '{q}'"

                elif tool_name == "request_analyst_information":
                    q = args.get("question", "Review complex pattern")
                    req = self.tools.request_analyst_information(q)
                    state.evidence_requests.append(req)
                    summary_str = f"Queued analyst review: '{q}'"

                elif tool_name == "evaluate_policy_decision":
                    if not state.analyzed_evidence and state.raw_graph_data:
                        state.analyzed_evidence = self.tools.analyze_evidence(state.raw_graph_data)
                    
                    decision = self.tools.evaluate_policy_decision(
                        case_id=case_id,
                        trigger_type=state.trigger.get("trigger_type", ""),
                        trigger_text=state.trigger.get("trigger_text", ""),
                        evidence=state.analyzed_evidence or {}
                    )
                    state.policy_decision = decision
                    summary_str = (
                        f"Verdict: {decision['case']['verdict']}, "
                        f"Pattern: {decision['case']['pattern']}, "
                        f"Prob: {decision['case']['fraud_probability']}"
                    )

                else:
                    logger.warning(f"Unrecognized tool call: {tool_name}")
                    summary_str = f"Unknown tool '{tool_name}'"

            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                summary_str = f"Error: {str(e)}"

            state.add_tool_call(
                tool_name=tool_name,
                arguments=args,
                summary=summary_str,
                rationale=selection.rationale,
                duration_s=time.time() - t_exec
            )

        # Ensure policy decision is evaluated
        if not state.policy_decision:
            if not state.analyzed_evidence and state.raw_graph_data:
                state.analyzed_evidence = self.tools.analyze_evidence(state.raw_graph_data)
            
            decision = self.tools.evaluate_policy_decision(
                case_id=case_id,
                trigger_type=state.trigger.get("trigger_type", ""),
                trigger_text=state.trigger.get("trigger_text", ""),
                evidence=state.analyzed_evidence or {}
            )
            state.policy_decision = decision

        # Write concluded case into TigerGraph Memory
        t_write = time.time()
        written = self.tools.write_case_to_graph_memory(
            case_id=case_id,
            case_decision=state.policy_decision,
            case_meta=state.trigger
        )
        state.written_to_graph = written
        state.policy_decision["case"]["written_to_graph"] = written
        state.policy_decision["case"]["graph_case_id"] = case_id if written else ""

        state.add_tool_call(
            tool_name="write_case_to_graph_memory",
            arguments={"case_id": case_id, "written": written},
            summary=f"Persisted case {case_id} as ClosedCase in TigerGraph (written={written})",
            rationale="Persist investigation verdict and outcome into institutional graph memory.",
            duration_s=time.time() - t_write
        )

        # Final Synthesis
        synthesis = self.llm_provider.synthesize_investigation(
            case_id=case_id,
            trigger=state.trigger,
            evidence=state.analyzed_evidence or {},
            policy_decision=state.policy_decision,
            tool_history=[t.to_dict() for t in state.tool_calls]
        )

        # Merge evidence requests from state into decision if any were queued
        if state.evidence_requests and not state.policy_decision.get("evidence_requests"):
            state.policy_decision["evidence_requests"] = state.evidence_requests

        total_latency = round(time.time() - start_time, 2)
        audit_trail = [t.to_dict() for t in state.tool_calls]

        final_benchmark_output = {
            "case_id": state.policy_decision["case_id"],
            "case": state.policy_decision["case"],
            "evidence_requests": state.policy_decision["evidence_requests"],
            "next_best_actions": state.policy_decision["next_best_actions"],
            "sar": state.policy_decision["sar"],
            "stop_reason": state.stop_reason or state.policy_decision.get("stop_reason", "sufficient_evidence"),
            "tool_calls": len(state.tool_calls),
            "tokens": 0,
            "latency_s": total_latency,
            "_audit_trail": audit_trail
        }

        logger.info(f"=== Investigation Complete for {case_id} in {total_latency}s ({len(state.tool_calls)} tool calls) ===")
        return final_benchmark_output
