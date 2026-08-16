import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BrowserDriverError(RuntimeError):
    pass


class PlaywrightDriver:
    """Deterministic browser driver using Playwright for governed execution."""

    def __init__(self, allowed_domains: list[str], headless: bool = True):
        self.allowed_domains = allowed_domains
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def _route_handler(self, route) -> None:
        request = route.request
        if request.is_navigation_request() and not self._is_url_allowed(request.url):
            await route.abort("accessdenied")
            return
        await route.continue_()

    async def start(self) -> None:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise BrowserDriverError("Playwright is not installed.") from exc

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()

        await self._page.route("**/*", self._route_handler)

    async def stop(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def _is_url_allowed(self, url: str) -> bool:
        if not self.allowed_domains:
            return False  # Strictly fail closed if no allowlist is configured

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        hostname = parsed.hostname
        if not hostname:
            return False
        return any(
            hostname == allowed or hostname.endswith(f".{allowed}")
            for allowed in self.allowed_domains
        )

    async def navigate(self, url: str) -> str:
        if not self._is_url_allowed(url):
            raise BrowserDriverError(f"Navigation to {url} is not permitted by the allowlist.")
        if not self._page:
            raise BrowserDriverError("Session not started.")

        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=10000)
        # We catch Exception here because Playwright exposes a broad set of dynamic errors
        # (TimeoutError, TargetClosedError, Error) which we normalize into our driver boundary.
        except Exception as e:  # noqa: BLE001
            raise BrowserDriverError(f"Navigation failed: {e}")

        final_url = self._page.url
        if not self._is_url_allowed(final_url):
            raise BrowserDriverError(
                f"Redirected to {final_url}, which is not permitted by the allowlist."
            )

        return final_url

    async def read_text(self, selector: str = "body") -> str:
        if not self._page:
            raise BrowserDriverError("Session not started.")

        try:
            return await self._page.inner_text(selector, timeout=5000)
        except Exception as e:  # noqa: BLE001
            raise BrowserDriverError(f"Failed to read text for selector '{selector}': {e}")

    async def capture_screenshot(self) -> bytes:
        if not self._page:
            raise BrowserDriverError("Session not started.")
        try:
            return await self._page.screenshot(type="png", full_page=False)
        except Exception as e:  # noqa: BLE001
            raise BrowserDriverError(f"Failed to capture screenshot: {e}")
