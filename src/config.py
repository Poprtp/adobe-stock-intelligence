"""Project configuration for the Phase 1 scoring pipeline."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

INPUT_WORKBOOK = DATA_DIR / "Adobe_Stock_Intelligence_Database_v2.xlsx"
NICHE_SHEET_NAME = "Niche Database"

OUTPUT_WORKBOOK = OUTPUT_DIR / "opportunity_ranking.xlsx"
SUMMARY_REPORT = OUTPUT_DIR / "summary_report.md"

# Knowledge layer inputs
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
BUYERS_CSV = KNOWLEDGE_DIR / "buyers.csv"
USE_CASES_CSV = KNOWLEDGE_DIR / "use_cases.csv"
ASSETS_CSV = KNOWLEDGE_DIR / "assets.csv"
OPPORTUNITIES_CSV = KNOWLEDGE_DIR / "opportunities.csv"
SCENE_LIBRARY_CSV = KNOWLEDGE_DIR / "scene_library.csv"
MATERIAL_LIBRARY_CSV = KNOWLEDGE_DIR / "material_library.csv"
LIGHTING_LIBRARY_CSV = KNOWLEDGE_DIR / "lighting_library.csv"
CAMERA_LIBRARY_CSV = KNOWLEDGE_DIR / "camera_library.csv"
COMPOSITION_LIBRARY_CSV = KNOWLEDGE_DIR / "composition_library.csv"

KNOWLEDGE_WORKBOOK = OUTPUT_DIR / "knowledge_ranking.xlsx"
KNOWLEDGE_REPORT = OUTPUT_DIR / "knowledge_summary.md"

# Design brief outputs
DESIGN_BRIEFS_WORKBOOK = OUTPUT_DIR / "design_briefs.xlsx"
DESIGN_BRIEFS_REPORT = OUTPUT_DIR / "design_briefs.md"

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
PROMPT_VARIATIONS_WORKBOOK = OUTPUT_DIR / "prompt_variations.xlsx"
PROMPT_VARIATIONS_REPORT = OUTPUT_DIR / "prompt_variations.md"
