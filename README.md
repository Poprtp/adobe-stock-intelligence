# Adobe Stock Intelligence

Adobe Stock Intelligence is a market research and scoring system for Adobe
Stock contributors. The goal is to identify commercially useful stock asset
niches based on buyer needs, not to generate random decorative images.

The project follows the BUY Framework:

- Buyer: who buys this image?
- Use Case: what will they use it for?
- Why Buy: why would they choose this asset instead of another stock image?

## Project Purpose

This project helps rank stock content opportunities for commercial marketing
asset collections. It focuses on structured niche research, market demand,
competition, commercial value, evergreen usefulness, repeat use, and AI
saturation.

The pipeline reads the Niche Database from Excel, calculates Opportunity Score,
ranks commercial asset opportunities, creates design briefs, and generates
modular commercial prompt variations for manual production review.

## Install

Create and activate a Python environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

From the project root:

```powershell
python src/main.py
```

## Expected Files

Input workbook:

- `data/Adobe_Stock_Intelligence_Database_v2.xlsx`

Input sheet:

- `Niche Database`

Knowledge inputs:

- `knowledge/buyers.csv`
- `knowledge/use_cases.csv`
- `knowledge/assets.csv`
- `knowledge/opportunities.csv`
- `knowledge/opportunity_database.csv`
- `knowledge/buyer_database.csv`
- `knowledge/use_case_database.csv`
- `knowledge/market_score.csv`
- `knowledge/asset_dna.csv`
- `knowledge/scene_dna.csv`
- `knowledge/material_dna.csv`
- `knowledge/lighting_dna.csv`
- `knowledge/camera_dna.csv`
- `knowledge/composition_dna.csv`
- `knowledge/commercial_dna.csv`

Generated outputs:

- `output/opportunity_ranking.xlsx`
- `output/opportunity_ranking.md`
- `output/summary_report.md`
- `output/knowledge_ranking.xlsx`
- `output/knowledge_summary.md`
- `output/design_briefs.xlsx`
- `output/design_briefs.md`
- `output/creative_directions.xlsx`
- `output/creative_directions.md`
- `output/prompt_variations.xlsx`
- `output/prompt_variations.md`

## Scoring Logic

Opportunity Score is calculated from available 1-10 scoring columns and
normalized to 0-100.

Weights:

- Demand (1-10): +30%
- Competition (1-10): inverse, 25%
- Commercial Value (1-10): +20%
- Evergreen (1-10): +10%
- Repeat Use (1-10): +10%
- AI Saturation (1-10): inverse, 5%

Competition and AI Saturation are inverse signals because lower competition and
lower saturation improve the opportunity.

## Knowledge Layer

The knowledge layer links:

```text
Buyer -> Use Case -> Asset -> Opportunity
```

This layer helps recommend what asset collection to build next, not just which
keyword to score.

## Opportunity Intelligence Engine

Milestone M7 ranks Adobe Stock opportunities before prompt generation and
answers:

```text
What should we create next?
```

The engine uses local seed data only:

- `knowledge/opportunity_database.csv`
- `knowledge/buyer_database.csv`
- `knowledge/use_case_database.csv`
- `knowledge/market_score.csv`

Each ranked opportunity includes:

- Overall Score (0-100)
- Recommended Collection
- Primary Buyer
- Primary Use Case
- Score Breakdown
- Recommendation
- Reasoning

Scoring dimensions:

- Demand
- Competition
- Commercial Value
- Reusability
- Approval Risk
- Revenue Potential
- Seasonality

## Design Brief Generator

The design brief generator converts the highest-ranked Buyer -> Use Case ->
Asset opportunities into production-ready creative briefs.

Design briefs define:

- buyer persona
- use case
- campaign goal
- visual direction
- composition
- lighting
- copy space
- product placement zone
- must-include elements
- avoid list
- production priority

## Scene DNA Variation Framework

Phase 6.1 replaces fixed template prompt generation with a Scene DNA variation
framework. The goal is to create distinct commercial image directions before
writing prompts, reducing near-duplicate risk.

The framework uses:

```text
Asset DNA + Scene DNA + Commercial DNA + Distinct Engine = Creative Direction + Prompt
```

Core modules:

- `src/creative_direction_engine.py`
- `src/distinct_engine.py`
- `src/commercial_prompt_engine.py`

Distinctness scoring rejects creative directions with similarity above 70% using
weighted layers for architecture, spatial layout, lighting, materials, camera,
props/styling, and color/mood.

Prompt rules:

- generate prompts from accepted creative directions
- keep prompts between 140 and 220 words
- do not mention internal scoring or database fields
- preserve the same Buyer and Use Case
- keep Adobe Stock commercial quality
- no image generation and no image APIs

## Phase 3 TODO

- OpenAI API research
- Web search
- Google Sheets sync
- Buyer Database
- Gap Analysis
- Prompt Library generation
