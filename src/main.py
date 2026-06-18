"""Phase 1 pipeline for the Adobe Stock Intelligence project."""

from __future__ import annotations

import sys

import pandas as pd

from config import (
    ASSETS_CSV,
    ASSET_DNA_CSV,
    BUYER_DATABASE_CSV,
    BUYERS_CSV,
    CAMERA_DNA_CSV,
    COMMERCIAL_DNA_CSV,
    COMPOSITION_DNA_CSV,
    CREATIVE_DIRECTIONS_REPORT,
    CREATIVE_DIRECTIONS_WORKBOOK,
    DOCS_DIR,
    GOLD_STANDARD_DIR,
    INPUT_WORKBOOK,
    INTERNAL_CREATIVE_DIRECTIONS_REPORT,
    INTERNAL_CREATIVE_DIRECTIONS_WORKBOOK,
    INTERNAL_DESIGN_BRIEFS_REPORT,
    INTERNAL_DESIGN_BRIEFS_WORKBOOK,
    INTERNAL_KNOWLEDGE_REPORT,
    INTERNAL_KNOWLEDGE_WORKBOOK,
    INTERNAL_OPPORTUNITY_RANKING_REPORT,
    INTERNAL_OPPORTUNITY_RANKING_WORKBOOK,
    INTERNAL_OUTPUT_DIR,
    INTERNAL_PROMPT_VARIATIONS_REPORT,
    INTERNAL_PROMPT_VARIATIONS_WORKBOOK,
    KNOWLEDGE_REPORT,
    KNOWLEDGE_WORKBOOK,
    MARKET_SCORE_CSV,
    DESIGN_BRIEFS_WORKBOOK,
    DESIGN_BRIEFS_REPORT,
    LIGHTING_DNA_CSV,
    MATERIAL_DNA_CSV,
    PROMPT_VARIATIONS_WORKBOOK,
    PROMPT_VARIATIONS_REPORT,
    SCENE_DNA_CSV,
    NICHE_SHEET_NAME,
    OPPORTUNITY_DATABASE_CSV,
    OPPORTUNITY_RANKING_REPORT,
    OPPORTUNITIES_CSV,
    OUTPUT_WORKBOOK,
    PORTFOLIO_DIR,
    PRODUCTION_COLLECTIONS_DIR,
    PRODUCTION_DIR,
    PRODUCTION_GENERATED_DIR,
    PRODUCTION_PROMPTS_DIR,
    PRODUCTION_SELECTED_DIR,
    PRODUCTION_STATUS_CSV,
    PRODUCTION_UPLOAD_DIR,
    SUMMARY_REPORT,
    USE_CASE_DATABASE_CSV,
    USE_CASES_CSV,
)
from excel_writer import write_opportunity_workbook, write_summary_report
from design_brief_generator import generate_design_briefs, write_design_brief_outputs
from creative_direction_engine import (
    DNAPaths,
    generate_creative_directions,
    load_dna_libraries,
    write_creative_direction_outputs,
)
from commercial_prompt_engine import (
    generate_prompt_variations,
    write_prompt_variation_outputs,
)
from opportunity_engine import (
    OpportunityPaths,
    load_opportunity_inputs,
    rank_opportunities,
    write_opportunity_outputs,
)
from production_prompt_engine import ensure_workspace_dirs, write_production_prompt_files
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


def run_pipeline() -> tuple[int, int, int, int, int, int, int, int, int]:
    """Run the full scoring, reporting, and knowledge-layer pipeline."""

    ensure_workspace_dirs(
        [
            INTERNAL_OUTPUT_DIR,
            PRODUCTION_DIR,
            PRODUCTION_COLLECTIONS_DIR,
            PRODUCTION_PROMPTS_DIR,
            PRODUCTION_GENERATED_DIR,
            PRODUCTION_SELECTED_DIR,
            PRODUCTION_UPLOAD_DIR,
            GOLD_STANDARD_DIR,
            PORTFOLIO_DIR,
            DOCS_DIR,
        ]
    )

    niche_data = load_niche_database()
    valid_niche_rows = len(clean_niche_rows(niche_data))
    scored_data = calculate_opportunity_scores(niche_data)
    scored_niche_rows = int(scored_data["Opportunity Score"].notna().sum())

    write_opportunity_workbook(scored_data, OUTPUT_WORKBOOK)
    write_summary_report(scored_data, SUMMARY_REPORT)

    opportunity_inputs = load_opportunity_inputs(
        OpportunityPaths(
            opportunities=OPPORTUNITY_DATABASE_CSV,
            buyers=BUYER_DATABASE_CSV,
            use_cases=USE_CASE_DATABASE_CSV,
            market_scores=MARKET_SCORE_CSV,
        )
    )
    ranked_opportunities = rank_opportunities(opportunity_inputs)
    write_opportunity_outputs(
        ranked_opportunities,
        OUTPUT_WORKBOOK,
        OPPORTUNITY_RANKING_REPORT,
    )
    write_opportunity_outputs(
        ranked_opportunities,
        INTERNAL_OPPORTUNITY_RANKING_WORKBOOK,
        INTERNAL_OPPORTUNITY_RANKING_REPORT,
    )

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
    write_knowledge_outputs(
        ranked_assets,
        opportunity_map,
        INTERNAL_KNOWLEDGE_WORKBOOK,
        INTERNAL_KNOWLEDGE_REPORT,
    )

    design_briefs = generate_design_briefs(opportunity_map, max_briefs=10)
    write_design_brief_outputs(design_briefs, DESIGN_BRIEFS_WORKBOOK, DESIGN_BRIEFS_REPORT)
    write_design_brief_outputs(
        design_briefs,
        INTERNAL_DESIGN_BRIEFS_WORKBOOK,
        INTERNAL_DESIGN_BRIEFS_REPORT,
    )

    dna_libraries = load_dna_libraries(
        DNAPaths(
            asset_dna=ASSET_DNA_CSV,
            scene_dna=SCENE_DNA_CSV,
            material_dna=MATERIAL_DNA_CSV,
            lighting_dna=LIGHTING_DNA_CSV,
            camera_dna=CAMERA_DNA_CSV,
            composition_dna=COMPOSITION_DNA_CSV,
            commercial_dna=COMMERCIAL_DNA_CSV,
        )
    )
    creative_directions = generate_creative_directions(dna_libraries)
    write_creative_direction_outputs(
        creative_directions,
        CREATIVE_DIRECTIONS_WORKBOOK,
        CREATIVE_DIRECTIONS_REPORT,
    )
    write_creative_direction_outputs(
        creative_directions,
        INTERNAL_CREATIVE_DIRECTIONS_WORKBOOK,
        INTERNAL_CREATIVE_DIRECTIONS_REPORT,
    )

    prompt_variations = generate_prompt_variations(creative_directions)
    write_prompt_variation_outputs(
        prompt_variations,
        PROMPT_VARIATIONS_WORKBOOK,
        PROMPT_VARIATIONS_REPORT,
    )
    write_prompt_variation_outputs(
        prompt_variations,
        INTERNAL_PROMPT_VARIATIONS_WORKBOOK,
        INTERNAL_PROMPT_VARIATIONS_REPORT,
    )

    production_collections = write_production_prompt_files(
        ranked_opportunities,
        prompt_variations,
        PRODUCTION_PROMPTS_DIR,
        PRODUCTION_STATUS_CSV,
    )

    return (
        len(niche_data),
        valid_niche_rows,
        scored_niche_rows,
        len(ranked_opportunities),
        len(ranked_assets),
        len(design_briefs),
        len(creative_directions),
        len(prompt_variations),
        len(production_collections),
    )


def main() -> int:
    try:
        (
            total_rows,
            valid_niche_rows,
            scored_niche_rows,
            opportunity_rows,
            ranked_asset_rows,
            design_brief_rows,
            creative_direction_rows,
            prompt_rows,
            production_collection_rows,
        ) = run_pipeline()
    except (FileNotFoundError, ValueError, RuntimeError, ScoringError) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Pipeline complete: "
        f"total worksheet rows={total_rows}, "
        f"valid niche rows={valid_niche_rows}, "
        f"scored niche rows={scored_niche_rows}, "
        f"opportunity rows={opportunity_rows}, "
        f"ranked asset rows={ranked_asset_rows}, "
        f"design brief rows={design_brief_rows}, "
        f"creative direction rows={creative_direction_rows}, "
        f"prompt variation rows={prompt_rows}, "
        f"production collections={production_collection_rows}, "
        f"wrote {OUTPUT_WORKBOOK}, {OPPORTUNITY_RANKING_REPORT}, {INTERNAL_OUTPUT_DIR}, {PRODUCTION_PROMPTS_DIR}, and production workspace folders."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
