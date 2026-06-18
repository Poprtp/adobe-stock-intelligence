# Tasks for Codex

## Completed

- Phase 1: Excel scoring pipeline
- Phase 2: Correct weighted scoring model and mock research agent
- Phase 3: Knowledge Layer foundation
  - buyers.csv
  - use_cases.csv
  - assets.csv
  - opportunities.csv
  - knowledge_engine.py
  - knowledge_ranking.xlsx
  - knowledge_summary.md

## Current Goal

Turn the project from a keyword scorer into a commercial decision engine.

Core logic:

```text
Buyer → Use Case → Asset → Opportunity → Prompt → Image
```

## Next Phase 4 Tasks

1. Expand knowledge CSVs:
   - 100 buyer personas
   - 200 use cases
   - 300 commercial visual assets
   - 500 opportunity links

2. Add design brief generation:
   - Input: top-ranked asset opportunity
   - Output: buyer, goal, use cases, visual direction, copy space, aspect ratios, prompt notes

3. Add prompt library generation:
   - Only for opportunities with Investment Decision = Invest or Test
   - Do not call image APIs

4. Add Google Sheets sync:
   - Read and write to Google Sheets
   - Keep Excel output as local backup

5. Add OpenAI research mode:
   - Research Agent should replace mock results with real structured analysis
   - Add optional web research

## Hard Rules

- Do not generate images.
- Do not use image APIs.
- Do not create prompts for opportunities without clear Buyer and Use Case.
- All future prompts must be based on the BUY Framework.

## Phase 4 completed

Implemented Design Brief Generator:

- `src/design_brief_generator.py`
- `output/design_briefs.xlsx`
- `output/design_briefs.md`

## Phase 5 next

Build Prompt Strategy Generator:

1. Read `output/design_briefs.xlsx`
2. Convert each design brief into 2 prompt versions:
   - 16:9 website / presentation hero
   - 4:5 social / product marketing layout
3. Include Adobe Stock safety rules:
   - no text
   - no logos
   - no brands
   - no people
   - no hands
   - no copyrighted objects
4. Save outputs to:
   - `output/prompt_library.xlsx`
   - `output/prompt_library.md`
5. Do not generate images yet.

## Phase 5 completed

Implemented Prompt Strategy Generator:

- `src/prompt_strategy_generator.py`
- `output/prompt_library.xlsx`
- `output/prompt_library.md`

The prompt generator creates two prompt strategies per design brief:

1. 16:9 website / presentation hero
2. 4:5 social / product marketing layout

Hard rule remains: no image APIs and no image generation.

## Phase 6 next

Build Metadata Generator:

1. Read `output/prompt_library.xlsx`
2. Generate Adobe Stock metadata:
   - title under 70 characters
   - description under 200 characters
   - 30-49 single-word keywords
   - category suggestion
3. Save outputs to:
   - `output/metadata_library.xlsx`
   - `output/metadata_library.md`
4. Do not generate images yet.
