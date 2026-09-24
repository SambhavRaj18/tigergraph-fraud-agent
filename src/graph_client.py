"""
TigerGraph Savanna Client for Fraud Investigation Agent.
Handles token lifecycle and executes installed GSQL queries.
"""

import os
import requests
import urllib3
from typing import Dict, Any, Optional
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TigerGraphClient:
    def __init__(self, env_path: Optional[str] = None):
        if env_path:
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
        else:
            # Check local working directory or relative project root .env
            local_env = os.path.join(os.getcwd(), ".env")
            if os.path.exists(local_env):
                load_dotenv(local_env, override=False)
            else:
                repo_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
                if os.path.exists(repo_env):
                    load_dotenv(repo_env, override=False)

        # Also check Streamlit Cloud secrets if available
        st_host = ""
        st_secret = ""
        st_graph = ""
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                st_host = str(st.secrets.get("TG_HOST", "") or "")
                st_secret = str(st.secrets.get("TG_SECRET", "") or "")
                st_graph = str(st.secrets.get("TG_GRAPHNAME", st.secrets.get("TG_GRAPH", "")) or "")
        except Exception:
            pass

        self.host = (os.getenv("TG_HOST", "") or st_host).strip().rstrip("/")
        self.secret = (os.getenv("TG_SECRET", "") or st_secret).strip()
        self.graph = (os.getenv("TG_GRAPHNAME", os.getenv("TG_GRAPH", "")) or st_graph or "FraudInvestigation").strip()
        self.token: Optional[str] = None

        if not self.host or not self.secret:
            raise ValueError("TG_HOST or TG_SECRET missing from environment! Please configure TG_HOST and TG_SECRET in your .env file or Streamlit Cloud Secrets.")

    def get_token(self) -> str:
        """Fetch or refresh JWT authentication token."""
        url = f"{self.host}/gsql/v1/tokens"
        resp = requests.post(url, json={"secret": self.secret, "graph": self.graph, "lifetime": 1000000}, verify=False, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Token acquisition error {resp.status_code}: {resp.text}")
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(f"JWT Token error: {data.get('message')}")
        self.token = data.get("token")
        return self.token

    def run_investigation_query(self, transaction_id: str) -> Dict[str, Any]:
        """Runs installed investigate_transaction query for a target transaction ID."""
        if not self.token:
            self.get_token()

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.host}/restpp/query/{self.graph}/investigate_transaction?target_txn={transaction_id}"
        
        resp = requests.get(url, headers=headers, verify=False, timeout=60)
        if resp.status_code == 403 or resp.status_code == 401:
            # Refresh token once
            self.get_token()
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(url, headers=headers, verify=False, timeout=60)

        if resp.status_code != 200:
            raise RuntimeError(f"Query execution error {resp.status_code}: {resp.text}")

        data = resp.json()
        if data.get("error"):
            raise RuntimeError(f"TigerGraph query error: {data.get('message')}")

        # Normalize results list into a dictionary
        results_dict: Dict[str, Any] = {}
        for item in data.get("results", []):
            for k, v in item.items():
                results_dict[k] = v

        return results_dict

    def write_case_to_graph(
        self,
        case_id: str,
        customer_id: str,
        card_id: str,
        opened_at: str,
        closed_at: str,
        status: str,
        outcome: str,
        pattern: str,
        first_fraud_txn_id: str,
        n_txns: int,
        exposure_usd: float,
        actions_taken: str,
        report_filed: bool,
        analyst_notes: str,
        affected_txn_ids: Optional[list] = None,
        connected_card_ids: Optional[list] = None,
    ) -> bool:
        """Writes/upserts a closed investigation case and its incident edges into TigerGraph."""
        if not self.token:
            self.get_token()

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.host}/restpp/graph/{self.graph}"

        vertices = {
            "ClosedCase": {
                case_id: {
                    "customer_id": {"value": customer_id},
                    "card_id": {"value": card_id},
                    "opened_at": {"value": opened_at},
                    "closed_at": {"value": closed_at},
                    "status": {"value": status},
                    "outcome": {"value": outcome},
                    "pattern": {"value": pattern},
                    "first_fraud_txn_id": {"value": first_fraud_txn_id or ""},
                    "n_txns": {"value": n_txns},
                    "exposure_usd": {"value": round(float(exposure_usd), 2)},
                    "actions_taken": {"value": actions_taken},
                    "report_filed": {"value": report_filed},
                    "analyst_notes": {"value": analyst_notes[:500] if analyst_notes else ""},
                }
            }
        }

        edges: Dict[str, Any] = {"ClosedCase": {case_id: {}}}

        if card_id:
            edges["ClosedCase"][case_id]["ON_CARD"] = {"Card": {card_id: {}}}

        if affected_txn_ids:
            edges["ClosedCase"][case_id]["INVOLVES"] = {
                "Transaction": {str(t): {} for t in affected_txn_ids}
            }

        if connected_card_ids:
            edges["ClosedCase"][case_id]["CONNECTED_TO"] = {
                "Card": {str(c): {} for c in connected_card_ids if str(c) != card_id}
            }

        payload = {"vertices": vertices, "edges": edges}

        resp = requests.post(url, json=payload, headers=headers, verify=False, timeout=30)
        if resp.status_code == 403 or resp.status_code == 401:
            self.get_token()
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(url, json=payload, headers=headers, verify=False, timeout=30)

        if resp.status_code != 200:
            return False

        data = resp.json()
        return not data.get("error", False)

