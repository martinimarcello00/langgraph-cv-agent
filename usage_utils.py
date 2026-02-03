"""
Utilities for querying OpenAI usage metrics.
Provides functions to track token usage for specific models.
"""
from __future__ import annotations

import datetime
import logging
import os
import requests
from typing import Dict, Optional, Union, List, Tuple, Any

# --- Initialization ---
logger = logging.getLogger(__name__)

# --- Constants ---
USAGE_API_URL = "https://api.openai.com/v1/organization/usage/completions"

# --- Functions ---

def get_today_completions_usage(
    bucket_width: str = "1d",
    raw_output: bool = False,
    by_model: bool = False,
) -> Union[Dict[str, int], Dict[str, Dict[str, int]]]:
    """
    Return today's organization usage for the completions endpoint.

    Args:
        bucket_width: Width of the aggregation bucket (e.g., "1d", "1h").
        raw_output: If True, returns the raw JSON response.
        by_model: If True, returns usage grouped by model.

    Returns:
        Dict: Usage statistics containing 'input_tokens', 'output_tokens', 'total_tokens'.
              If by_model is True, returns a nested dict keyed by model name.
    """
    api_key = os.getenv("OPENAI_ADMIN_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("OPENAI_API_KEY or OPENAI_ADMIN_API_KEY environment variable is missing.")
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    # Calculate timeframe for "today" (UTC)
    start_dt = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_dt = start_dt + datetime.timedelta(days=1)

    # API Parameters
    params: List[Tuple[str, Union[int, str]]] = [
        ("start_time", int(start_dt.timestamp())),
        ("end_time", int(end_dt.timestamp())),
        ("bucket_width", bucket_width),
    ]

    if by_model:
        params.append(("group_by", "model"))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            USAGE_API_URL,
            params=params,
            headers=headers,
            timeout=10, 
        )

        response.raise_for_status()
        json_response = response.json()

        if raw_output:
            return json_response

        # Parse results
        data = json_response.get("data", [])
        if not data:
            return {} if by_model else {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        results = data[0].get("results", [])

        if by_model:
            return _aggregate_usage_by_model(results)
        
        return _aggregate_total_usage(results)

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP Request failed for usage data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching usage data: {e}")

    # Fallback return on error
    return {} if by_model else {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _aggregate_usage_by_model(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Helper to aggregate raw usage results by model."""
    usage_by_model: Dict[str, Dict[str, int]] = {}
    
    for r in results:
        model_name = r.get("model") or r.get("name") or r.get("model_name") or "unknown"
        input_tokens = int(r.get("input_tokens") or 0)
        output_tokens = int(r.get("output_tokens") or 0)
        
        if model_name not in usage_by_model:
            usage_by_model[model_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            }
            
        usage_by_model[model_name]["input_tokens"] += input_tokens
        usage_by_model[model_name]["output_tokens"] += output_tokens
        usage_by_model[model_name]["total_tokens"] += input_tokens + output_tokens
        
    return usage_by_model


def _aggregate_total_usage(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Helper to aggregate raw usage results into a single total."""
    if not results:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        
    # The API typically returns one result object for the aggregate view, 
    # but defensive coding uses the first one.
    first_res = results[0]
    input_tokens = int(first_res.get("input_tokens") or 0)
    output_tokens = int(first_res.get("output_tokens") or 0)
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def get_today_model_usage(model_name: str, bucket_width: str = "1d") -> Dict[str, int]:
    """
    Return today's token usage for a specific model (or partial match).

    Args:
        model_name: Model identifier (e.g., "gpt-5-mini").
        bucket_width: Aggregation bucket width.

    Returns:
        Dict: {'input_tokens': int, 'output_tokens': int, 'total_tokens': int}
    """
    try:
        # Force type cast because we know it returns a dict of dicts when by_model=True
        usage = get_today_completions_usage(bucket_width=bucket_width, by_model=True) # type: ignore
    except Exception as exc:
        logger.error("Failed to retrieve usage data: %s", exc)
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    if not isinstance(usage, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    # Aggregate usage for any key containing the model_name (case-insensitive)
    target_lower = model_name.lower()
    aggregate = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
    found_match = False
    for key, stats in usage.items():
        if isinstance(stats, dict) and target_lower in key.lower():
            found_match = True
            aggregate["input_tokens"] += int(stats.get("input_tokens", 0))
            aggregate["output_tokens"] += int(stats.get("output_tokens", 0))
            aggregate["total_tokens"] += int(stats.get("total_tokens", 0))

    if not found_match:
        logger.debug(f"No usage found for model matching '{model_name}'")

    return aggregate
