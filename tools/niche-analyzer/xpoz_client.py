"""Xpoz MCP HTTP client for Twitter/Reddit/Instagram data.

Xpoz uses MCP Streamable HTTP transport (SSE responses).
All operations are async: tool call → operationId → poll checkOperationStatus.
Response text is YAML-like (not JSON).
"""

import json
import re
import sys
import time

import requests

from config import load_xpoz_config, XPOZ_POLL_INTERVAL, XPOZ_MAX_WAIT


class XpozClient:
    """Client for Xpoz MCP server via HTTP (Streamable HTTP transport)."""

    def __init__(self):
        url, token = load_xpoz_config()
        if not url or not token:
            raise RuntimeError("Xpoz MCP not configured in ~/.claude.json")
        self.url = url
        self.token = token
        self._request_id = 0
        self._initialized = False

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _parse_sse(self, text: str) -> dict:
        """Extract JSON-RPC response from SSE formatted response."""
        for line in text.split("\n"):
            if line.startswith("data: "):
                return json.loads(line[6:])
        return json.loads(text)

    def _extract_text(self, data: dict) -> str:
        """Extract text content from MCP result."""
        if "error" in data:
            raise RuntimeError(f"Xpoz error: {json.dumps(data['error'])}")
        result = data.get("result", {})
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                return item.get("text", "")
        return ""

    def _post(self, body: dict) -> dict:
        """Send JSON-RPC request and parse SSE response."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
        }
        resp = requests.post(self.url, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        return self._parse_sse(resp.text)

    def _ensure_init(self):
        if self._initialized:
            return
        body = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "niche-analyzer", "version": "0.1.0"},
            },
            "id": self._next_id(),
        }
        self._post(body)
        self._initialized = True

    def _parse_yaml_text(self, text: str) -> dict:
        """Parse Xpoz YAML-like response text into a dict.

        Handles three formats:
        1. Simple: ``success: true``
        2. Nested: ``data:\n  results: 659287``
        3. Array:  ``data:\n  results[143]{id,username,followersCount}:\n    "id1",user1,100``
        """
        result = {}
        lines = text.strip().split("\n")
        current_key = None
        # For parsing results[N]{fields}: rows
        row_fields = None  # list of field names when inside a results block
        rows_list = []

        for line in lines:
            # Check for results[N]{fields}: header inside a nested section
            if current_key and row_fields is None:
                m_arr = re.match(r'^\s+results\[\d+\]\{([^}]+)\}:', line)
                if m_arr:
                    row_fields = [f.strip() for f in m_arr.group(1).split(",")]
                    rows_list = []
                    continue

            # If we're inside a results block, parse CSV rows
            if row_fields is not None and line.startswith("    "):
                row = self._parse_csv_row(line.strip(), row_fields)
                if row:
                    rows_list.append(row)
                continue

            # If we were in a results block but hit a non-row line, finalize
            if row_fields is not None and not line.startswith("    "):
                if isinstance(result.get(current_key), dict):
                    result[current_key]["rows"] = rows_list
                row_fields = None
                rows_list = []
                # Fall through to parse this line normally

            # Top-level key: value
            m = re.match(r'^(\w+):\s*(.*)$', line)
            if m and not line.startswith("  "):
                key, val = m.group(1), m.group(2).strip()
                if val:
                    result[key] = self._coerce_value(val)
                    current_key = None
                else:
                    result[key] = {}
                    current_key = key
            elif current_key and line.startswith("  "):
                m2 = re.match(r'^\s+(\w+):\s*(.+)$', line)
                if m2:
                    nkey, nval = m2.group(1), m2.group(2).strip()
                    nval = self._coerce_value(nval)
                    if isinstance(result[current_key], dict):
                        result[current_key][nkey] = nval

        # Finalize if file ends while inside a results block
        if row_fields is not None and current_key and isinstance(result.get(current_key), dict):
            result[current_key]["rows"] = rows_list

        return result

    @staticmethod
    def _coerce_value(val: str):
        """Convert string value to int/float/bool, or strip quotes."""
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        return val

    @staticmethod
    def _parse_csv_row(line: str, fields: list) -> dict:
        """Parse a CSV-like row into a dict using field names.

        Row format: ``"389805855",fabiolauria92,3841``
        """
        parts = []
        current = ""
        in_quotes = False
        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == ',' and not in_quotes:
                parts.append(current.strip().strip('"'))
                current = ""
                continue
            current += ch
        parts.append(current.strip().strip('"'))

        if len(parts) < len(fields):
            return None
        row = {}
        for i, field in enumerate(fields):
            val = parts[i] if i < len(parts) else ""
            # Try numeric conversion for known numeric fields
            try:
                val = int(val)
            except (ValueError, TypeError):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    pass
            row[field] = val
        return row

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call an MCP tool and return the raw text response."""
        self._ensure_init()
        body = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
            "id": self._next_id(),
        }
        data = self._post(body)
        return self._extract_text(data)

    def call_tool_parsed(self, name: str, arguments: dict) -> dict:
        """Call a tool, poll if async, return parsed result."""
        text = self.call_tool(name, arguments)
        parsed = self._parse_yaml_text(text)

        # Check for async operation
        op_id = parsed.get("operationId")
        if op_id:
            return self._poll_operation(str(op_id))

        return parsed

    def _poll_operation(self, operation_id: str) -> dict:
        """Poll checkOperationStatus until complete."""
        elapsed = 0.0
        while elapsed < XPOZ_MAX_WAIT:
            text = self.call_tool("checkOperationStatus", {"operationId": operation_id})
            parsed = self._parse_yaml_text(text)

            # "success: true" means completed
            if parsed.get("success") is True:
                return parsed

            # Check for explicit failure
            status = parsed.get("status", "")
            if status == "failed":
                raise RuntimeError(f"Xpoz operation failed: {text}")

            time.sleep(XPOZ_POLL_INTERVAL)
            elapsed += XPOZ_POLL_INTERVAL

        raise TimeoutError(f"Xpoz operation {operation_id} timed out after {XPOZ_MAX_WAIT}s")

    # ── Convenience methods ──

    def count_tweets(self, phrase: str, start_date: str = None, end_date: str = None) -> int:
        """Count tweets containing a phrase. Returns count."""
        args = {"phrase": phrase}
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date

        result = self.call_tool_parsed("countTweets", args)

        # Extract count from parsed YAML
        # Format: success: true / data: { results: 659287 }
        data = result.get("data", {})
        if isinstance(data, dict):
            count = data.get("results", 0)
        else:
            count = result.get("results", 0)
        return int(count) if count else 0

    def get_twitter_posts(
        self, query: str, start_date: str = None, end_date: str = None,
        fields: list = None,
    ) -> dict:
        """Search Twitter posts by keywords."""
        args = {"query": query}
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date
        if fields:
            args["fields"] = fields
        else:
            args["fields"] = ["id", "text", "likeCount", "retweetCount",
                              "viewCount", "authorUsername", "createdAt"]
        return self.call_tool_parsed("getTwitterPostsByKeywords", args)

    def get_twitter_users(self, query: str, start_date: str = None, end_date: str = None) -> dict:
        """Search Twitter users by keywords in their posts."""
        args = {"query": query}
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date
        args["fields"] = ["id", "username", "displayName", "followersCount"]
        return self.call_tool_parsed("getTwitterUsersByKeywords", args)

    def get_reddit_posts(
        self, query: str, start_date: str = None, end_date: str = None,
    ) -> dict:
        """Search Reddit posts by keywords."""
        args = {"query": query}
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date
        args["fields"] = ["id", "title", "selftext", "score", "numComments",
                          "subreddit", "createdAt"]
        return self.call_tool_parsed("getRedditPostsByKeywords", args)

    def get_instagram_posts(
        self, query: str, start_date: str = None, end_date: str = None,
    ) -> dict:
        """Search Instagram posts by keywords."""
        args = {"query": query}
        if start_date:
            args["startDate"] = start_date
        if end_date:
            args["endDate"] = end_date
        args["fields"] = ["id", "text", "likeCount", "videoPlayCount",
                          "ownerUsername", "createdAt"]
        return self.call_tool_parsed("getInstagramPostsByKeywords", args)


if __name__ == "__main__":
    client = XpozClient()
    count = client.count_tweets("AI", "2026-02-01", "2026-02-21")
    print(f"Tweets containing 'AI' (Feb 2026): {count:,}")
