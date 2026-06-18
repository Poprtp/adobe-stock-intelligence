"""Opportunity scoring utilities.

The scoring model uses only structured columns already present in the Niche
Database. Competition and AI Saturation use inverse scoring because lower
values are better for a stock contributor looking for less crowded commercial
niches.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from config import PRIORITY_BANDS, SCORING_COLUMNS


class ScoringError(ValueError):
    """Raised when the input data cannot be scored safely."""


def available_scoring_columns(
    dataframe: pd.DataFrame,
    scoring_columns: Mapping[str, Mapping[str, float | bool]] = SCORING_COLUMNS,
) -> list[str]:
    """Return configured scoring columns that are present in the dataframe."""

    return [column for column in scoring_columns if column in dataframe.columns]


def clean_niche_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove workbook template rows that do not describe a real niche."""

    if "Niche" not in dataframe.columns:
        raise ScoringError("The Niche Database sheet must include a 'Niche' column.")

    cleaned = dataframe.copy()
    niche_text = cleaned["Niche"].astype("string").str.strip()
    return cleaned[niche_text.notna() & (niche_text != "")].copy()


def calculate_opportunity_scores(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculate Opportunity Score from all available scoring columns.

    Scores are normalized to a 0-100 scale. Each configured weight represents
    the model percentage for that signal. If a row has only some scoring inputs
    populated, the score is calculated from the available configured weights
    and the number of inputs used is recorded for auditability.
    """

    scored = clean_niche_rows(dataframe)
    scoring_columns = available_scoring_columns(scored)
    if not scoring_columns:
        expected = ", ".join(SCORING_COLUMNS)
        raise ScoringError(f"No scoring columns found. Expected at least one of: {expected}")

    weighted_total = pd.Series(0.0, index=scored.index)
    weight_total = pd.Series(0.0, index=scored.index)
    inputs_used = pd.Series(0, index=scored.index)

    for column in scoring_columns:
        config = SCORING_COLUMNS[column]
        numeric = pd.to_numeric(scored[column], errors="coerce").clip(lower=1, upper=10)
        signal = 11 - numeric if config["inverse"] else numeric
        valid = signal.notna()
        weight = float(config["weight"])

        weighted_total.loc[valid] += signal.loc[valid] * weight
        weight_total.loc[valid] += 10 * weight
        inputs_used.loc[valid] += 1

    score = (weighted_total / weight_total * 100).round()
    scored["Opportunity Score"] = score.where(weight_total > 0)
    scored["Score Inputs Used"] = inputs_used
    scored["Calculated Priority"] = scored["Opportunity Score"].apply(assign_priority)

    return scored.sort_values(
        by=["Opportunity Score", "Commercial Value (1-10)", "Demand (1-10)"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)


def assign_priority(score: float | int | None) -> str:
    """Convert a 0-100 opportunity score into a simple priority label."""

    if pd.isna(score):
        return "Unscored"

    numeric_score = float(score)
    for minimum_score, label in PRIORITY_BANDS:
        if numeric_score >= minimum_score:
            return label
    return "Avoid"
