"""Placeholder research agent for future niche analysis.

Phase 1 does not call OpenAI, web search, image APIs, or any external research
service. This module provides the interface that later phases can replace with
real market research while keeping downstream pipeline code stable.
"""

from __future__ import annotations


def analyze_niche(niche_name: str) -> dict[str, object]:
    """Return mock structured research data for a niche.

    Args:
        niche_name: Plain-language niche name to analyze.

    Returns:
        A structured dictionary matching the planned Niche Database fields.
    """

    normalized_niche = niche_name.strip()
    if not normalized_niche:
        raise ValueError("niche_name must be a non-empty string.")

    return {
        "industry": "TBD",
        "niche": normalized_niche,
        "buyer_persona": "Marketing buyer",
        "job_to_be_done": "Use in commercial marketing assets, sales decks, and web content.",
        "demand_score": 5,
        "competition_score": 5,
        "commercial_value": 5,
        "evergreen": 5,
        "repeat_use": 5,
        "ai_saturation": 5,
        "recommendation": "Research further before production.",
        "notes": "Mock output only. Replace with real OpenAI and web research in Phase 3.",
    }


# TODO Phase 3
# - OpenAI API research
# - Web search
# - Google Sheets sync
# - Buyer Database integration
# - Gap Analysis
# - Prompt Library generation
