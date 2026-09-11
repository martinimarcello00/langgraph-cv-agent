"""Daily token budget for the agent.

Tokens are counted in-process as the LLM returns them, so checking the budget is a
comparison rather than an HTTP call. The OpenAI usage API is only consulted by a
background task, which is what keeps it off the request path.
"""
from __future__ import annotations

import asyncio
import datetime
import logging
import os
from typing import Dict, Mapping, Optional

import httpx

# --- Initialization ---
logger = logging.getLogger(__name__)

# --- Constants ---
USAGE_API_URL = "https://api.openai.com/v1/organization/usage/completions"
REQUEST_TIMEOUT_SECONDS = 10.0

# Shared by the agent (which model to call) and the budget (which model to meter).
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5-nano")

_ZERO_USAGE = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


# --- Functions ---

def _utc_today() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


async def fetch_today_model_usage(model_name: str) -> Dict[str, int]:
    """Today's organization-wide token usage for a model. Returns zeros on any failure."""
    api_key = os.getenv("OPENAI_ADMIN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_ADMIN_API_KEY or OPENAI_API_KEY set, cannot reconcile usage.")
        return dict(_ZERO_USAGE)

    start_dt = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    params = [
        ("start_time", int(start_dt.timestamp())),
        ("end_time", int((start_dt + datetime.timedelta(days=1)).timestamp())),
        ("bucket_width", "1d"),
        ("group_by", "model"),
    ]

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(
                USAGE_API_URL,
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            buckets = response.json().get("data", [])
    except Exception as exc:
        logger.warning("Usage reconcile failed: %s", exc)
        return dict(_ZERO_USAGE)

    if not buckets:
        return dict(_ZERO_USAGE)

    # Match partially so "gpt-5-nano-2025-08-07" still counts against "gpt-5-nano".
    target = model_name.lower()
    aggregate = dict(_ZERO_USAGE)
    for result in buckets[0].get("results", []):
        name = result.get("model") or result.get("name") or ""
        if target not in name.lower():
            continue
        input_tokens = int(result.get("input_tokens") or 0)
        output_tokens = int(result.get("output_tokens") or 0)
        aggregate["input_tokens"] += input_tokens
        aggregate["output_tokens"] += output_tokens
        aggregate["total_tokens"] += input_tokens + output_tokens

    return aggregate



class TokenBudget:
    """Monotonic daily token counter, reset on UTC rollover."""

    def __init__(self, model_name: str, daily_limit: int) -> None:
        self.model_name = model_name
        self.daily_limit = daily_limit
        self._day = _utc_today()
        self._tokens = 0

    def _roll_day(self) -> None:
        today = _utc_today()
        if today != self._day:
            self._day = today
            self._tokens = 0

    def record(self, usage_metadata: Optional[Mapping[str, object]]) -> None:
        """Add the tokens reported by a single LLM response."""
        if not usage_metadata:
            return
        self._roll_day()
        self._tokens += int(usage_metadata.get("total_tokens") or 0)

    @property
    def total_tokens(self) -> int:
        self._roll_day()
        return self._tokens

    def exceeded(self) -> bool:
        return self.daily_limit > 0 and self.total_tokens >= self.daily_limit

    async def reconcile(self) -> None:
        """Catch up with real usage, which covers tokens spent before the last restart."""
        usage = await fetch_today_model_usage(self.model_name)
        reported = usage.get("total_tokens", 0)
        if reported <= 0:
            return
        self._roll_day()
        # The API lags behind, so it may only ever raise the local count.
        self._tokens = max(self._tokens, reported)
        logger.info("Token usage reconciled: %s/%s", self._tokens, self.daily_limit)

    async def run_periodic(self, interval_seconds: float) -> None:
        while True:
            try:
                await self.reconcile()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Background usage reconcile errored: %s", exc)
            await asyncio.sleep(interval_seconds)


budget = TokenBudget(
    model_name=MODEL_NAME,
    daily_limit=int(os.getenv("DAILY_TOKEN_LIMIT", "50000")),
)

