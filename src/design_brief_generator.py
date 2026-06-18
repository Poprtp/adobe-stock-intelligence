"""Design brief generation for top commercial visual asset opportunities.

This module turns the knowledge layer output into production-ready creative
briefs. It does not generate prompts or images yet. Its job is to translate
Buyer -> Use Case -> Asset intelligence into a clear creative direction that a
human designer, ChatGPT, or a future prompt engine can use safely.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BRIEF_COLUMNS = [
    "Brief ID",
    "Asset",
    "Industry",
    "Niche",
    "Buyer Persona",
    "Use Case",
    "Campaign Goal",
    "Commercial Uses",
    "Visual Direction",
    "Composition",
    "Lighting",
    "Copy Space",
    "Product Placement Zone",
    "Recommended Aspect Ratios",
    "Must Include",
    "Avoid",
    "Production Priority",
    "Prompt Strategy Note",
]


def generate_design_briefs(opportunity_map: pd.DataFrame, max_briefs: int = 10) -> pd.DataFrame:
    """Create design briefs from the highest-ranked opportunity rows.

    Args:
        opportunity_map: Output from knowledge_engine.build_opportunity_map.
        max_briefs: Maximum number of briefs to create.

    Returns:
        DataFrame containing one production brief per selected opportunity.
    """

    if opportunity_map.empty:
        return pd.DataFrame(columns=BRIEF_COLUMNS)

    required = ["Asset", "Industry", "Niche", "Buyer Persona", "Use Case", "Asset Score"]
    missing = [column for column in required if column not in opportunity_map.columns]
    if missing:
        raise ValueError(f"Opportunity map is missing required columns: {missing}")

    selected = (
        opportunity_map.sort_values(by="Asset Score", ascending=False)
        .drop_duplicates(subset=["Asset", "Buyer Persona", "Use Case"], keep="first")
        .head(max_briefs)
        .reset_index(drop=True)
    )

    briefs = []
    for index, row in selected.iterrows():
        briefs.append(_build_brief(index + 1, row))

    return pd.DataFrame(briefs, columns=BRIEF_COLUMNS)


def write_design_brief_outputs(
    briefs: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Write design briefs to Excel and Markdown."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        briefs.to_excel(writer, sheet_name="Design Briefs", index=False)

    output_report.write_text(build_design_brief_report(briefs), encoding="utf-8")


def build_design_brief_report(briefs: pd.DataFrame) -> str:
    """Generate a readable Markdown report for production review."""

    lines = [
        "# Design Brief Generator Output",
        "",
        "These briefs convert market intelligence into production direction.",
        "They are intentionally not image prompts yet. Each brief must answer Buyer, Use Case, and Why Buy before production.",
        "",
    ]

    if briefs.empty:
        lines.append("No design briefs were generated.")
        return "\n".join(lines) + "\n"

    for _, row in briefs.iterrows():
        lines.extend(
            [
                f"## {row['Brief ID']} — {row['Asset']}",
                "",
                f"- **Industry:** {row['Industry']}",
                f"- **Niche:** {row['Niche']}",
                f"- **Buyer:** {row['Buyer Persona']}",
                f"- **Use Case:** {row['Use Case']}",
                f"- **Campaign Goal:** {row['Campaign Goal']}",
                f"- **Commercial Uses:** {row['Commercial Uses']}",
                f"- **Visual Direction:** {row['Visual Direction']}",
                f"- **Composition:** {row['Composition']}",
                f"- **Lighting:** {row['Lighting']}",
                f"- **Copy Space:** {row['Copy Space']}",
                f"- **Product Placement Zone:** {row['Product Placement Zone']}",
                f"- **Aspect Ratios:** {row['Recommended Aspect Ratios']}",
                f"- **Must Include:** {row['Must Include']}",
                f"- **Avoid:** {row['Avoid']}",
                f"- **Production Priority:** {row['Production Priority']}",
                f"- **Prompt Strategy Note:** {row['Prompt Strategy Note']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def _build_brief(index: int, row: pd.Series) -> dict[str, str]:
    asset = _clean(row.get("Asset"))
    industry = _clean(row.get("Industry"))
    niche = _clean(row.get("Niche"))
    buyer = _clean(row.get("Buyer Persona"))
    use_case = _clean(row.get("Use Case"))
    direction = _clean(row.get("Design Direction")) or _default_direction(asset, industry)
    ratios = _clean(row.get("Recommended Aspect Ratios")) or "16:9; 4:5"
    score = row.get("Asset Score")

    return {
        "Brief ID": f"DB{index:03d}",
        "Asset": asset,
        "Industry": industry,
        "Niche": niche,
        "Buyer Persona": buyer,
        "Use Case": use_case,
        "Campaign Goal": _campaign_goal(use_case, buyer),
        "Commercial Uses": _commercial_uses(use_case),
        "Visual Direction": direction,
        "Composition": _composition(asset, use_case),
        "Lighting": _lighting(industry),
        "Copy Space": "Minimum 35-45% clean negative space for headline, packaging, or campaign message.",
        "Product Placement Zone": _placement_zone(asset),
        "Recommended Aspect Ratios": ratios,
        "Must Include": _must_include(asset, industry),
        "Avoid": "No logos, no readable text, no brands, no people, no hands, no copyrighted objects, no cluttered backgrounds.",
        "Production Priority": _priority(score),
        "Prompt Strategy Note": _prompt_note(asset, buyer, use_case),
    }


def _campaign_goal(use_case: str, buyer: str) -> str:
    lowered = use_case.lower()
    if "launch" in lowered:
        return f"Help {buyer} introduce a new product with a premium reusable visual system."
    if "website" in lowered or "hero" in lowered:
        return f"Give {buyer} a credible website hero environment with room for campaign copy."
    if "sales" in lowered or "pitch" in lowered:
        return f"Support {buyer} with a professional sales or retail presentation scene."
    if "social" in lowered:
        return f"Create a reusable social advertising background for {buyer}."
    return f"Support {buyer} with a commercial marketing asset that can be adapted across channels."


def _commercial_uses(use_case: str) -> str:
    base = [use_case, "Website Hero", "Sales Deck", "Brochure", "Social Media Ads"]
    unique = []
    for item in base:
        if item and item not in unique:
            unique.append(item)
    return "; ".join(unique)


def _default_direction(asset: str, industry: str) -> str:
    if industry.lower() == "healthcare":
        return "Trustworthy premium healthcare environment, clean, modern, globally usable, not overly sterile."
    if industry.lower() == "pet":
        return "Premium pet brand environment, warm, clean, modern, practical for packaging and web marketing."
    if industry.lower() == "fmcg":
        return "Retail-ready packaging presentation environment with realistic shelf/display context and clear placement space."
    return "Commercial marketing environment with realistic materials, clear visual hierarchy, and broad reuse potential."


def _composition(asset: str, use_case: str) -> str:
    lowered_asset = asset.lower()
    lowered_use = use_case.lower()
    if "shelf" in lowered_asset or "display" in lowered_asset:
        return "Eye-level or slight 3/4 retail display composition, clear central product zone, organized shelf rhythm."
    if "launch" in lowered_use or "hero" in lowered_use:
        return "Wide hero composition, strongest visual anchor on one side, large clear copy area opposite."
    if "reception" in lowered_asset:
        return "Architectural interior composition with calm depth, clean foreground, and open space for headline overlay."
    return "Balanced commercial composition with one obvious focal area and usable negative space."


def _lighting(industry: str) -> str:
    if industry.lower() == "healthcare":
        return "Soft bright daylight with subtle clinical cleanliness, gentle shadows, no harsh glare."
    if industry.lower() == "pet":
        return "Soft natural daylight, warm but neutral, realistic home or retail atmosphere."
    if industry.lower() == "fmcg":
        return "Professional retail lighting with realistic shelf highlights and controlled reflections."
    return "Commercial-grade realistic lighting with natural shadows and premium material response."


def _placement_zone(asset: str) -> str:
    lowered = asset.lower()
    if "shelf" in lowered or "display" in lowered:
        return "Center or lower-third empty zone sized for packaging mockups or product cutouts."
    if "launch" in lowered:
        return "Foreground platform or clean counter area reserved for product hero placement."
    if "reception" in lowered or "environment" in lowered:
        return "Open foreground or side area suitable for product, headline, or UI overlay."
    return "Clearly defined empty product area, not blocked by props or shadows."


def _must_include(asset: str, industry: str) -> str:
    lowered = asset.lower()
    if "pharmacy" in lowered:
        return "Clean pharmacy-inspired shelving/counter, healthcare cues, empty packaging-ready areas, realistic materials."
    if "pet" in lowered:
        return "Pet retail or home-lifestyle cues, premium material palette, space for packaging or product placement."
    if "frozen" in lowered:
        return "Freezer or chilled retail context, clean lighting, empty product placement zones, no visible brands."
    if "coffee" in lowered:
        return "Warm roastery or premium shelf cues, pouch-ready empty zones, natural material palette."
    if industry.lower() == "healthcare":
        return "Trust cues, cleanliness, modern healthcare context, and broad commercial usability."
    return "Commercially useful environment, realistic textures, clear negative space, reusable composition."


def _priority(score: object) -> str:
    if pd.isna(score):
        return "Review"
    score = int(score)
    if score >= 88:
        return "Create first 10-image test collection"
    if score >= 82:
        return "Create small 5-image test set"
    if score >= 75:
        return "Hold for later production"
    return "Do not produce yet"


def _prompt_note(asset: str, buyer: str, use_case: str) -> str:
    return (
        f"Prompt should frame this as a {asset} for {buyer} using it as {use_case}. "
        "Prioritize practical marketing usability over decorative beauty."
    )


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
