"""Grok Responses API client (x_search)."""

import json
import sys

import requests

from config import XAI_API_KEY, GROK_API_BASE, GROK_MODEL, GROK_TIMEOUT


def search(
    prompt: str,
    *,
    from_date: str = None,
    to_date: str = None,
) -> dict:
    """Call Grok Responses API with x_search tool.

    Returns the raw API response dict.
    """
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY not set. Check ~/.claude/mcp-servers/x-search-mcp/.env")

    tool = {"type": "x_search"}
    if from_date:
        tool["from_date"] = from_date
    if to_date:
        tool["to_date"] = to_date

    body = {
        "model": GROK_MODEL,
        "input": [{"role": "user", "content": prompt}],
        "tools": [tool],
    }

    resp = requests.post(
        f"{GROK_API_BASE}/responses",
        headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=GROK_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def extract_text(response: dict) -> str:
    """Extract text content from Grok API response."""
    output = response.get("output", [])
    parts = []
    for item in output:
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    parts.append(c.get("text", ""))
        elif isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts) if parts else json.dumps(response, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Quick test
    r = search("What are the top 3 trending topics on X right now? Reply in 3 bullet points.")
    print(extract_text(r))
