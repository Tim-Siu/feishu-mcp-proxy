import argparse
import asyncio
import logging
import os
import sys

from aiohttp import web
from dotenv import load_dotenv

from .server import create_app
from .token import TokenManager


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Feishu MCP Proxy with auto token refresh")
    parser.add_argument("--host", default=os.getenv("PROXY_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PROXY_PORT", "9099")))
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        print("Error: FEISHU_APP_ID and FEISHU_APP_SECRET must be set", file=sys.stderr)
        print("Copy .env.example to .env and fill in your credentials", file=sys.stderr)
        sys.exit(1)

    allowed_tools = os.getenv("FEISHU_ALLOWED_TOOLS")

    token_manager = TokenManager(app_id, app_secret)

    async def on_startup(app: web.Application):
        await token_manager.start()

    async def on_cleanup(app: web.Application):
        await token_manager.stop()

    app = create_app(token_manager, allowed_tools)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    print(f"Starting Feishu MCP Proxy on http://{args.host}:{args.port}/mcp")
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
