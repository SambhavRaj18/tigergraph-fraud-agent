"""
Regression Test Suite for Real TigerGraph MCP Server Integration.
Runs cases: HHG-001, HHG-005, HHG-006, HHG-017.
"""

from src.agent.investigation_agent import FraudInvestigationAgent
from src.agent.tools import InvestigationTools
from src.agent.llm_provider import get_llm_provider


def main():
    cases = ["HHG-001", "HHG-005", "HHG-006", "HHG-017"]
    tools = InvestigationTools(use_mcp=True)
    agent = FraudInvestigationAgent(tools=tools, llm_provider=get_llm_provider("deterministic"))

    print("=" * 100)
    print("REGRESSION RESULTS (REAL TIGERGRAPH MCP SERVER - STDIO TRANSPORT)")
    print("=" * 100)

    for cid in cases:
        res = agent.investigate_case(cid)
        case_info = res["case"]
        verdict = case_info["verdict"]
        pattern = case_info["pattern"]
        prob = case_info["fraud_probability"]
        exposure = case_info["exposure_usd"]
        sar = res["sar"]["file"]
        tools_called = res["tool_calls"]
        lat = res["latency_s"]
        
        print(f"Case: {cid:<8s} | Verdict: {verdict:<11s} | Pattern: {pattern:<28s} | Prob: {prob:<4.2f} | Exposure: ${exposure:>8.2f} | SAR: {str(sar):<5s} | ToolCalls: {tools_called} | Latency: {lat:>5.2f}s")

    print("=" * 100)


if __name__ == "__main__":
    main()
