import sys
import asyncio


def _set_windows_event_loop_policy_if_needed() -> None:
    """On Windows, force the selector event loop policy to avoid asyncio/websockets issues.

    Safe to call multiple times; no-op on non-Windows platforms.
    """
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            # Best-effort shim; if unavailable or already set, continue without raising
            pass


_set_windows_event_loop_policy_if_needed()


