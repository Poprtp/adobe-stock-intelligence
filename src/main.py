"""Phase 1 pipeline for the Adobe Stock Intelligence project."""

from __future__ import annotations

import sys

import pandas as pd

from config import (
    ASSETS_CSV,
    BUYERS_CSV,
    INPUT_WORKBOOK,
    KNOWLEDGE_REPORT,
    KNOWLEDGE_WORKBOOK,
    DESIGN_BRIEFS_WORKBOOK,
    DESIGN_BRIEFS_REPORT,
    PROMPT_VARIATIONS_WORKBOOK,
    PROMPT_VARIATIONS_REPORT,
    SCENE_LIBRARY_CSV,
    MATERIAL_LIBRARY_CSV,
    LIGHTING_LIBRARY_CSV,
    CAMERA_LIBRARY_CSV,
    COMPOSITION_LIBRARY_CSV,
    NICHE_SHEET_NAME,
    OPPORTUNITIES_CSV,
    OUTPUT_WORKBOOK,
    SUMMARY_REPORT,
    USE_CASES_CSV,
)
from excel_writer import write_opportunity_workbook, write_summary_report
from design_brief_generator import generate_design_briefs, write_design_brief_outputs
from commercial_prompt_engine import (
    PromptLibraryPaths,
    generate_prompt_variations,
    load_prompt_libraries,
    write_prompt_variation_outputs,
)
from knowledge_engine import (
    KnowledgePaths,
    build_opportunity_map,
    load_knowledge_base,
    rank_assets,
    write_knowledge_outputs,
)
from scoring import ScoringError, calculate_opportunity_scores, clean_niche_rows


def load_niche_database() -> pd.DataFrame:
    """Load the Niche Database sheet from the configured Excel workbook."""

    if not INPUT_WORKBOOK.exists():
        raise FileNotFoundError(f"Input workbook not found: {INPUT_WORKBOOK}")

    try:
        return pd.read_excel(INPUT_WORKBOOK, sheet_name=NICHE_SHEET_NAME)
    except ValueError as exc:
        raise ValueError(
            f"Sheet '{NICHE_SHEET_NAME}' was not found in {INPUT_WORKBOOK.name}."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Unable to read input workbook: {INPUT_WORKBOOK}") from exc


def run_pipeline() -> tuple[int, int, int, int]:
    """Run the full scoring, reporting, and knowledge-layer pipeline."""

    niche_data = load_niche_database()
    valid_niche_rows = len(clean_niche_rows(niche_data))
    scored_data = calculate_opportunity_scores(niche_data)
    scored_niche_rows = int(scored_data["Opportunity Score"].notna().sum())

    write_opportunity_workbook(scored_data, OUTPUT_WORKBOOK)
    write_summary_report(scored_data, SUMMARY_REPORT)

    knowledge_base = load_knowledge_base(
        KnowledgePaths(
            buyers=BUYERS_CSV,
            use_cases=USE_CASES_CSV,
            assets=ASSETS_CSV,
            opportunities=OPPORTUNITIES_CSV,
        )
    )
    ranked_assets = rank_assets(knowledge_base["assets"])
    opportunity_map = build_opportunity_map(knowledge_base)
    write_knowledge_outputs(ranked_assets, opportunity_map, KNOWLEDGE_WORKBOOK, KNOWLEDGE_REPORT)

    design_briefs = generate_design_briefs(opportunity_map, max_briefs=10)
    write_design_brief_outputs(design_briefs, DESIGN_BRIEFS_WORKBOOK, DESIGN_BRIEFS_REPORT)

    prompt_libraries = load_prompt_libraries(
        PromptLibraryPaths(
            scenes=SCENE_LIBRARY_CSV,
            materials=MATERIAL_LIBRARY_CSV,
            lighting=LIGHTING_LIBRARY_CSV,
            camera=CAMERA_LIBRARY_CSV,
            composition=COMPOSITION_LIBRARY_CSV,
        )
    )
    prompt_variations = generate_prompt_variations(design_briefs, prompt_libraries)
    write_prompt_variation_outputs(
        prompt_variations,
        PROMPT_VARIATIONS_WORKBOOK,
        PROMPT_VARIATIONS_REPORT,
    )

    return (
        len(niche_data),
        valid_niche_rows,
        scored_niche_rows,
        len(ranked_assets),
        len(design_briefs),
        len(prompt_variations),
    )


def main() -> int:
    try:
        total_rows, valid_niche_rows, scored_niche_rows, ranked_asset_rows, design_brief_rows, prompt_rows = run_pipeline()
    except (FileNotFoundError, ValueError, RuntimeError, ScoringError) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Pipeline complete: "
        f"total worksheet rows={total_rows}, "
        f"valid niche rows={valid_niche_rows}, "
        f"scored niche rows={scored_niche_rows}, "
        f"ranked asset rows={ranked_asset_rows}, "
        f"design brief rows={design_brief_rows}, "
        f"prompt variation rows={prompt_rows}, "
        f"wrote {OUTPUT_WORKBOOK}, {SUMMARY_REPORT}, {KNOWLEDGE_WORKBOOK}, {KNOWLEDGE_REPORT}, {DESIGN_BRIEFS_WORKBOOK}, {DESIGN_BRIEFS_REPORT}, {PROMPT_VARIATIONS_WORKBOOK}, and {PROMPT_VARIATIONS_REPORT}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
