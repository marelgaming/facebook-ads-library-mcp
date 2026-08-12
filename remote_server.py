import os
from typing import Any, Dict, List, Optional, Union

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp_types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.services.scrapecreators_service import (
    get_ads,
    get_ads_batch,
    get_platform_id,
    get_platform_ids_batch,
)


INSTRUCTIONS = """
Remote read-only MCP server for researching competitors in Meta Ad Library.

Workflow:
1. Use get_meta_platform_id to search for one or more brands and obtain Meta Page IDs.
2. Use get_meta_ads with those IDs to retrieve currently running ads.
3. Use country="GB" when the user specifically wants UK-targeted results.

The underlying Meta Ad Library data is retrieved through the ScrapeCreators API.
"""


mcp = MCPServer(
    name="Meta Ads Library",
    title="Meta Ad Library",
    description="Search competitor ads from Meta Ad Library.",
    instructions=INSTRUCTIONS,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "ok", "service": "Meta Ads Library MCP"})


@mcp.tool(
    title="Search Meta Ad Library Brands",
    description="Search Meta Ad Library for one or more brand names and return matching Meta Page IDs.",
    annotations=ToolAnnotations(
        title="Search Meta Ad Library Brands",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
def get_meta_platform_id(brand_names: Union[str, List[str]]) -> Dict[str, Any]:
    """Search Meta Ad Library for brand names and return matching Meta Page IDs."""
    if isinstance(brand_names, str):
        brand_name = brand_names.strip()
        if not brand_name:
            return {"success": False, "error": "Brand name cannot be empty."}
        results = get_platform_id(brand_name)
        return {
            "success": True,
            "results": results,
            "total_results": len(results),
        }

    cleaned = [str(name).strip() for name in brand_names if str(name).strip()]
    if not cleaned:
        return {"success": False, "error": "At least one brand name is required."}

    results = get_platform_ids_batch(cleaned)
    return {
        "success": True,
        "results": results,
        "total_results": sum(len(items) for items in results.values()),
    }


@mcp.tool(
    title="Get Meta Ad Library Ads",
    description="Retrieve currently running Meta ads for one or more Meta Page IDs, optionally filtered by a 2-letter country code such as GB or US.",
    annotations=ToolAnnotations(
        title="Get Meta Ad Library Ads",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
def get_meta_ads(
    platform_ids: Union[str, List[str]],
    limit: int = 50,
    country: Optional[str] = None,
    trim: bool = True,
) -> Dict[str, Any]:
    """Retrieve currently running Meta ads for one or more Meta Page IDs."""
    limit = max(1, min(int(limit), 500))

    if country:
        country = country.strip().upper()
        if len(country) != 2:
            return {
                "success": False,
                "error": "country must be a 2-letter code such as GB or US.",
            }

    if isinstance(platform_ids, str):
        platform_id = platform_ids.strip()
        if not platform_id:
            return {"success": False, "error": "Platform ID cannot be empty."}
        results = get_ads(platform_id, limit, country, trim)
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "country": country,
        }

    cleaned = [str(pid).strip() for pid in platform_ids if str(pid).strip()]
    if not cleaned:
        return {"success": False, "error": "At least one platform ID is required."}

    results = get_ads_batch(cleaned, limit, country, trim)
    return {
        "success": True,
        "results": results,
        "count": sum(len(items) for items in results.values()),
        "country": country,
    }


if __name__ == "__main__":
    public_host = os.getenv(
        "RAILWAY_PUBLIC_DOMAIN",
        "facebook-ads-library-mcp-production-0edd.up.railway.app",
    )

    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            public_host,
            f"{public_host}:443",
            "localhost:*",
            "127.0.0.1:*",
        ],
        allowed_origins=[
            "https://chatgpt.com",
            "https://chat.openai.com",
        ],
    )

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=transport_security,
    )
