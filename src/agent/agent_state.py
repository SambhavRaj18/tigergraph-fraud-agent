"""
Investigation State and Tool Telemetry Data Structures.
Defines the state container for the Agentic Fraud Investigation layer.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ToolCallRecord:
    step: int
    tool_name: str
    arguments: Dict[str, Any]
    summary: str
    rationale: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    duration_s: float = 0.0
    state_changed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "tool": self.tool_name,
            "args": self.arguments,
            "summary": self.summary,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
            "duration_s": self.duration_s,
            "state_changed": self.state_changed
        }


@dataclass
class InvestigationState:
    case_id: str
    trigger: Dict[str, Any] = field(default_factory=dict)
    flagged_txn_id: str = ""
    target_transaction: Optional[Dict[str, Any]] = None
    customer_profile: Optional[Dict[str, Any]] = None
    raw_graph_data: Optional[Dict[str, Any]] = None
    analyzed_evidence: Optional[Dict[str, Any]] = None
    historical_cases: List[Dict[str, Any]] = field(default_factory=list)
    policy_decision: Optional[Dict[str, Any]] = None
    
    # Reasoning & Telemetry
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    reasoning_summary: str = ""
    hypotheses: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    evidence_requests: List[Dict[str, Any]] = field(default_factory=list)
    
    # Control flags
    stop_reason: Optional[str] = None
    iteration: int = 0
    max_iterations: int = 10
    is_complete: bool = False
    written_to_graph: bool = False

    def add_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        summary: str,
        rationale: str,
        duration_s: float,
        state_changed: bool = True
    ) -> ToolCallRecord:
        record = ToolCallRecord(
            step=len(self.tool_calls) + 1,
            tool_name=tool_name,
            arguments=arguments,
            summary=summary,
            rationale=rationale,
            duration_s=round(duration_s, 3),
            state_changed=state_changed
        )
        self.tool_calls.append(record)
        return record
