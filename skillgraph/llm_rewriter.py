"""
SkillGraph — Optional LLM-Assisted Resume Rewriter

Provides an optional generative rewriting mode (off by default) that can be
enabled with an explicit API key. Strictly falls back to deterministic slot-filling
if the API key is not present or if an error occurs.

Includes grounding validation to detect whether generative rewrites introduce
unsupported numbers, metrics, or factual claims not present in the original statement.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import Any

logger = logging.getLogger(__name__)


def generate_llm_rewrite(
    inference: dict[str, Any],
    api_key: str | None = None,
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> str | None:
    """Generate an optional LLM-assisted bullet rewrite.

    Off by default. Requires an explicit API key or the OPENAI_API_KEY or
    SKILLGRAPH_LLM_KEY environment variable.

    Args:
        inference: Confirmed or partially confirmed inference dictionary.
        api_key: Optional API key.
        api_base: API base URL (defaults to OpenAI).
        model: Model identifier.

    Returns:
        Rewritten bullet string if successful, or None to fall back to deterministic slot-filling.
    """
    key = api_key or os.getenv("SKILLGRAPH_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        return None

    # Defense: restrict API base to secure HTTPS endpoints
    if not api_base or not api_base.startswith("https://"):
        logger.warning("Rejected non-HTTPS or invalid api_base: %s", api_base)
        return None

    missing_skill = inference.get("missing_skill", "")
    original_stmt = inference.get("matched_statement", "")
    classification = inference.get("classification", "CONFIRMED")
    selected_option = inference.get("selected_option", "")

    system_prompt = (
        "You are an expert resume editor. Your job is to rewrite a single resume bullet point "
        "to naturally incorporate a candidate's confirmed technical skill.\n"
        "STRICT CONSTRAINTS:\n"
        "1. DO NOT invent, hallucinate, or extrapolate new metrics, percentages, numbers, or achievements.\n"
        "2. Keep the exact employer, context, and scope from the original bullet.\n"
        "3. If the skill is 'PARTIALLY_CONFIRMED', state that it was used via tooling, libraries, or frameworks.\n"
        "4. Return ONLY the rewritten bullet sentence without commentary or quotation marks."
    )

    user_prompt = (
        f"Original bullet: \"{original_stmt}\"\n"
        f"Skill to incorporate: {missing_skill}\n"
        f"Candidate confirmation status: {classification} ({selected_option})\n\n"
        "Provide a single, professional bullet point rewrite:"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 150,
    }

    try:
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
            return content.strip('"')
    except Exception as exc:
        logger.warning("LLM rewrite failed or unavailable (%s). Using deterministic rewrite.", exc)
        return None


def verify_grounding(original_statement: str, rewrite: str, target_skill: str) -> dict[str, Any]:
    """Verify that a rewrite does not introduce unsupported numerical claims or metrics.

    Args:
        original_statement: The original candidate bullet.
        rewrite: The proposed rewritten bullet.
        target_skill: The target skill incorporated.

    Returns:
        Dict with 'is_grounded': bool, 'new_numbers': list[str], 'reasons': list[str].
    """
    orig_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?%?(?:k|m|b)?\b", original_statement.lower()))
    rewrite_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?%?(?:k|m|b)?\b", rewrite.lower()))

    # Numbers in rewrite that were not in original
    hallucinated_numbers = sorted(rewrite_numbers - orig_numbers)

    reasons = []
    if hallucinated_numbers:
        reasons.append(f"Introduced ungrounded numerical metrics: {', '.join(hallucinated_numbers)}")

    if target_skill.lower() not in rewrite.lower():
        reasons.append(f"Target skill '{target_skill}' was not found in the rewrite")

    return {
        "is_grounded": len(hallucinated_numbers) == 0,
        "hallucinated_numbers": hallucinated_numbers,
        "reasons": reasons,
    }
