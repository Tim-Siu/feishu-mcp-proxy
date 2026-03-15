import logging

import aiohttp
from aiohttp import web

from .token import TokenManager

logger = logging.getLogger(__name__)

FEISHU_MCP_URL = "https://mcp.feishu.cn/mcp"

# All available tools
ALL_TOOLS = (
    "create-doc,fetch-doc,update-doc,search-doc,list-docs,"
    "get-comments,add-comments,search-user,get-user,fetch-file"
)


def create_app(token_manager: TokenManager, allowed_tools: str | None = None) -> web.Application:
    tools = allowed_tools or ALL_TOOLS

    async def handle_mcp(request: web.Request) -> web.StreamResponse:
        body = await request.read()

        headers = {
            "Content-Type": "application/json",
            "Accept-Encoding": "identity",
            "X-Lark-MCP-TAT": token_manager.get_token(),
            "X-Lark-MCP-Allowed-Tools": tools,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(FEISHU_MCP_URL, data=body, headers=headers) as upstream_resp:
                upstream_content_type = upstream_resp.headers.get("Content-Type", "")

                # If upstream returns SSE, stream it through
                if "text/event-stream" in upstream_content_type:
                    response = web.StreamResponse(
                        status=upstream_resp.status,
                        headers={
                            "Content-Type": "text/event-stream",
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                        },
                    )
                    await response.prepare(request)

                    async for chunk in upstream_resp.content.iter_any():
                        await response.write(chunk)

                    await response.write_eof()
                    return response

                # Regular JSON response — return as-is
                resp_body = await upstream_resp.read()

                # Forward relevant headers
                resp_headers = {}
                if "Content-Type" in upstream_resp.headers:
                    resp_headers["Content-Type"] = upstream_resp.headers["Content-Type"]
                # Forward Mcp-Session-Id if present
                if "Mcp-Session-Id" in upstream_resp.headers:
                    resp_headers["Mcp-Session-Id"] = upstream_resp.headers["Mcp-Session-Id"]

                return web.Response(
                    status=upstream_resp.status,
                    body=resp_body,
                    headers=resp_headers,
                )

    async def handle_health(request: web.Request) -> web.Response:
        try:
            token = token_manager.get_token()
            return web.json_response({"status": "ok", "token_prefix": token[:10] + "..."})
        except RuntimeError as e:
            return web.json_response({"status": "error", "message": str(e)}, status=503)

    app = web.Application()
    app.router.add_post("/mcp", handle_mcp)
    app.router.add_get("/health", handle_health)
    return app
