"""Commercial Prompt Engine for Adobe Stock Intelligence.

Phase 6 replaces fixed prompt templates with a modular library system. It
combines scene, material, lighting, camera, composition, and commercial rules
to create prompt variations for each BUY-framework asset brief.

This module does not call image APIs and does not generate images.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


COMMERCIAL_RULES = (
    "Adobe Stock commercial quality, realistic stock photography, no text, no logos, "
    "no brands, no people, no hands, no copyrighted objects, no readable labels, "
    "no trademarked packaging, clean negative space, broadly reusable marketing asset"
)

PROMPT_VARIATION_COLUMNS = [
    "Variation ID",
    "Brief ID",
    "Asset",
    "Industry",
    "Niche",
    "Buyer Persona",
    "Use Case",
    "Scene",
    "Material Set",
    "Lighting",
    "Camera",
    "Composition",
    "Camera + Composition Key",
    "Prompt",
    "Word Count",
    "Commercial Rules",
    "Production Status",
]


@dataclass(frozen=True)
class PromptLibraryPaths:
    """CSV paths required by the commercial prompt engine."""

    scenes: Path
    materials: Path
    lighting: Path
    camera: Path
    composition: Path


def load_prompt_libraries(paths: PromptLibraryPaths) -> dict[str, pd.DataFrame]:
    """Load every modular prompt library CSV."""

    libraries = {
        "scenes": _read_library(paths.scenes, ["scene_id", "scene_name", "scene_description"]),
        "materials": _read_library(paths.materials, ["material_set_id", "material_set_name", "materials"]),
        "lighting": _read_library(paths.lighting, ["lighting_id", "lighting_name", "lighting_description"]),
        "camera": _read_library(paths.camera, ["camera_id", "camera_name", "camera_instruction"]),
        "composition": _read_library(
            paths.composition,
            ["composition_id", "composition_name", "composition_instruction"],
        ),
    }

    if len(libraries["materials"]) < 10:
        raise ValueError("material_library.csv must contain at least 10 material sets.")
    if len(libraries["camera"]) * len(libraries["composition"]) < 10:
        raise ValueError("camera and composition libraries must provide at least 10 unique combinations.")

    return libraries


def generate_prompt_variations(
    asset_briefs: pd.DataFrame,
    libraries: dict[str, pd.DataFrame],
    variations_per_asset: int = 10,
) -> pd.DataFrame:
    """Generate unique commercial prompt variations for each asset brief."""

    if asset_briefs.empty:
        return pd.DataFrame(columns=PROMPT_VARIATION_COLUMNS)

    required = ["Brief ID", "Asset", "Industry", "Niche", "Buyer Persona", "Use Case"]
    missing = [column for column in required if column not in asset_briefs.columns]
    if missing:
        raise ValueError(f"Asset briefs are missing required columns: {missing}")

    rows: list[dict[str, object]] = []
    variation_index = 1

    for _, brief in asset_briefs.iterrows():
        used_material_sets: set[str] = set()
        used_camera_compositions: set[str] = set()

        for variation_number in range(variations_per_asset):
            scene = _select_library_row(libraries["scenes"], variation_number, brief, "scene_name")
            material = _next_unique_row(
                libraries["materials"],
                variation_number,
                used_material_sets,
                "material_set_id",
            )
            lighting = _select_library_row(libraries["lighting"], variation_number, brief, "lighting_name")
            camera, composition = _next_unique_camera_composition(
                libraries["camera"],
                libraries["composition"],
                variation_number,
                used_camera_compositions,
            )

            prompt = _build_prompt(brief, scene, material, lighting, camera, composition)
            word_count = _word_count(prompt)
            if not 140 <= word_count <= 220:
                raise ValueError(
                    f"Prompt word count out of range for {brief.get('Asset')} variation "
                    f"{variation_number + 1}: {word_count} words"
                )

            camera_composition_key = (
                f"{_clean(camera['camera_id'])}+{_clean(composition['composition_id'])}"
            )

            rows.append(
                {
                    "Variation ID": f"CP{variation_index:04d}",
                    "Brief ID": _clean(brief.get("Brief ID")),
                    "Asset": _clean(brief.get("Asset")),
                    "Industry": _clean(brief.get("Industry")),
                    "Niche": _clean(brief.get("Niche")),
                    "Buyer Persona": _clean(brief.get("Buyer Persona")),
                    "Use Case": _clean(brief.get("Use Case")),
                    "Scene": _clean(scene["scene_name"]),
                    "Material Set": _clean(material["material_set_name"]),
                    "Lighting": _clean(lighting["lighting_name"]),
                    "Camera": _clean(camera["camera_name"]),
                    "Composition": _clean(composition["composition_name"]),
                    "Camera + Composition Key": camera_composition_key,
                    "Prompt": prompt,
                    "Word Count": word_count,
                    "Commercial Rules": COMMERCIAL_RULES,
                    "Production Status": "Ready for manual prompt test",
                }
            )
            variation_index += 1

    return pd.DataFrame(rows, columns=PROMPT_VARIATION_COLUMNS)


def write_prompt_variation_outputs(
    prompt_variations: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Write prompt variations to Excel and Markdown."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        prompt_variations.to_excel(writer, sheet_name="Prompt Variations", index=False)

    output_report.write_text(build_prompt_variation_report(prompt_variations), encoding="utf-8")


def build_prompt_variation_report(prompt_variations: pd.DataFrame) -> str:
    """Create a readable Markdown report for commercial prompt variations."""

    lines = [
        "# Commercial Prompt Engine Output",
        "",
        "Phase 6 generates modular prompt variations from scene, material, lighting, camera, and composition libraries.",
        "This phase does not generate images or call image APIs.",
        "",
    ]

    if prompt_variations.empty:
        lines.append("No prompt variations were generated.")
        return "\n".join(lines) + "\n"

    grouped = prompt_variations.groupby(["Brief ID", "Asset", "Buyer Persona", "Use Case"], sort=False)
    for (brief_id, asset, buyer, use_case), group in grouped:
        lines.extend(
            [
                f"## {brief_id} - {asset}",
                "",
                f"- **Buyer:** {buyer}",
                f"- **Use Case:** {use_case}",
                f"- **Variations:** {len(group)}",
                "",
            ]
        )

        for _, row in group.iterrows():
            lines.extend(
                [
                    f"### {row['Variation ID']} - {row['Scene']} / {row['Material Set']}",
                    "",
                    f"- **Lighting:** {row['Lighting']}",
                    f"- **Camera:** {row['Camera']}",
                    f"- **Composition:** {row['Composition']}",
                    f"- **Word Count:** {row['Word Count']}",
                    "",
                    row["Prompt"],
                    "",
                ]
            )

    return "\n".join(lines) + "\n"


def _build_prompt(
    brief: pd.Series,
    scene: pd.Series,
    material: pd.Series,
    lighting: pd.Series,
    camera: pd.Series,
    composition: pd.Series,
) -> str:
    asset = _clean(brief.get("Asset"))
    industry = _clean(brief.get("Industry"))
    niche = _clean(brief.get("Niche"))
    buyer = _clean(brief.get("Buyer Persona"))
    use_case = _clean(brief.get("Use Case"))
    visual_direction = _clean(brief.get("Visual Direction"))
    copy_space = _clean(brief.get("Copy Space"))
    placement = _clean(brief.get("Product Placement Zone"))
    must_include = _clean(brief.get("Must Include"))

    return (
        f"Ultra realistic commercial stock photography prompt for a {asset} in the {industry} industry, "
        f"built for {buyer} using the image for {use_case}. "
        f"Scene: {_clean(scene['scene_description'])}. Materials: {_clean(material['materials'])}, chosen for "
        f"{_clean(material['commercial_effect'])}. Lighting: {_clean(lighting['lighting_description'])}. "
        f"Camera: {_clean(camera['camera_instruction'])}. Composition: {_clean(composition['composition_instruction'])}. "
        f"Visual direction: {visual_direction}. Keep {copy_space.lower()} Reserve {placement.lower()} "
        f"Must include {must_include.lower()} Tie the image to {niche} while keeping it reusable for websites, "
        "sales decks, ecommerce banners, and campaign layouts. Use accurate shadows, believable scale, "
        "clean geometry, refined color, and premium marketing finish. "
        f"Commercial rules: Adobe Stock commercial quality, no text, logos, brands, people, hands, copyrighted objects, "
        "readable labels, trademarked packaging, clutter, or obvious AI artifacts."
    )


def _read_library(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Prompt library not found: {path}")

    dataframe = pd.read_csv(path).fillna("")
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    if dataframe.empty:
        raise ValueError(f"{path.name} must contain at least one row.")
    return dataframe


def _select_library_row(
    dataframe: pd.DataFrame,
    variation_number: int,
    brief: pd.Series,
    name_column: str,
) -> pd.Series:
    """Deterministically rotate through the most relevant library selections."""

    ranked = _rank_library_for_brief(dataframe, brief)
    pool_limit = 2 if name_column in {"scene_name", "lighting_name"} else 4
    pool_size = min(pool_limit, len(ranked))
    seed = len(_clean(brief.get("Asset"))) + len(_clean(brief.get("Buyer Persona"))) + len(name_column)
    return ranked.iloc[(variation_number + seed) % pool_size]


def _rank_library_for_brief(dataframe: pd.DataFrame, brief: pd.Series) -> pd.DataFrame:
    brief_text = " ".join(
        [
            _clean(brief.get("Asset")),
            _clean(brief.get("Industry")),
            _clean(brief.get("Niche")),
            _clean(brief.get("Buyer Persona")),
            _clean(brief.get("Use Case")),
        ]
    ).lower()
    tokens = {
        token
        for token in brief_text.replace("/", " ").replace("-", " ").split()
        if len(token) > 3
    }

    ranked = dataframe.copy()
    scores = []
    for _, row in ranked.iterrows():
        row_text = " ".join(_clean(value).lower() for value in row.values)
        scores.append(sum(1 for token in tokens if token in row_text))
    ranked["_match_score"] = scores
    return ranked.sort_values(by="_match_score", ascending=False, kind="mergesort").drop(
        columns=["_match_score"]
    )


def _next_unique_row(
    dataframe: pd.DataFrame,
    variation_number: int,
    used_keys: set[str],
    key_column: str,
) -> pd.Series:
    for offset in range(len(dataframe)):
        row = dataframe.iloc[(variation_number + offset) % len(dataframe)]
        key = _clean(row[key_column])
        if key not in used_keys:
            used_keys.add(key)
            return row
    raise ValueError(f"Could not find a unique {key_column} value.")


def _next_unique_camera_composition(
    camera_library: pd.DataFrame,
    composition_library: pd.DataFrame,
    variation_number: int,
    used_keys: set[str],
) -> tuple[pd.Series, pd.Series]:
    total_combinations = len(camera_library) * len(composition_library)
    for offset in range(total_combinations):
        index = variation_number + offset
        camera = camera_library.iloc[index % len(camera_library)]
        composition = composition_library.iloc[
            (index // len(camera_library) + index) % len(composition_library)
        ]
        key = f"{_clean(camera['camera_id'])}+{_clean(composition['composition_id'])}"
        if key not in used_keys:
            used_keys.add(key)
            return camera, composition
    raise ValueError("Could not find a unique camera + composition combination.")


def _word_count(prompt: str) -> int:
    return len(prompt.split())


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
