"""
TigerGraph MCP Client.
Spawns the TigerGraph MCP server subprocess and connects over standard IO transport.
Provides high-level synchronous tool invocation methods for the Investigation Agent.
"""

import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("MCPClient")


class TigerGraphMCPClient:
    def __init__(self, server_script_path: Optional[str] = None):
        default_server = os.path.abspath(os.path.join(os.path.dirname(__file__), "server.py"))
        self.server_script_path = server_script_path or default_server
        self.python_exe = sys.executable

    def _get_server_params(self) -> StdioServerParameters:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        env_dict = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": project_root
        }
        return StdioServerParameters(
            command=self.python_exe,
            args=[self.server_script_path],
            env=env_dict
        )

    async def _async_list_tools(self) -> List[Dict[str, Any]]:
        server_params = self._get_server_params()
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": getattr(tool, "input_schema", getattr(tool, "inputSchema", None))
                    }
                    for tool in tools_result.tools
                ]

    async def _async_call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        server_params = self._get_server_params()
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments=arguments)
                if result.content and len(result.content) > 0:
                    c = result.content[0]
                    if hasattr(c, "text"):
                        text_val = c.text
                        try:
                            return json.loads(text_val)
                        except (json.JSONDecodeError, TypeError):
                            return text_val
                    elif hasattr(c, "data"):
                        return c.data
                return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools exposed by the TigerGraph MCP server."""
        return asyncio.run(self._async_list_tools())

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool synchronously."""
        return asyncio.run(self._async_call_tool(name, arguments))

    def investigate_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Convenience method for investigate_transaction MCP tool."""
        return self.call_tool("investigate_transaction", {"transaction_id": str(transaction_id)})

    def analyze_evidence(self, transaction_id: str) -> Dict[str, Any]:
        """Convenience method for analyze_evidence MCP tool."""
        return self.call_tool("analyze_evidence", {"transaction_id": str(transaction_id)})

    def get_similar_closed_cases(self, case_ids: List[str]) -> List[Dict[str, Any]]:
        """Convenience method for get_similar_closed_cases MCP tool."""
        return self.call_tool("get_similar_closed_cases", {"case_ids": case_ids})

    def get_policy_rule(self, rule_id: str) -> Dict[str, str]:
        """Convenience method for get_policy_rule MCP tool."""
        return self.call_tool("get_policy_rule", {"rule_id": str(rule_id)})
