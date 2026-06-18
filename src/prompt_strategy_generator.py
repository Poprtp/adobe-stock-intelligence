"""Prompt Strategy Generator for Adobe Stock Intelligence.

Phase 5 converts approved design briefs into structured prompt strategies.
It does not call image APIs and it does not generate images. The goal is to
turn Buyer -> Use Case -> Asset briefs into safe, reusable prompt text for
manual ChatGPT image generation or a later production engine.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROMPT_COLUMNS = [
    "Prompt ID",
    "Brief ID",
    "Asset",
    "Industry",
    "Niche",
    "Buyer Persona",
    "Use Case",
    "Aspect Ratio",
    "Prompt Version",
    "Prompt",
    "Negative Prompt / Safety Rules",
    "Metadata Title Draft",
    "Metadata Description Draft",
    "Keyword Seed",
    "Production Status",
]

SAFETY_RULES = (
    "no text, no logos, no brands, no people, no hands, no copyrighted objects, "
    "no trademarked packaging, no readable labels, no clutter, no unrealistic AI artifacts"
)


def generate_prompt_library(design_briefs: pd.DataFrame) -> pd.DataFrame:
    """Create two prompt strategy rows for each design brief.

    Args:
        design_briefs: DataFrame from output/design_briefs.xlsx.

    Returns:
        DataFrame with one row per prompt strategy.
    """

    if design_briefs.empty:
        return pd.DataFrame(columns=PROMPT_COLUMNS)

    required = [
        "Brief ID",
        "Asset",
        "Industry",
        "Niche",
        "Buyer Persona",
        "Use Case",
        "Visual Direction",
        "Composition",
        "Lighting",
        "Copy Space",
        "Product Placement Zone",
        "Must Include",
        "Avoid",
    ]
    missing = [column for column in required if column not in design_briefs.columns]
    if missing:
        raise ValueError(f"Design briefs are missing required columns: {missing}")

    rows: list[dict[str, str]] = []
    prompt_index = 1

    for _, brief in design_briefs.iterrows():
        for version, aspect_ratio in [
            ("Website / presentation hero", "16:9"),
            ("Social / product marketing layout", "4:5"),
        ]:
            rows.append(_build_prompt_row(prompt_index, brief, version, aspect_ratio))
            prompt_index += 1

    return pd.DataFrame(rows, columns=PROMPT_COLUMNS)


def write_prompt_library_outputs(
    prompt_library: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Write prompt library output to Excel and Markdown."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        prompt_library.to_excel(writer, sheet_name="Prompt Library", index=False)

    output_report.write_text(build_prompt_library_report(prompt_library), encoding="utf-8")


def build_prompt_library_report(prompt_library: pd.DataFrame) -> str:
    """Create a human-readable Markdown prompt report."""

    lines = [
        "# Prompt Strategy Generator Output",
        "",
        "These prompts are generated from approved design briefs using the BUY Framework.",
        "They are for prompt testing only. This phase does not generate images or call image APIs.",
        "",
    ]

    if prompt_library.empty:
        lines.append("No prompt strategies were generated.")
        return "\n".join(lines) + "\n"

    for _, row in prompt_library.iterrows():
        lines.extend(
            [
                f"## {row['Prompt ID']} — {row['Asset']} ({row['Aspect Ratio']})",
                "",
                f"- **Brief ID:** {row['Brief ID']}",
                f"- **Buyer:** {row['Buyer Persona']}",
                f"- **Use Case:** {row['Use Case']}",
                f"- **Version:** {row['Prompt Version']}",
                "",
                "### Prompt",
                "",
                row["Prompt"],
                "",
                "### Safety Rules",
                "",
                row["Negative Prompt / Safety Rules"],
                "",
                f"- **Title Draft:** {row['Metadata Title Draft']}",
                f"- **Description Draft:** {row['Metadata Description Draft']}",
                f"- **Keyword Seed:** {row['Keyword Seed']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def _build_prompt_row(index: int, brief: pd.Series, version: str, aspect_ratio: str) -> dict[str, str]:
    asset = _clean(brief.get("Asset"))
    industry = _clean(brief.get("Industry"))
    niche = _clean(brief.get("Niche"))
    buyer = _clean(brief.get("Buyer Persona"))
    use_case = _clean(brief.get("Use Case"))
    visual_direction = _clean(brief.get("Visual Direction"))
    composition = _clean(brief.get("Composition"))
    lighting = _clean(brief.get("Lighting"))
    copy_space = _clean(brief.get("Copy Space"))
    placement = _clean(brief.get("Product Placement Zone"))
    must_include = _clean(brief.get("Must Include"))
    avoid = _clean(brief.get("Avoid"))

    prompt = _compose_prompt(
        asset=asset,
        buyer=buyer,
        use_case=use_case,
        visual_direction=visual_direction,
        composition=composition,
        lighting=lighting,
        copy_space=copy_space,
        placement=placement,
        must_include=must_include,
        aspect_ratio=aspect_ratio,
        version=version,
    )

    return {
        "Prompt ID": f"P{index:03d}",
        "Brief ID": _clean(brief.get("Brief ID")),
        "Asset": asset,
        "Industry": industry,
        "Niche": niche,
        "Buyer Persona": buyer,
        "Use Case": use_case,
        "Aspect Ratio": aspect_ratio,
        "Prompt Version": version,
        "Prompt": prompt,
        "Negative Prompt / Safety Rules": f"{SAFETY_RULES}; {avoid}",
        "Metadata Title Draft": _title_draft(asset, aspect_ratio),
        "Metadata Description Draft": _description_draft(asset, use_case),
        "Keyword Seed": _keyword_seed(asset, industry, niche, use_case),
        "Production Status": "Ready for manual prompt test",
    }


def _compose_prompt(
    *,
    asset: str,
    buyer: str,
    use_case: str,
    visual_direction: str,
    composition: str,
    lighting: str,
    copy_space: str,
    placement: str,
    must_include: str,
    aspect_ratio: str,
    version: str,
) -> str:
    if aspect_ratio == "16:9":
        layout_instruction = (
            "wide horizontal hero composition for website banner, sales presentation, and campaign key visual"
        )
    else:
        layout_instruction = (
            "vertical product marketing composition for social media, mobile advertising, and product storytelling"
        )

    return (
        f"Ultra realistic commercial stock photography of a {asset}, designed for {buyer} using it for {use_case}. "
        f"{visual_direction}. {layout_instruction}. {composition}. {lighting}. "
        f"{copy_space} {placement}. Must include: {must_include}. "
        "Realistic materials, physically accurate shadows, clean professional composition, high-end marketing asset, "
        "globally usable commercial environment, Adobe Stock contributor quality. "
        f"Aspect ratio {aspect_ratio}. "
        f"No text, no logos, no brands, no people, no hands, no copyrighted objects, no readable labels."
    )


def _title_draft(asset: str, aspect_ratio: str) -> str:
    return f"{asset} Commercial Marketing Background {aspect_ratio}"


def _description_draft(asset: str, use_case: str) -> str:
    description = f"Reusable {asset.lower()} for {use_case.lower()}, designed as a clean commercial marketing background with copy space."
    return description[:200]


def _keyword_seed(asset: str, industry: str, niche: str, use_case: str) -> str:
    words = [
        *asset.replace("/", " ").replace("-", " ").split(),
        *industry.replace("/", " ").replace("-", " ").split(),
        *niche.replace("/", " ").replace("-", " ").split(),
        *use_case.replace("/", " ").replace("-", " ").split(),
        "commercial",
        "marketing",
        "background",
        "copyspace",
        "presentation",
        "advertising",
        "realistic",
        "premium",
        "display",
        "environment",
    ]
    cleaned = []
    for word in words:
        token = "".join(ch for ch in word.lower() if ch.isalnum())
        if token and token not in cleaned:
            cleaned.append(token)
    return ", ".join(cleaned[:30])


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
