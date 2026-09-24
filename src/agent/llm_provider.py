"""
LLM Provider Abstraction for Fraud Investigation Agent.
Supports Gemini, OpenAI, and Deterministic Fallback Provider.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("LLMProvider")


@dataclass
class ToolSelection:
    tool_name: str
    arguments: Dict[str, Any]
    rationale: str
    is_terminal: bool = False
    stop_reason: Optional[str] = None


@dataclass
class SynthesisResult:
    summary: str
    rationale: str
    key_evidence: List[str]
    uncertainty: List[str]


class LLMProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    @abstractmethod
    def select_next_action(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        state_summary: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> ToolSelection:
        """Determines the next tool to invoke or signals investigation termination."""
        pass

    @abstractmethod
    def synthesize_investigation(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        evidence: Dict[str, Any],
        policy_decision: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> SynthesisResult:
        """Synthesizes the final investigation summary and rationale."""
        pass


class DeterministicFallbackProvider(LLMProvider):
    """
    High-fidelity deterministic LLM provider.
    Enforces rigorous investigation paths, transparent reasoning, and tool selection
    without requiring external API keys or network connectivity.
    """

    def select_next_action(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        state_summary: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> ToolSelection:
        executed_tools = [h["tool"] for h in tool_history]
        flagged_txn = trigger.get("flagged_txn_id", "")
        customer_id = trigger.get("customer_id", "")

        # 1. If we haven't retrieved the graph subgraph for the flagged transaction, do that first.
        if "investigate_transaction" not in executed_tools and flagged_txn:
            return ToolSelection(
                tool_name="investigate_transaction",
                arguments={"transaction_id": flagged_txn},
                rationale=f"Retrieve multi-hop transaction subgraph, customer profile, and connected entities for flagged txn {flagged_txn}."
            )

        # 2. If we have raw graph data but haven't analyzed baseline/geographic/pattern signals, analyze evidence.
        if "analyze_evidence" not in executed_tools and state_summary.get("has_raw_graph_data"):
            return ToolSelection(
                tool_name="analyze_evidence",
                arguments={"transaction_id": flagged_txn},
                rationale="Compute statistical baseline, geographic distance, device sharing, and fraud pattern features."
            )

        # 3. If closed cases exist in graph data and we haven't retrieved historical details, retrieve them.
        related_cases = state_summary.get("related_closed_cases", [])
        if "get_similar_closed_cases" not in executed_tools and "retrieve_historical_case_details" not in executed_tools and len(related_cases) > 0:
            return ToolSelection(
                tool_name="get_similar_closed_cases",
                arguments={"case_ids": related_cases[:5]},
                rationale=f"Examine {len(related_cases)} related historical closed cases in TigerGraph memory to identify precedent patterns."
            )

        # 4. If we haven't evaluated policy decision against R1-R10, evaluate policy.
        if "evaluate_policy_decision" not in executed_tools and state_summary.get("has_analyzed_evidence"):
            return ToolSelection(
                tool_name="evaluate_policy_decision",
                arguments={"case_id": case_id, "trigger_type": trigger.get("trigger_type", "")},
                rationale="Evaluate deterministic policy rules R1-R10, assess pattern conditions, calculate exposure, and generate actions."
            )

        # 5. If policy decision is evaluated, terminate reasoning and write to graph memory.
        return ToolSelection(
            tool_name="stop_investigation",
            arguments={},
            rationale="All necessary graph evidence, baseline metrics, historical precedent, and policy rules have been evaluated.",
            is_terminal=True,
            stop_reason="sufficient_evidence"
        )

    def synthesize_investigation(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        evidence: Dict[str, Any],
        policy_decision: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> SynthesisResult:
        case_info = policy_decision.get("case", {})
        verdict = case_info.get("verdict", "legitimate")
        pattern = case_info.get("pattern", "none")
        prob = case_info.get("fraud_probability", 0.0)
        exposure = case_info.get("exposure_usd", 0.0)
        summary = case_info.get("summary", "")
        
        # Build synthesis rationale
        key_ev = []
        txn = evidence.get("target_transaction", {})
        geo = evidence.get("geographic_analysis", {})
        base = evidence.get("customer_baseline_statistics", {})
        dev = evidence.get("device_analysis", {})
        
        key_ev.append(f"Target transaction {txn.get('transaction_id')} for ${txn.get('amount', 0.0):.2f} (channel: {txn.get('channel')}, risk_score: {txn.get('risk_score')}).")
        key_ev.append(f"Customer baseline: {base.get('total_transactions', 0)} historical transactions, avg amount ${base.get('avg_amount', 0.0):.2f}.")
        key_ev.append(f"Billing region: {geo.get('target_billing_region')} (historical count: {geo.get('target_region_historical_count', 0)}, pct: {geo.get('target_region_percentage', 0.0):.1f}%).")
        
        if dev.get("device_id"):
            key_ev.append(f"Device: {dev.get('device_id')} ({dev.get('device_type')}, OS: {dev.get('os_family')}). Shared with {len(dev.get('shared_customers', []))} other customers.")

        rationale = (
            f"Investigation concluded with verdict '{verdict}' under pattern '{pattern}' (probability={prob:.2f}, exposure=${exposure:.2f}). "
            f"Evaluated across {len(tool_history)} investigation steps. {summary}"
        )

        uncertainty = policy_decision.get("case", {}).get("uncertainty", [])
        if not uncertainty:
            uncertainty = ["None; sufficient evidence gathered across TigerGraph multi-hop neighborhood."]

        return SynthesisResult(
            summary=summary,
            rationale=rationale,
            key_evidence=key_ev,
            uncertainty=uncertainty
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        st_openai_key = ""
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                st_openai_key = str(st.secrets.get("OPENAI_API_KEY", "") or "")
        except Exception:
            pass

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or st_openai_key
        self.model = os.environ.get("LLM_MODEL", model)
        self.fallback = DeterministicFallbackProvider()
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found; will fallback to DeterministicFallbackProvider.")

    def select_next_action(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        state_summary: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> ToolSelection:
        if not self.api_key:
            return self.fallback.select_next_action(case_id, trigger, available_tools, state_summary, tool_history)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            system_prompt = (
                "You are an expert fraud investigation AI agent operating over TigerGraph Savanna. "
                "Your objective is to investigate the given fraud alert by selecting the next best tool to gather evidence, "
                "analyze patterns (card_testing, card_not_present_fraud, card_not_present_new_device, out_of_region_use, account_takeover), "
                "and apply policy rules. Select a tool or choose 'stop_investigation' if enough evidence has been collected."
            )

            prompt = {
                "case_id": case_id,
                "trigger": trigger,
                "available_tools": [t["name"] for t in available_tools],
                "state_summary": state_summary,
                "tool_history": tool_history
            }

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Decide the next action for this fraud investigation:\n{json.dumps(prompt, indent=2)}\nRespond in JSON format: {{\"tool_name\": string, \"arguments\": object, \"rationale\": string, \"is_terminal\": boolean, \"stop_reason\": string or null}}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            data = json.loads(response.choices[0].message.content)
            return ToolSelection(
                tool_name=data.get("tool_name", "stop_investigation"),
                arguments=data.get("arguments", {}),
                rationale=data.get("rationale", "LLM-driven tool selection."),
                is_terminal=data.get("is_terminal", False) or data.get("tool_name") == "stop_investigation",
                stop_reason=data.get("stop_reason")
            )
        except Exception as e:
            logger.warning(f"OpenAI call failed ({e}); falling back to deterministic provider.")
            return self.fallback.select_next_action(case_id, trigger, available_tools, state_summary, tool_history)

    def synthesize_investigation(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        evidence: Dict[str, Any],
        policy_decision: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> SynthesisResult:
        if not self.api_key:
            return self.fallback.synthesize_investigation(case_id, trigger, evidence, policy_decision, tool_history)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            system_prompt = (
                "You are an expert fraud investigator summarizing the final investigation findings. "
                "Synthesize a concise, factual narrative without altering the deterministic verdict, pattern, or policy actions."
            )

            prompt = {
                "case_id": case_id,
                "trigger": trigger,
                "evidence_summary": {
                    "target_transaction": evidence.get("target_transaction"),
                    "geographic": evidence.get("geographic_analysis"),
                    "device": evidence.get("device_analysis"),
                    "baseline": evidence.get("customer_baseline_statistics")
                },
                "policy_decision": policy_decision.get("case"),
                "tool_history": tool_history
            }

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Synthesize final investigation narrative:\n{json.dumps(prompt, indent=2)}\nRespond in JSON format: {{\"summary\": string, \"rationale\": string, \"key_evidence\": [string], \"uncertainty\": [string]}}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            data = json.loads(response.choices[0].message.content)
            return SynthesisResult(
                summary=data.get("summary", policy_decision.get("case", {}).get("summary", "")),
                rationale=data.get("rationale", ""),
                key_evidence=data.get("key_evidence", []),
                uncertainty=data.get("uncertainty", policy_decision.get("case", {}).get("uncertainty", []))
            )
        except Exception as e:
            logger.warning(f"OpenAI synthesis failed ({e}); falling back to deterministic provider.")
            return self.fallback.synthesize_investigation(case_id, trigger, evidence, policy_decision, tool_history)


class GeminiProvider(LLMProvider):
    """Google Gemini API Provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3.5-flash",
        strict: bool = True
    ):
        from dotenv import load_dotenv
        local_env = os.path.join(os.getcwd(), ".env")
        if os.path.exists(local_env):
            load_dotenv(local_env, override=False)
        else:
            repo_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
            if os.path.exists(repo_env):
                load_dotenv(repo_env, override=False)

        st_gemini_key = ""
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                st_gemini_key = str(st.secrets.get("GEMINI_API_KEY", st.secrets.get("GOOGLE_API_KEY", "")) or "")
        except Exception:
            pass

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or st_gemini_key
        self.model = os.environ.get("LLM_MODEL", model)
        self.strict = strict
        self.real_api_calls = 0
        self.fallback = DeterministicFallbackProvider()
        if not self.api_key:
            if self.strict:
                logger.error("GEMINI_API_KEY is not set in environment, .env file, or Streamlit Cloud Secrets.")
            else:
                logger.warning("GEMINI_API_KEY not found; will fallback to DeterministicFallbackProvider.")

    def select_next_action(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        state_summary: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> ToolSelection:
        if not self.api_key:
            if self.strict:
                raise RuntimeError("GEMINI_API_KEY is missing from environment / .env file.")
            return self.fallback.select_next_action(case_id, trigger, available_tools, state_summary, tool_history)

        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        system_instruction = (
            "You are an expert fraud investigation AI agent operating over TigerGraph Savanna. "
            "Your task is to iteratively investigate the case alert by selecting the next best tool to gather graph evidence, "
            "compute customer baseline statistics, evaluate fraud patterns, and consult policy rules.\n\n"
            "Allowed Tools:\n"
            "- investigate_transaction: args {\"transaction_id\": string}\n"
            "- analyze_evidence: args {\"transaction_id\": string}\n"
            "- get_similar_closed_cases: args {\"case_ids\": [string]}\n"
            "- get_policy_rule: args {\"rule_id\": string}\n"
            "- evaluate_policy_decision: args {\"case_id\": string, \"trigger_type\": string}\n"
            "- stop_investigation: args {}\n\n"
            "If all necessary graph evidence, baseline metrics, historical precedent, and policy rules have been evaluated, "
            "choose 'stop_investigation' with is_terminal=true.\n"
            "Always respond strictly with valid JSON conforming to: "
            "{\"tool_name\": string, \"arguments\": object, \"rationale\": string, \"is_terminal\": boolean, \"stop_reason\": string or null}"
        )

        prompt_payload = {
            "case_id": case_id,
            "trigger": trigger,
            "state_summary": state_summary,
            "tool_history": tool_history
        }

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [{
                "role": "user",
                "parts": [{
                    "text": f"Current Investigation State:\n{json.dumps(prompt_payload, indent=2)}\n\nSelect the next best action:"
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        }

        import time
        max_retries = 5
        for attempt in range(max_retries):
            self.real_api_calls += 1
            res = requests.post(url, json=payload, timeout=45)
            if res.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                retry_seconds = 5 * (2 ** attempt)  # 5s, 10s, 20s, 40s...
                if res.status_code == 429:
                    try:
                        res_err = res.json()
                        for detail in res_err.get("error", {}).get("details", []):
                            if detail.get("@type", "").endswith("RetryInfo"):
                                d_str = detail.get("retryDelay", "20s").rstrip("s")
                                retry_seconds = max(int(float(d_str)) + 2, 5)
                    except Exception:
                        pass
                logger.warning(f"Gemini API returned HTTP {res.status_code}. Waiting {retry_seconds}s before retry (attempt {attempt+1}/{max_retries})...")
                time.sleep(retry_seconds)
                continue
            
            if res.status_code != 200:
                err_msg = f"Gemini API returned HTTP {res.status_code}: {res.text}"
                logger.error(err_msg)
                if self.strict:
                    raise RuntimeError(err_msg)
                return self.fallback.select_next_action(case_id, trigger, available_tools, state_summary, tool_history)

            try:
                res_json = res.json()
                candidates = res_json.get("candidates", [])
                if not candidates:
                    raise ValueError(f"No candidates returned in Gemini response: {res.text}")
                
                raw_text = candidates[0]["content"]["parts"][0]["text"]
                data = json.loads(raw_text)
                
                tool_name = data.get("tool_name", "stop_investigation")
                arguments = data.get("arguments", {})
                rationale = data.get("rationale", "Gemini-selected investigation step.")
                is_terminal = data.get("is_terminal", False) or tool_name == "stop_investigation"
                stop_reason = data.get("stop_reason")

                return ToolSelection(
                    tool_name=tool_name,
                    arguments=arguments,
                    rationale=rationale,
                    is_terminal=is_terminal,
                    stop_reason=stop_reason
                )
            except Exception as e:
                logger.error(f"Failed to parse Gemini tool selection ({e})")
                if self.strict:
                    raise RuntimeError(f"Failed to parse Gemini response: {e}")
                return self.fallback.select_next_action(case_id, trigger, available_tools, state_summary, tool_history)

    def synthesize_investigation(
        self,
        case_id: str,
        trigger: Dict[str, Any],
        evidence: Dict[str, Any],
        policy_decision: Dict[str, Any],
        tool_history: List[Dict[str, Any]]
    ) -> SynthesisResult:
        if not self.api_key:
            if self.strict:
                raise RuntimeError("GEMINI_API_KEY is missing from environment / .env file.")
            return self.fallback.synthesize_investigation(case_id, trigger, evidence, policy_decision, tool_history)

        import requests
        import time
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        prompt_payload = {
            "case_id": case_id,
            "trigger": trigger,
            "evidence_summary": {
                "target_transaction": evidence.get("target_transaction"),
                "geographic": evidence.get("geographic_analysis"),
                "device": evidence.get("device_analysis"),
                "baseline": evidence.get("customer_baseline_statistics")
            },
            "policy_decision": policy_decision.get("case"),
            "tool_history": tool_history
        }

        payload = {
            "system_instruction": {
                "parts": [{
                    "text": (
                        "You are an expert fraud investigator summarizing the final investigation findings. "
                        "Synthesize a concise executive narrative and list key evidence without altering the deterministic verdict, pattern, or policy actions. "
                        "Respond strictly with valid JSON: {\"summary\": string, \"rationale\": string, \"key_evidence\": [string], \"uncertainty\": [string]}"
                    )
                }]
            },
            "contents": [{
                "role": "user",
                "parts": [{
                    "text": f"Completed Investigation Data:\n{json.dumps(prompt_payload, indent=2)}"
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        }

        max_retries = 5
        for attempt in range(max_retries):
            self.real_api_calls += 1
            res = requests.post(url, json=payload, timeout=45)
            if res.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                retry_seconds = 5 * (2 ** attempt)
                if res.status_code == 429:
                    try:
                        res_err = res.json()
                        for detail in res_err.get("error", {}).get("details", []):
                            if detail.get("@type", "").endswith("RetryInfo"):
                                d_str = detail.get("retryDelay", "20s").rstrip("s")
                                retry_seconds = max(int(float(d_str)) + 2, 5)
                    except Exception:
                        pass
                logger.warning(f"Gemini API returned HTTP {res.status_code}. Waiting {retry_seconds}s before retry (attempt {attempt+1}/{max_retries})...")
                time.sleep(retry_seconds)
                continue

            if res.status_code != 200:
                err_msg = f"Gemini API returned HTTP {res.status_code}: {res.text}"
                logger.error(err_msg)
                if self.strict:
                    raise RuntimeError(err_msg)
                return self.fallback.synthesize_investigation(case_id, trigger, evidence, policy_decision, tool_history)

            try:
                res_json = res.json()
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(raw_text)
                return SynthesisResult(
                    summary=data.get("summary", policy_decision.get("case", {}).get("summary", "")),
                    rationale=data.get("rationale", ""),
                    key_evidence=data.get("key_evidence", []),
                    uncertainty=data.get("uncertainty", policy_decision.get("case", {}).get("uncertainty", []))
                )
            except Exception as e:
                if self.strict:
                    raise RuntimeError(f"Failed to parse Gemini synthesis response: {e}")
                return self.fallback.synthesize_investigation(case_id, trigger, evidence, policy_decision, tool_history)


def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider_name = (provider_type or os.environ.get("LLM_PROVIDER", "deterministic")).lower()
    
    if provider_name in ["gemini", "google"]:
        return GeminiProvider()
    elif provider_name in ["openai", "gpt"]:
        return OpenAIProvider()
    elif provider_name in ["deterministic", "mock", "fallback"]:
        return DeterministicFallbackProvider()
    else:
        logger.info(f"Unknown provider '{provider_name}', defaulting to DeterministicFallbackProvider.")
        return DeterministicFallbackProvider()
