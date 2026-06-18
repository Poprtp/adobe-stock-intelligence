"""Knowledge-layer utilities for the Adobe Stock Intelligence project.

The knowledge layer turns the project from a keyword scorer into a decision
engine. It links buyers, use cases, and commercial asset types, then ranks
asset opportunities based on business usefulness instead of visual taste.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


class KnowledgeBaseError(ValueError):
    """Raised when the knowledge base cannot be loaded or ranked safely."""


@dataclass(frozen=True)
class KnowledgePaths:
    """Paths to the knowledge CSV files."""

    buyers: Path
    use_cases: Path
    assets: Path
    opportunities: Path


def load_csv(path: Path, required_columns: Iterable[str]) -> pd.DataFrame:
    """Load a CSV file and validate required columns."""

    if not path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {path}")

    dataframe = pd.read_csv(path)
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise KnowledgeBaseError(f"{path.name} is missing required columns: {missing}")
    return dataframe


def load_knowledge_base(paths: KnowledgePaths) -> dict[str, pd.DataFrame]:
    """Load all knowledge base CSV files."""

    return {
        "buyers": load_csv(paths.buyers, ["Buyer ID", "Buyer Persona", "Industry"]),
        "use_cases": load_csv(paths.use_cases, ["Use Case ID", "Use Case"]),
        "assets": load_csv(paths.assets, ["Asset ID", "Asset", "Industry"]),
        "opportunities": load_csv(
            paths.opportunities,
            ["Opportunity ID", "Asset ID", "Buyer ID", "Use Case ID", "Niche"],
        ),
    }


def rank_assets(assets: pd.DataFrame) -> pd.DataFrame:
    """Rank commercial assets using the project investment criteria.

    Asset Score is intentionally different from Niche Opportunity Score.
    It rewards buyer breadth, commercial value, reusability, and evergreen
    usefulness, while penalizing competition and AI saturation.
    """

    ranked = assets.copy()
    numeric_columns = [
        "Buyer Count",
        "Commercial Value (1-10)",
        "Reusable (1-10)",
        "Evergreen (1-10)",
        "Competition (1-10)",
        "AI Saturation (1-10)",
    ]

    for column in numeric_columns:
        if column not in ranked.columns:
            raise KnowledgeBaseError(f"assets.csv is missing scoring column: {column}")
        ranked[column] = pd.to_numeric(ranked[column], errors="coerce").clip(lower=1, upper=10)

    buyer_signal = (ranked["Buyer Count"].clip(upper=8) / 8) * 10
    competition_signal = 11 - ranked["Competition (1-10)"]
    saturation_signal = 11 - ranked["AI Saturation (1-10)"]

    weighted = (
        buyer_signal * 0.25
        + ranked["Commercial Value (1-10)"] * 0.25
        + ranked["Reusable (1-10)"] * 0.15
        + ranked["Evergreen (1-10)"] * 0.15
        + competition_signal * 0.15
        + saturation_signal * 0.05
    )

    ranked["Asset Score"] = (weighted * 10).round().astype("Int64")
    ranked["Investment Decision"] = ranked["Asset Score"].apply(_asset_decision)

    return ranked.sort_values(
        by=["Asset Score", "Commercial Value (1-10)", "Buyer Count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def build_opportunity_map(knowledge_base: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create a joined Buyer -> Use Case -> Asset opportunity map."""

    buyers = knowledge_base["buyers"]
    use_cases = knowledge_base["use_cases"]
    ranked_assets = rank_assets(knowledge_base["assets"])
    opportunities = knowledge_base["opportunities"]

    merged = opportunities.merge(ranked_assets, on="Asset ID", how="left")
    merged = merged.merge(
        buyers[["Buyer ID", "Buyer Persona", "Department", "Primary Goal", "Priority"]],
        on="Buyer ID",
        how="left",
        suffixes=("", " Buyer"),
    )
    merged = merged.merge(
        use_cases[["Use Case ID", "Use Case", "Commercial Value (1-10)", "Repeat Use (1-10)"]],
        on="Use Case ID",
        how="left",
        suffixes=("", " Use Case"),
    )

    merged["Recommendation Reason"] = merged.apply(_recommendation_reason, axis=1)

    columns = [
        "Opportunity ID",
        "Asset Score",
        "Investment Decision",
        "Asset",
        "Industry",
        "Niche",
        "Buyer Persona",
        "Use Case",
        "Primary Goal",
        "Design Direction",
        "Recommended Aspect Ratios",
        "Recommendation Reason",
        "Notes",
    ]
    return merged[columns].sort_values(by="Asset Score", ascending=False).reset_index(drop=True)


def write_knowledge_outputs(
    ranked_assets: pd.DataFrame,
    opportunity_map: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Write knowledge-layer ranking files."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        ranked_assets.to_excel(writer, sheet_name="Asset Ranking", index=False)
        opportunity_map.to_excel(writer, sheet_name="Opportunity Map", index=False)

    output_report.write_text(build_knowledge_report(ranked_assets, opportunity_map), encoding="utf-8")


def build_knowledge_report(ranked_assets: pd.DataFrame, opportunity_map: pd.DataFrame) -> str:
    """Generate a concise Markdown report for the knowledge layer."""

    lines = [
        "# Commercial Asset Knowledge Summary",
        "",
        "This report ranks commercial visual asset opportunities using the BUY Framework:",
        "Buyer → Use Case → Asset → Opportunity.",
        "",
        "## Top Commercial Assets",
        "",
        "| Rank | Asset | Industry | Score | Decision | Primary Buyers |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ]

    for index, row in ranked_assets.head(10).iterrows():
        lines.append(
            f"| {index + 1} | {_md(row.get('Asset'))} | {_md(row.get('Industry'))} | "
            f"{_md(row.get('Asset Score'))} | {_md(row.get('Investment Decision'))} | "
            f"{_md(row.get('Primary Buyers'))} |"
        )

    lines.extend(["", "## Top Buyer-Led Opportunities", ""])
    lines.extend(["| Rank | Asset | Buyer | Use Case | Reason |", "| ---: | --- | --- | --- | --- |"])

    for index, row in opportunity_map.head(10).iterrows():
        lines.append(
            f"| {index + 1} | {_md(row.get('Asset'))} | {_md(row.get('Buyer Persona'))} | "
            f"{_md(row.get('Use Case'))} | {_md(row.get('Recommendation Reason'))} |"
        )

    lines.extend(
        [
            "",
            "## Next Production Recommendation",
            "",
            "Start with 10-image test collections for the highest-ranked assets only. Do not generate images for assets that lack a clear buyer and use case.",
        ]
    )
    return "\n".join(lines) + "\n"


def _asset_decision(score: object) -> str:
    if pd.isna(score):
        return "Unscored"
    score_int = int(score)
    if score_int >= 85:
        return "Invest"
    if score_int >= 75:
        return "Test"
    if score_int >= 60:
        return "Watch"
    return "Avoid"


def _recommendation_reason(row: pd.Series) -> str:
    asset = row.get("Asset", "this asset")
    buyer = row.get("Buyer Persona", "the target buyer")
    use_case = row.get("Use Case", "the target use case")
    score = row.get("Asset Score", "")
    return f"{asset} serves {buyer} for {use_case} with asset score {score}."


def _md(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("|", "\\|").strip()
