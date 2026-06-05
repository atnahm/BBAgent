"""Model Context Protocol (MCP) server exposing BBAgent tools to external AI Assistants."""
from typing import Dict, Any, List
import json
import asyncio
import sys

from backend.core.orchestrator import Orchestrator
from backend.memory.relational_db import Transaction

# Extremely minimal MCP JSON-RPC Server implementation for demonstration.
# In a real environment, you'd use a dedicated library like standard `mcp`.

class MCPServer:
    def __init__(self):
        self.orchestrator = Orchestrator()

    async def get_invoice_status(self, invoice_number: str) -> str:
        """MCP Tool: Retrieves the status of a specific invoice."""
        db_session = self.orchestrator.db.get_session()
        try:
            txn = db_session.query(Transaction).filter_by(invoice_number=invoice_number).first()
            if not txn:
                return f"Invoice {invoice_number} not found."

            return json.dumps({
                "invoice_number": txn.invoice_number,
                "status": txn.status,
                "days_overdue": txn.days_overdue,
                "amount": txn.amount,
                "currency": txn.currency
            })
        finally:
            db_session.close()

    async def get_compliance_rules(self, country_code: str) -> str:
        """MCP Tool: Retrieves compliance rules for a specific country."""
        from backend.compliance.rag_loader import ComplianceRAGLoader
        loader = ComplianceRAGLoader(self.orchestrator.vector_memory)
        # Mock load in case it's empty
        loader.load_mock_rules()

        results = loader.fetch_rules_for_country(country_code)
        if not results:
            return f"No rules found for {country_code}."

        return json.dumps([r['document'] for r in results])

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        response = {"jsonrpc": "2.0", "id": request_id}

        try:
            if method == "get_invoice_status":
                result = await self.get_invoice_status(params.get("invoice_number"))
                response["result"] = result
            elif method == "get_compliance_rules":
                result = await self.get_compliance_rules(params.get("country_code"))
                response["result"] = result
            elif method == "tools/list":
                response["result"] = {
                    "tools": [
                        {
                            "name": "get_invoice_status",
                            "description": "Get status of an invoice by number",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"invoice_number": {"type": "string"}},
                                "required": ["invoice_number"]
                            }
                        },
                        {
                            "name": "get_compliance_rules",
                            "description": "Get compliance rules for a country",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"country_code": {"type": "string"}},
                                "required": ["country_code"]
                            }
                        }
                    ]
                }
            else:
                response["error"] = {"code": -32601, "message": "Method not found"}

        except Exception as e:
            response["error"] = {"code": -32603, "message": str(e)}

        return response

    async def run(self):
        """Read stdin line by line and process requests."""
        loop = asyncio.get_running_loop()

        while True:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                request = json.loads(line)
                response = await self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                pass
            except Exception as e:
                response = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.run())
