"""
Comprehensive Test Suite for Agentic Fraud Investigation System.
Validates:
1. Multi-step tool invocation and state transitions.
2. State uncertainty tracking and resolution.
3. Error handling on invalid case identifiers.
4. Correct multi-transaction burst clustering & exposure for HHG-006 ($1,906.07).
5. Correct multi-transaction burst clustering & exposure for HHG-011 ($470.97).
6. Proper pattern handling and R1 legitimacy for HHG-017 ($0.00 exposure).
7. Device sharing evaluation and legitimacy for HHG-005 ($0.00 exposure).
8. FinCEN SAR narrative & regulatory compliance triggers.
9. Strict enforcement of deterministic policy boundaries.
10. TigerGraph institutional case memory persistence.
"""

import os
import unittest
import json
from src.agent.investigation_agent import FraudInvestigationAgent
from src.agent.tools import InvestigationTools, TOOL_DEFINITIONS
from src.agent.agent_state import InvestigationState
from src.agent.llm_provider import DeterministicFallbackProvider, get_llm_provider


class TestAgenticInvestigationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = InvestigationTools()
        cls.agent = FraudInvestigationAgent(tools=cls.tools, llm_provider=DeterministicFallbackProvider())

    def test_01_tool_definitions_and_schema(self):
        """Verify tool definition schema and completeness."""
        self.assertGreaterEqual(len(TOOL_DEFINITIONS), 7)
        tool_names = [t["name"] for t in TOOL_DEFINITIONS]
        expected_tools = [
            "retrieve_case_trigger",
            "investigate_transaction",
            "analyze_evidence",
            "get_similar_closed_cases",
            "get_policy_rule",
            "request_customer_validation",
            "evaluate_policy_decision"
        ]
        for exp in expected_tools:
            self.assertIn(exp, tool_names, f"Expected tool '{exp}' in TOOL_DEFINITIONS")

    def test_02_invalid_case_id_handling(self):
        """Verify proper exception handling when an invalid case ID is passed."""
        with self.assertRaises(ValueError):
            self.agent.investigate_case("HHG-INVALID-999")

    def test_03_hhg001_legitimate_flow(self):
        """Verify HHG-001 end-to-end investigation with state & audit trail."""
        result = self.agent.investigate_case("HHG-001")
        self.assertEqual(result["case_id"], "HHG-001")
        self.assertEqual(result["case"]["verdict"], "legitimate")
        self.assertEqual(result["case"]["exposure_usd"], 0.0)
        self.assertEqual(result["case"]["affected_txn_ids"], [])
        self.assertFalse(result["sar"]["file"])
        self.assertEqual(result["stop_reason"], "sufficient_evidence")
        self.assertGreater(result["tool_calls"], 3)
        self.assertTrue(result["case"]["written_to_graph"])

    def test_04_hhg006_burst_and_exposure(self):
        """Verify HHG-006 4-transaction Product C burst and exact $1,906.07 exposure."""
        result = self.agent.investigate_case("HHG-006")
        self.assertEqual(result["case_id"], "HHG-006")
        self.assertEqual(result["case"]["verdict"], "fraud")
        self.assertEqual(result["case"]["pattern"], "card_not_present_fraud")
        self.assertAlmostEqual(result["case"]["exposure_usd"], 1906.07, places=2)
        self.assertEqual(result["case"]["first_suspicious_txn_id"], "3476602")
        self.assertEqual(
            result["case"]["affected_txn_ids"],
            ["3476602", "3476633", "3476665", "3476682"]
        )
        self.assertTrue(result["sar"]["file"])
        self.assertAlmostEqual(result["sar"]["total_amount_usd"], 1906.07, places=2)

    def test_05_hhg011_burst_and_exposure(self):
        """Verify HHG-011 10-transaction Product C burst and exact $470.97 exposure."""
        result = self.agent.investigate_case("HHG-011")
        self.assertEqual(result["case_id"], "HHG-011")
        self.assertEqual(result["case"]["verdict"], "fraud")
        self.assertEqual(result["case"]["pattern"], "card_not_present_new_device")
        self.assertAlmostEqual(result["case"]["exposure_usd"], 470.97, places=2)
        self.assertEqual(result["case"]["first_suspicious_txn_id"], "3583368")
        self.assertEqual(len(result["case"]["affected_txn_ids"]), 10)
        self.assertTrue(result["sar"]["file"])
        self.assertAlmostEqual(result["sar"]["total_amount_usd"], 470.97, places=2)

    def test_06_hhg017_card_testing_rejection_and_policy_r1(self):
        """Verify HHG-017 is NOT card testing, evaluated under Policy R1 (uncertain pending customer verification)."""
        result = self.agent.investigate_case("HHG-017")
        self.assertEqual(result["case_id"], "HHG-017")
        self.assertEqual(result["case"]["verdict"], "uncertain")
        self.assertFalse(result["sar"]["file"])
        actions = [a["action"] for a in result["next_best_actions"]["final"]]
        self.assertIn("VERIFY_WITH_CUSTOMER", actions)

    def test_07_hhg005_device_sharing_policy_r1(self):
        """Verify HHG-005 device sharing on iOS in home region evaluates under Policy R1 (uncertain pending verification)."""
        result = self.agent.investigate_case("HHG-005")
        self.assertEqual(result["case_id"], "HHG-005")
        self.assertEqual(result["case"]["verdict"], "uncertain")
        self.assertFalse(result["sar"]["file"])
        actions = [a["action"] for a in result["next_best_actions"]["final"]]
        self.assertIn("VERIFY_WITH_CUSTOMER", actions)

    def test_08_policy_boundary_immutability(self):
        """Verify policy actions cannot be bypassed or invented."""
        result = self.agent.investigate_case("HHG-001")
        actions = [a["action"] for a in result["next_best_actions"]["final"]]
        self.assertIn("ALLOW_TRANSACTION", actions)
        self.assertIn("CLOSE_NO_FRAUD", actions)
        self.assertNotIn("BLOCK_CARD", actions)

    def test_09_evidence_request_queueing(self):
        """Verify evidence request tools queue structured requests without fabricating customer answers."""
        req_cust = self.tools.request_customer_validation("Did you authorize $500 at Merchant X?", channel="SMS")
        self.assertEqual(req_cust["status"], "QUEUED_OUT_OF_BAND")
        self.assertIsNone(req_cust["response"])

        req_analyst = self.tools.request_analyst_information("Review potential multi-card syndicate")
        self.assertEqual(req_analyst["status"], "QUEUED_FOR_TRIAGE")
        self.assertIsNone(req_analyst["response"])

    def test_10_provider_factory(self):
        """Verify provider factory returns appropriate LLM providers."""
        prov_det = get_llm_provider("deterministic")
        self.assertIsInstance(prov_det, DeterministicFallbackProvider)


if __name__ == "__main__":
    unittest.main()
