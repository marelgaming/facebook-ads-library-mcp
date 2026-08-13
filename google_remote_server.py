import os
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from google_ads_transparency_mcp.scraper import GoogleAdsTransparency


INSTRUCTIONS = """
Remote read-only MCP server for researching competitor ads in Google's Ads Transparency Center.

Use region="GB" for UK-specific research. Use "anywhere" for global research.
No API key is required.
"""


mcp = FastMCP(
    name="Google Ads Transparency",
    instructions=INSTRUCTIONS,
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request):
    return JSONResponse({"status": "ok"})


def _client(region: str = "anywhere") -> GoogleAdsTransparency:
    region = (region or "anywhere").strip()
    return GoogleAdsTransparency(region=region)


@mcp.tool(
    description="Find a Google Ads Transparency advertiser by website domain. Use region='GB' for UK-specific results.",
    annotations={"title": "Find Google Advertiser by Domain", "readOnlyHint": True, "openWorldHint": True},
)
def search_advertiser_by_domain(domain: str, region: str = "anywhere") -> Dict[str, Any]:
    if not domain or not domain.strip():
        return {"success": False, "error": "domain cannot be empty"}
    try:
        result = _client(region).search_advertiser_by_domain(domain.strip())
        return {"success": True, "result": result, "region": region}
    except Exception as exc:
        return {"success": False, "error": str(exc), "region": region}


@mcp.tool(
    description="Search Google Ads Transparency advertisers by company name or keyword. Use region='GB' for UK-specific research.",
    annotations={"title": "Search Google Advertisers", "readOnlyHint": True, "openWorldHint": True},
)
def search_advertisers(query: str, region: str = "anywhere") -> Dict[str, Any]:
    if not query or not query.strip():
        return {"success": False, "error": "query cannot be empty"}
    try:
        results = _client(region).search_advertisers(query.strip())
        return {"success": True, "results": results, "count": len(results), "region": region}
    except Exception as exc:
        return {"success": False, "error": str(exc), "region": region}


@mcp.tool(
    description="Get Google Ads Transparency creatives for an advertiser, including decoded text ad content where available. Use region='GB' for UK.",
    annotations={"title": "Get Google Advertiser Ads", "readOnlyHint": True, "openWorldHint": True},
)
def get_ads(advertiser_name: str, count: int = 10, region: str = "anywhere") -> Dict[str, Any]:
    if not advertiser_name or not advertiser_name.strip():
        return {"success": False, "error": "advertiser_name cannot be empty"}
    count = max(1, min(int(count), 100))
    try:
        results = _client(region).get_ads(advertiser_name.strip(), count=count)
        return {"success": True, "results": results, "count": len(results), "region": region}
    except Exception as exc:
        return {"success": False, "error": str(exc), "region": region}


@mcp.tool(
    description="Get full details for one Google ad creative by advertiser ID and creative ID.",
    annotations={"title": "Get Google Ad Detail", "readOnlyHint": True, "openWorldHint": True},
)
def get_ad_detail(advertiser_id: str, creative_id: str, region: str = "anywhere") -> Dict[str, Any]:
    if not advertiser_id or not creative_id:
        return {"success": False, "error": "advertiser_id and creative_id are required"}
    try:
        result = _client(region).get_ad_detail(advertiser_id.strip(), creative_id.strip())
        return {"success": True, "result": result, "region": region}
    except Exception as exc:
        return {"success": False, "error": str(exc), "region": region}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
