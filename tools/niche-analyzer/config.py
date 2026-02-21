"""Configuration for niche-demand-analyzer."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load Grok API key from .env
_env_path = Path.home() / ".claude" / "mcp-servers" / "x-search-mcp" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ── Project paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_BASE = PROJECT_ROOT / "content" / "niche-analysis" / "scans"
YTDLP_PATH = Path.home() / "Library" / "Python" / "3.9" / "bin" / "yt-dlp"

# ── Grok API ──
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
GROK_API_BASE = "https://api.x.ai/v1"
GROK_MODEL = "grok-4-1-fast"
GROK_TIMEOUT = 120


# ── Xpoz MCP ──
def load_xpoz_config() -> tuple[str, str]:
    """Load Xpoz MCP URL and token from ~/.claude.json."""
    claude_json = Path.home() / ".claude.json"
    if not claude_json.exists():
        return "", ""
    data = json.loads(claude_json.read_text())
    xpoz = data.get("mcpServers", {}).get("xpoz-mcp", {})
    url = xpoz.get("url", "")
    auth = xpoz.get("headers", {}).get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else auth
    return url, token


# ── Defaults ──
DEFAULT_YT_RESULTS = 20
DEFAULT_TWITTER_DAYS = 30
XPOZ_POLL_INTERVAL = 2.0
XPOZ_MAX_WAIT = 120.0

# ── Stage 1 prompts ──
TREND_SCAN_PROMPT_EN = """\
Search X/Twitter for content niches where AI-generated content is performing well.
Focus on: news summaries, trivia/fun facts, history explainers, product reviews,
how-to guides, rankings, data analysis, fortune telling, educational content.
Exclude: handmade/physical products, personal services, art commissions,
travel vlogs, face-on-camera content.
Show real tweets from the last 30 days where people are building audiences
or monetizing in these content niches. Include engagement metrics.
Return as JSON array with fields: niche, description, example_tweet, author, likes, views."""

TREND_SCAN_PROMPT_JP = """\
X/Twitterで、AIを使ったコンテンツ発信で伸びているニッチを探してください。
対象: ニュースまとめ、雑学・トリビア、歴史解説、商品レビュー・比較、
ハウツー、ランキング、占い・診断、教育コンテンツ。
除外: ハンドメイド、物販、対面サービス、アートコミッション、旅行vlog、顔出し。
直近30日で、これらのニッチでフォロワーを増やしたり収益化しているツイートを
実例付きで見せてください。エンゲージメント数値も含めてください。
JSON配列で返してください: niche, description, example_tweet, author, likes, views"""
