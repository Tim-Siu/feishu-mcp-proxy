import asyncio
import logging
import time

import aiohttp

logger = logging.getLogger(__name__)

FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"


class TokenManager:
    """Manages Feishu tenant_access_token with automatic refresh."""

    def __init__(self, app_id: str, app_secret: str):
        self._app_id = app_id
        self._app_secret = app_secret
        self._token: str | None = None
        self._expire_at: float = 0
        self._refresh_task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None

    async def start(self):
        self._session = aiohttp.ClientSession()
        await self._fetch_token()
        self._refresh_task = asyncio.create_task(self._refresh_loop())
        logger.info("Token manager started")

    async def stop(self):
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()

    def get_token(self) -> str:
        if not self._token:
            raise RuntimeError("Token not available yet")
        return self._token

    async def _fetch_token(self):
        """Fetch a new tenant_access_token from Feishu."""
        payload = {"app_id": self._app_id, "app_secret": self._app_secret}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self._session.post(FEISHU_TOKEN_URL, json=payload) as resp:
                    data = await resp.json()

                if data.get("code") != 0:
                    raise RuntimeError(f"Feishu token API error: {data.get('msg', data)}")

                self._token = data["tenant_access_token"]
                expire_seconds = data["expire"]
                self._expire_at = time.monotonic() + expire_seconds
                logger.info(
                    "Token refreshed, expires in %d seconds (token prefix: %s...)",
                    expire_seconds,
                    self._token[:10],
                )
                return

            except Exception:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** (attempt + 1)
                logger.warning("Token fetch failed (attempt %d/%d), retrying in %ds", attempt + 1, max_retries, wait)
                await asyncio.sleep(wait)

    async def _refresh_loop(self):
        """Background loop that refreshes the token before it expires."""
        while True:
            # Refresh at 50% of the remaining lifetime
            remaining = self._expire_at - time.monotonic()
            sleep_time = max(remaining * 0.5, 60)  # At least 60 seconds
            logger.debug("Next token refresh in %.0f seconds", sleep_time)
            await asyncio.sleep(sleep_time)

            try:
                await self._fetch_token()
            except Exception:
                logger.exception("Token refresh failed, will retry in 30 seconds")
                await asyncio.sleep(30)
