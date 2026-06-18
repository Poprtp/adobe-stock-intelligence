"""Opportunity Intelligence Engine.

Milestone M7 answers "What should we create next?" before prompt generation.
It ranks seeded Adobe Stock opportunities from local CSV data only; it does not
generate images, call image APIs, use web research, or sync Google Sheets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


OPPORTUNITY_COLUMNS = [
    "Rank",
    "Opportunity ID",
    "Opportunity",
    "Asset",
    "Recommended Collection",
    "Primary Buyer",
    "Primary Use Case",
    "Overall Score",
    "Demand",
    "Competition",
    "Commercial Value",
    "Reusability",
    "Approval Risk",
    "Revenue Potential",
    "Seasonality",
    "Score Breakdown",
    "Recommendation",
    "Reasoning",
]

SCORE_WEIGHTS = {
    "demand": 0.20,
    "competition": 0.15,
    "commercial_value": 0.20,
    "reusability": 0.15,
    "approval_risk": 0.10,
    "revenue_potential": 0.15,
    "seasonality": 0.05,
}


@dataclass(frozen=True)
class OpportunityPaths:
    opportunities: Path
    buyers: Path
    use_cases: Path
    market_scores: Path


def load_opportunity_inputs(paths: OpportunityPaths) -> dict[str, pd.DataFrame]:
    """Load and validate M7 opportunity intelligence seed data."""

    return {
        "opportunities": _read_csv(
            paths.opportunities,
            [
                "opportunity_id",
                "opportunity_name",
                "asset_name",
                "collection_theme",
                "buyer_id",
                "use_case_id",
                "market_id",
                "recommended_collection",
                "reasoning_seed",
            ],
        ),
        "buyers": _read_csv(
            paths.buyers,
            [
                "buyer_id",
                "buyer_name",
                "industry",
                "primary_goal",
                "budget_signal",
                "approval_sensitivity",
                "notes",
            ],
        ),
        "use_cases": _read_csv(
            paths.use_cases,
            [
                "use_case_id",
                "use_case_name",
                "channel",
                "commercial_intent",
                "required_copy_space",
                "format_priority",
                "notes",
            ],
        ),
        "market_scores": _read_csv(
            paths.market_scores,
            [
                "market_id",
                "demand",
                "competition",
                "commercial_value",
                "reusability",
                "approval_risk",
                "revenue_potential",
                "seasonality",
                "market_notes",
            ],
        ),
    }


def rank_opportunities(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Join seed data and produce deterministic ranked opportunities."""

    required_keys = {"opportunities", "buyers", "use_cases", "market_scores"}
    missing_keys = required_keys - set(inputs)
    if missing_keys:
        raise ValueError(f"Missing opportunity input tables: {sorted(missing_keys)}")

    joined = (
        inputs["opportunities"]
        .merge(inputs["buyers"], on="buyer_id", how="left", validate="many_to_one")
        .merge(inputs["use_cases"], on="use_case_id", how="left", validate="many_to_one")
        .merge(inputs["market_scores"], on="market_id", how="left", validate="many_to_one")
    )

    if joined[["buyer_name", "use_case_name", "demand"]].isna().any().any():
        raise ValueError("Opportunity seed data contains unresolved buyer, use case, or market references.")

    rows = []
    for _, row in joined.iterrows():
        score = _overall_score(row)
        rows.append(
            {
                "Opportunity ID": row["opportunity_id"],
                "Opportunity": row["opportunity_name"],
                "Asset": row["asset_name"],
                "Recommended Collection": row["recommended_collection"],
                "Primary Buyer": row["buyer_name"],
                "Primary Use Case": row["use_case_name"],
                "Overall Score": score,
                "Demand": int(row["demand"]),
                "Competition": int(row["competition"]),
                "Commercial Value": int(row["commercial_value"]),
                "Reusability": int(row["reusability"]),
                "Approval Risk": int(row["approval_risk"]),
                "Revenue Potential": int(row["revenue_potential"]),
                "Seasonality": int(row["seasonality"]),
                "Score Breakdown": _score_breakdown(row),
                "Recommendation": _recommendation(score),
                "Reasoning": _reasoning(row, score),
            }
        )

    ranked = (
        pd.DataFrame(rows)
        .sort_values(
            by=["Overall Score", "Commercial Value", "Demand", "Opportunity ID"],
            ascending=[False, False, False, True],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )
    ranked.insert(0, "Rank", ranked.index + 1)
    return ranked[OPPORTUNITY_COLUMNS]


def write_opportunity_outputs(
    ranked_opportunities: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Export ranked opportunities to Excel and Markdown."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        ranked_opportunities.to_excel(writer, sheet_name="Opportunity Ranking", index=False)

    output_report.write_text(build_opportunity_report(ranked_opportunities), encoding="utf-8")


def build_opportunity_report(ranked_opportunities: pd.DataFrame) -> str:
    """Create a Markdown opportunity ranking report."""

    lines = [
        "# Opportunity Intelligence Ranking",
        "",
        "This report ranks seeded Adobe Stock opportunities before prompt generation.",
        "It is deterministic from local seed data and does not use image generation or external web research.",
        "",
        "## Scoring Dimensions",
        "",
        "- Demand",
        "- Competition",
        "- Commercial Value",
        "- Reusability",
        "- Approval Risk",
        "- Revenue Potential",
        "- Seasonality",
        "",
    ]

    if ranked_opportunities.empty:
        lines.append("No ranked opportunities were generated.")
        return "\n".join(lines) + "\n"

    for _, row in ranked_opportunities.iterrows():
        lines.extend(
            [
                f"## {row['Rank']}. {row['Opportunity']}",
                "",
                f"- **Overall Score:** {row['Overall Score']}",
                f"- **Recommended Collection:** {row['Recommended Collection']}",
                f"- **Primary Buyer:** {row['Primary Buyer']}",
                f"- **Primary Use Case:** {row['Primary Use Case']}",
                f"- **Score Breakdown:** {row['Score Breakdown']}",
                f"- **Recommendation:** {row['Recommendation']}",
                f"- **Reasoning:** {row['Reasoning']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def _overall_score(row: pd.Series) -> int:
    weighted_total = 0.0
    for field, weight in SCORE_WEIGHTS.items():
        value = float(row[field])
        signal = 11 - value if field in {"competition", "approval_risk", "seasonality"} else value
        weighted_total += signal * weight
    return int(round(weighted_total * 10))


def _score_breakdown(row: pd.Series) -> str:
    return (
        f"Demand {int(row['demand'])}/10; "
        f"Competition {int(row['competition'])}/10 inverse; "
        f"Commercial Value {int(row['commercial_value'])}/10; "
        f"Reusability {int(row['reusability'])}/10; "
        f"Approval Risk {int(row['approval_risk'])}/10 inverse; "
        f"Revenue Potential {int(row['revenue_potential'])}/10; "
        f"Seasonality {int(row['seasonality'])}/10 inverse"
    )


def _recommendation(score: int) -> str:
    if score >= 85:
        return "Create next"
    if score >= 78:
        return "Test collection"
    if score >= 70:
        return "Backlog for later"
    return "Do not prioritize yet"


def _reasoning(row: pd.Series, score: int) -> str:
    return (
        f"{row['reasoning_seed']}. Demand {int(row['demand'])}/10, commercial value "
        f"{int(row['commercial_value'])}/10, and reusability {int(row['reusability'])}/10 "
        f"support a {score}/100 score for {row['buyer_name']} using it as {row['use_case_name']}. "
        f"{row['market_notes']}"
    )


def _read_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Opportunity seed file not found: {path}")

    dataframe = pd.read_csv(path).fillna("")
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    if dataframe.empty:
        raise ValueError(f"{path.name} must contain at least one row.")
    return dataframe
