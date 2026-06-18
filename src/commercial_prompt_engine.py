"""Prompt generation from Scene DNA creative directions.

Phase 6.1 prompts are generated from accepted creative directions, not from
fixed templates or raw library labels. This module does not generate images,
call image APIs, perform web research, or sync to Google Sheets.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROMPT_VARIATION_COLUMNS = [
    "Prompt ID",
    "Creative Direction ID",
    "Version",
    "Asset",
    "Buyer",
    "Use Case",
    "Scene",
    "Prompt",
    "Word Count",
    "Negative Constraints",
    "Production Status",
]


def generate_prompt_variations(creative_directions: pd.DataFrame) -> pd.DataFrame:
    """Generate image-model prompts from accepted creative directions."""

    if creative_directions.empty:
        return pd.DataFrame(columns=PROMPT_VARIATION_COLUMNS)

    required = [
        "Creative Direction ID",
        "Version",
        "asset",
        "buyer",
        "use_case",
        "scene",
        "architecture",
        "layout",
        "materials",
        "lighting",
        "camera",
        "composition",
        "copy_space",
        "negative_constraints",
    ]
    missing = [column for column in required if column not in creative_directions.columns]
    if missing:
        raise ValueError(f"Creative directions are missing required columns: {missing}")

    rows: list[dict[str, object]] = []
    for index, direction in creative_directions.iterrows():
        prompt = _build_prompt(direction)
        word_count = len(prompt.split())
        if not 140 <= word_count <= 220:
            raise ValueError(
                f"Prompt word count out of range for {direction['Version']}: {word_count} words"
            )

        rows.append(
            {
                "Prompt ID": f"PV{index + 1:04d}",
                "Creative Direction ID": _clean(direction["Creative Direction ID"]),
                "Version": _clean(direction["Version"]),
                "Asset": _clean(direction["asset"]),
                "Buyer": _clean(direction["buyer"]),
                "Use Case": _clean(direction["use_case"]),
                "Scene": _clean(direction["scene"]),
                "Prompt": prompt,
                "Word Count": word_count,
                "Negative Constraints": _clean(direction["negative_constraints"]),
                "Production Status": "Ready for manual image prompt testing",
            }
        )

    return pd.DataFrame(rows, columns=PROMPT_VARIATION_COLUMNS)


def write_prompt_variation_outputs(
    prompt_variations: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Export prompt variations to Excel and Markdown."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        prompt_variations.to_excel(writer, sheet_name="Prompt Variations", index=False)

    output_report.write_text(build_prompt_variation_report(prompt_variations), encoding="utf-8")


def build_prompt_variation_report(prompt_variations: pd.DataFrame) -> str:
    """Create a Markdown prompt report with clearly named versions."""

    lines = [
        "# Scene DNA Prompt Variations",
        "",
        "Prompts are generated from accepted creative directions. This phase does not generate images or call image APIs.",
        "",
    ]

    if prompt_variations.empty:
        lines.append("No prompt variations were generated.")
        return "\n".join(lines) + "\n"

    grouped = prompt_variations.groupby(["Asset", "Buyer", "Use Case"], sort=False)
    for (asset, buyer, use_case), group in grouped:
        lines.extend(
            [
                f"## {asset}",
                "",
                f"- **Buyer:** {buyer}",
                f"- **Use Case:** {use_case}",
                f"- **Prompt Variations:** {len(group)}",
                "",
            ]
        )

        for _, row in group.iterrows():
            lines.extend(
                [
                    f"### {row['Version']}",
                    "",
                    f"- **Prompt ID:** {row['Prompt ID']}",
                    f"- **Scene:** {row['Scene']}",
                    f"- **Word Count:** {row['Word Count']}",
                    "",
                    row["Prompt"],
                    "",
                ]
            )

    return "\n".join(lines) + "\n"


def _build_prompt(direction: pd.Series) -> str:
    scene = _clean(direction["scene"])
    asset = _clean(direction["asset"])
    use_case = _clean(direction["use_case"])
    architecture = _clean(direction["architecture"])
    layout = _clean(direction["layout"])
    materials = _clean(direction["materials"])
    lighting = _clean(direction["lighting"])
    camera = _clean(direction["camera"])
    composition = _clean(direction["composition"])
    copy_space = _clean(direction["copy_space"])
    constraints = _clean(direction["negative_constraints"])

    return (
        f"Ultra realistic commercial stock image showing {scene} designed around a {asset}. "
        f"Show {architecture}, with {layout}. Use {materials}. "
        f"Light the scene with {lighting}. Capture it using {camera}, arranged as {composition}. "
        f"Keep the image useful for {use_case}: clear product placement, credible healthcare retail context, "
        f"and {copy_space}. The scene should feel distinct, premium, globally usable, and practical for "
        "packaging presentations, website hero layouts, sales decks, ecommerce banners, and campaign visuals. "
        "Prioritize realistic scale, clean geometry, believable shelf depth, refined color balance, accurate "
        "shadows, and polished Adobe Stock commercial quality. Negative constraints: "
        f"{constraints}. Avoid decorative filler, unreadable clutter, fantasy styling, exaggerated medical claims, "
        "or anything that resembles a real brand, logo, label, trademarked package, person, hand, or copyrighted object."
    )


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
