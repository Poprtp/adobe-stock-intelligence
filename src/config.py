"""Project configuration for the Phase 1 scoring pipeline."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
INTERNAL_OUTPUT_DIR = PROJECT_ROOT / "internal_output"
PRODUCTION_DIR = PROJECT_ROOT / "production"
PRODUCTION_COLLECTIONS_DIR = PRODUCTION_DIR / "01_Collections"
PRODUCTION_PROMPTS_DIR = PRODUCTION_DIR / "02_Production_Prompts"
PRODUCTION_GENERATED_DIR = PRODUCTION_DIR / "03_Generated"
PRODUCTION_SELECTED_DIR = PRODUCTION_DIR / "04_Selected"
PRODUCTION_UPLOAD_DIR = PRODUCTION_DIR / "05_Upload"
GOLD_STANDARD_DIR = PROJECT_ROOT / "gold_standard"
PORTFOLIO_DIR = PROJECT_ROOT / "portfolio"
DOCS_DIR = PROJECT_ROOT / "docs"

INPUT_WORKBOOK = DATA_DIR / "Adobe_Stock_Intelligence_Database_v2.xlsx"
NICHE_SHEET_NAME = "Niche Database"

OUTPUT_WORKBOOK = OUTPUT_DIR / "opportunity_ranking.xlsx"
OPPORTUNITY_RANKING_REPORT = OUTPUT_DIR / "opportunity_ranking.md"
SUMMARY_REPORT = OUTPUT_DIR / "summary_report.md"
INTERNAL_OPPORTUNITY_RANKING_WORKBOOK = INTERNAL_OUTPUT_DIR / "opportunity_ranking.xlsx"
INTERNAL_OPPORTUNITY_RANKING_REPORT = INTERNAL_OUTPUT_DIR / "opportunity_ranking.md"
PRODUCTION_STATUS_CSV = PRODUCTION_DIR / "prompt_status.csv"

# Knowledge layer inputs
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
BUYERS_CSV = KNOWLEDGE_DIR / "buyers.csv"
USE_CASES_CSV = KNOWLEDGE_DIR / "use_cases.csv"
ASSETS_CSV = KNOWLEDGE_DIR / "assets.csv"
OPPORTUNITIES_CSV = KNOWLEDGE_DIR / "opportunities.csv"
OPPORTUNITY_DATABASE_CSV = KNOWLEDGE_DIR / "opportunity_database.csv"
BUYER_DATABASE_CSV = KNOWLEDGE_DIR / "buyer_database.csv"
USE_CASE_DATABASE_CSV = KNOWLEDGE_DIR / "use_case_database.csv"
MARKET_SCORE_CSV = KNOWLEDGE_DIR / "market_score.csv"
SCENE_LIBRARY_CSV = KNOWLEDGE_DIR / "scene_library.csv"
MATERIAL_LIBRARY_CSV = KNOWLEDGE_DIR / "material_library.csv"
LIGHTING_LIBRARY_CSV = KNOWLEDGE_DIR / "lighting_library.csv"
CAMERA_LIBRARY_CSV = KNOWLEDGE_DIR / "camera_library.csv"
COMPOSITION_LIBRARY_CSV = KNOWLEDGE_DIR / "composition_library.csv"
ASSET_DNA_CSV = KNOWLEDGE_DIR / "asset_dna.csv"
SCENE_DNA_CSV = KNOWLEDGE_DIR / "scene_dna.csv"
MATERIAL_DNA_CSV = KNOWLEDGE_DIR / "material_dna.csv"
LIGHTING_DNA_CSV = KNOWLEDGE_DIR / "lighting_dna.csv"
CAMERA_DNA_CSV = KNOWLEDGE_DIR / "camera_dna.csv"
COMPOSITION_DNA_CSV = KNOWLEDGE_DIR / "composition_dna.csv"
COMMERCIAL_DNA_CSV = KNOWLEDGE_DIR / "commercial_dna.csv"

KNOWLEDGE_WORKBOOK = OUTPUT_DIR / "knowledge_ranking.xlsx"
KNOWLEDGE_REPORT = OUTPUT_DIR / "knowledge_summary.md"
INTERNAL_KNOWLEDGE_WORKBOOK = INTERNAL_OUTPUT_DIR / "knowledge_ranking.xlsx"
INTERNAL_KNOWLEDGE_REPORT = INTERNAL_OUTPUT_DIR / "knowledge_summary.md"

# Design brief outputs
DESIGN_BRIEFS_WORKBOOK = OUTPUT_DIR / "design_briefs.xlsx"
DESIGN_BRIEFS_REPORT = OUTPUT_DIR / "design_briefs.md"
INTERNAL_DESIGN_BRIEFS_WORKBOOK = INTERNAL_OUTPUT_DIR / "design_briefs.xlsx"
INTERNAL_DESIGN_BRIEFS_REPORT = INTERNAL_OUTPUT_DIR / "design_briefs.md"

IDENTITY_COLUMNS = [
    "Industry",
    "Niche",
    "Buyer Persona",
    "Job To Be Done",
]

SCORING_COLUMNS = {
    "Demand (1-10)": {"weight": 0.30, "inverse": False},
    "Competition (1-10)": {"weight": 0.25, "inverse": True},
    "Commercial Value (1-10)": {"weight": 0.20, "inverse": False},
    "Evergreen (1-10)": {"weight": 0.10, "inverse": False},
    "Repeat Use (1-10)": {"weight": 0.10, "inverse": False},
    "AI Saturation (1-10)": {"weight": 0.05, "inverse": True},
}

SCORE_COLUMN = "Opportunity Score"
SCORE_INPUTS_COLUMN = "Score Inputs Used"

PRIORITY_COLUMN = "Calculated Priority"
PRIORITY_BANDS = [
    (80, "High"),
    (65, "Medium"),
    (50, "Low"),
    (0, "Avoid"),
]

# Prompt strategy outputs
PROMPT_LIBRARY_WORKBOOK = OUTPUT_DIR / "prompt_library.xlsx"
PROMPT_LIBRARY_REPORT = OUTPUT_DIR / "prompt_library.md"

# Phase 6 commercial prompt engine outputs
CREATIVE_DIRECTIONS_WORKBOOK = OUTPUT_DIR / "creative_directions.xlsx"
CREATIVE_DIRECTIONS_REPORT = OUTPUT_DIR / "creative_directions.md"
PROMPT_VARIATIONS_WORKBOOK = OUTPUT_DIR / "prompt_variations.xlsx"
PROMPT_VARIATIONS_REPORT = OUTPUT_DIR / "prompt_variations.md"
INTERNAL_CREATIVE_DIRECTIONS_WORKBOOK = INTERNAL_OUTPUT_DIR / "creative_directions.xlsx"
INTERNAL_CREATIVE_DIRECTIONS_REPORT = INTERNAL_OUTPUT_DIR / "creative_directions.md"
INTERNAL_PROMPT_VARIATIONS_WORKBOOK = INTERNAL_OUTPUT_DIR / "prompt_variations.xlsx"
INTERNAL_PROMPT_VARIATIONS_REPORT = INTERNAL_OUTPUT_DIR / "prompt_variations.md"
