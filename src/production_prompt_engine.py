"""Production prompt workspace writer.

This module converts internal ranking and prompt outputs into collection-ready
Markdown files for day-to-day Adobe Stock production. It does not generate
images, call image APIs, perform web research, or upload to Adobe Stock.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


PRODUCTION_COLUMNS = [
    "Collection",
    "Industry",
    "Output Path",
    "Prompt Count",
    "Primary Buyer",
    "Primary Use Case",
]


def ensure_workspace_dirs(paths: list[Path]) -> None:
    """Create workspace directories used by the local production workflow."""

    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def write_production_prompt_files(
    ranked_opportunities: pd.DataFrame,
    prompt_variations: pd.DataFrame,
    production_prompts_dir: Path,
    status_csv: Path,
    max_collections: int = 5,
) -> pd.DataFrame:
    """Write one clean Markdown production file per selected collection."""

    if ranked_opportunities.empty:
        return pd.DataFrame(columns=PRODUCTION_COLUMNS)

    required_opportunity = [
        "Rank",
        "Opportunity",
        "Asset",
        "Recommended Collection",
        "Primary Buyer",
        "Primary Use Case",
        "Reasoning",
    ]
    required_prompts = ["Version", "Asset", "Buyer", "Use Case", "Scene", "Prompt"]
    _require_columns(ranked_opportunities, required_opportunity, "ranked opportunities")
    _require_columns(prompt_variations, required_prompts, "prompt variations")

    production_prompts_dir.mkdir(parents=True, exist_ok=True)
    status_rows = []
    summary_rows = []

    selected = ranked_opportunities.sort_values(by="Rank").head(max_collections)
    for _, opportunity in selected.iterrows():
        matching_prompts = _matching_prompts(opportunity, prompt_variations)
        if matching_prompts.empty:
            continue

        industry = _industry_for_opportunity(opportunity)
        collection_dir = production_prompts_dir / _safe_filename(industry)
        collection_dir.mkdir(parents=True, exist_ok=True)

        asset = _clean(opportunity["Asset"])
        output_path = collection_dir / f"{_safe_filename(asset)}.md"
        prompt_count = min(10, len(matching_prompts))
        output_path.write_text(
            _build_collection_markdown(opportunity, matching_prompts.head(prompt_count)),
            encoding="utf-8",
        )

        summary_rows.append(
            {
                "Collection": asset,
                "Industry": industry,
                "Output Path": str(output_path),
                "Prompt Count": prompt_count,
                "Primary Buyer": _clean(opportunity["Primary Buyer"]),
                "Primary Use Case": _clean(opportunity["Primary Use Case"]),
            }
        )

        for index, prompt in matching_prompts.head(prompt_count).iterrows():
            status_rows.append(
                {
                    "collection": asset,
                    "prompt_id": _clean(prompt.get("Prompt ID")) or f"P{index + 1:03d}",
                    "version": _clean(prompt["Version"]),
                    "scene": _clean(prompt["Scene"]),
                    "status": "Todo",
                    "notes": "",
                }
            )

    if status_rows:
        status_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(status_rows).to_csv(status_csv, index=False)

    return pd.DataFrame(summary_rows, columns=PRODUCTION_COLUMNS)


def _build_collection_markdown(opportunity: pd.Series, prompts: pd.DataFrame) -> str:
    asset = _clean(opportunity["Asset"])
    buyer = _clean(opportunity["Primary Buyer"])
    use_case = _clean(opportunity["Primary Use Case"])
    collection = _clean(opportunity["Recommended Collection"])
    reasoning = _clean(opportunity["Reasoning"])

    lines = [
        f"# {asset}",
        "",
        f"Buyer: {buyer}",
        f"Use Case: {use_case}",
        f"Collection Goal: {_collection_goal(collection)}",
        f"Recommended Image Count: {len(prompts)}",
        "",
        "---",
        "",
    ]

    intended_use = _intended_use(use_case)
    for index, (_, prompt) in enumerate(prompts.iterrows(), start=1):
        scene_name = _scene_from_version(_clean(prompt["Version"]))
        lines.extend(
            [
                f"## Image {index:02d} — {scene_name}",
                "",
                "### Production Prompt",
                _clean(prompt["Prompt"]),
                "",
                "### Intended Use",
                intended_use,
                "",
                "### Notes",
                _notes_for_prompt(index, reasoning),
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def _matching_prompts(opportunity: pd.Series, prompt_variations: pd.DataFrame) -> pd.DataFrame:
    asset = _clean(opportunity["Asset"])
    buyer = _clean(opportunity["Primary Buyer"])
    use_case = _clean(opportunity["Primary Use Case"])
    matched = prompt_variations[
        (prompt_variations["Asset"] == asset)
        & (prompt_variations["Buyer"] == buyer)
        & (prompt_variations["Use Case"] == use_case)
    ]
    return matched.reset_index(drop=True)


def _industry_for_opportunity(opportunity: pd.Series) -> str:
    asset_text = " ".join(
        [
            _clean(opportunity.get("Asset")),
            _clean(opportunity.get("Opportunity")),
            _clean(opportunity.get("Primary Buyer")),
        ]
    ).lower()
    if any(token in asset_text for token in ["pharmacy", "healthcare", "clinic", "dental", "medical"]):
        return "Healthcare"
    if "pet" in asset_text:
        return "Pet"
    if any(token in asset_text for token in ["fmcg", "frozen", "coffee", "packaging", "retail"]):
        return "FMCG"
    if "warehouse" in asset_text or "logistics" in asset_text:
        return "Logistics"
    if "industrial" in asset_text or "manufacturing" in asset_text:
        return "Manufacturing"
    return "General"


def _collection_goal(collection: str) -> str:
    cleaned = collection.strip()
    if not cleaned:
        return "Premium Commercial Marketing Collection"
    return cleaned[0].upper() + cleaned[1:]


def _intended_use(use_case: str) -> str:
    base = [use_case, "website hero", "sales deck"]
    unique = []
    for item in base:
        item = item.strip()
        if item and item.lower() not in [existing.lower() for existing in unique]:
            unique.append(item)
    return ", ".join(unique)


def _notes_for_prompt(index: int, reasoning: str) -> str:
    if index == 1:
        return "Use this as the first gold-standard candidate."
    if reasoning:
        return f"Keep aligned with the collection strategy: {reasoning}"
    return "Use this as a production-ready variation for the same collection."


def _scene_from_version(version: str) -> str:
    if "—" in version:
        return version.split("—", 1)[1].strip()
    if "-" in version:
        return version.split("-", 1)[1].strip()
    return version


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "", value).strip()
    return cleaned or "Untitled"


def _require_columns(dataframe: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
