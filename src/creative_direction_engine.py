"""Scene DNA creative direction generation.

This module converts Asset DNA, Scene DNA, Commercial DNA, and supporting
visual DNA libraries into structured creative directions before prompt writing.
It does not generate images, call image APIs, perform web research, or sync to
Google Sheets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from distinct_engine import highest_similarity, is_distinct


CREATIVE_DIRECTION_COLUMNS = [
    "Creative Direction ID",
    "Version",
    "asset",
    "buyer",
    "use_case",
    "commercial_objective",
    "scene",
    "architecture",
    "layout",
    "materials",
    "lighting",
    "camera",
    "composition",
    "copy_space",
    "negative_constraints",
    "spatial_layout",
    "props_styling",
    "color_mood",
    "product_zone",
    "output_format",
    "similarity_to_previous",
    "status",
]


@dataclass(frozen=True)
class DNAPaths:
    asset_dna: Path
    scene_dna: Path
    material_dna: Path
    lighting_dna: Path
    camera_dna: Path
    composition_dna: Path
    commercial_dna: Path


def load_dna_libraries(paths: DNAPaths) -> dict[str, pd.DataFrame]:
    """Load and validate all Phase 6.1 DNA CSV files."""

    return {
        "asset": _read_csv(
            paths.asset_dna,
            [
                "asset_id",
                "asset_name",
                "industry",
                "buyer_persona",
                "use_case",
                "commercial_objective",
                "required_product_zone",
                "required_copy_space",
                "avoid",
            ],
        ),
        "scene": _read_csv(
            paths.scene_dna,
            [
                "scene_id",
                "scene_name",
                "architecture_style",
                "spatial_layout",
                "mood",
                "best_industries",
                "avoid_with",
            ],
        ),
        "material": _read_csv(
            paths.material_dna,
            [
                "material_id",
                "material_set_name",
                "primary_materials",
                "finish",
                "mood",
                "best_industries",
                "avoid_with",
            ],
        ),
        "lighting": _read_csv(
            paths.lighting_dna,
            ["lighting_id", "lighting_name", "contrast", "mood", "best_use_case", "avoid_with"],
        ),
        "camera": _read_csv(
            paths.camera_dna,
            ["camera_id", "camera_name", "focal_length", "angle", "best_use_case", "copy_space_support"],
        ),
        "composition": _read_csv(
            paths.composition_dna,
            [
                "composition_id",
                "composition_name",
                "product_zone",
                "copy_space_position",
                "copy_space_percentage",
                "best_use_case",
            ],
        ),
        "commercial": _read_csv(
            paths.commercial_dna,
            ["commercial_id", "objective", "buyer", "use_case", "output_format", "required_rules"],
        ),
    }


def generate_creative_directions(
    dna: dict[str, pd.DataFrame],
    variations_per_asset: int = 10,
) -> pd.DataFrame:
    """Generate distinct creative directions from DNA libraries."""

    rows: list[dict[str, object]] = []
    direction_index = 1

    assets = _prioritize_assets(dna["asset"])
    for _, asset in assets.iterrows():
        accepted_for_asset: list[dict[str, object]] = []
        candidates = _build_candidate_pool(asset, dna)

        for candidate in candidates:
            if not is_distinct(candidate, accepted_for_asset):
                continue

            candidate["similarity_to_previous"] = highest_similarity(candidate, accepted_for_asset)
            candidate["Creative Direction ID"] = f"CDIR{direction_index:04d}"
            candidate["Version"] = _version_label(len(accepted_for_asset), candidate["scene"])
            candidate["status"] = "Accepted"
            rows.append(candidate)
            accepted_for_asset.append(candidate)
            direction_index += 1

            if len(accepted_for_asset) >= variations_per_asset:
                break

        if len(accepted_for_asset) < variations_per_asset:
            raise ValueError(
                f"Could not create {variations_per_asset} distinct directions for "
                f"{_clean(asset['asset_name'])}."
            )

    return pd.DataFrame(rows, columns=CREATIVE_DIRECTION_COLUMNS)


def write_creative_direction_outputs(
    creative_directions: pd.DataFrame,
    output_workbook: Path,
    output_report: Path,
) -> None:
    """Export creative directions to Excel and Markdown."""

    output_workbook.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_workbook, engine="openpyxl") as writer:
        creative_directions.to_excel(writer, sheet_name="Creative Directions", index=False)

    output_report.write_text(build_creative_direction_report(creative_directions), encoding="utf-8")


def build_creative_direction_report(creative_directions: pd.DataFrame) -> str:
    lines = [
        "# Scene DNA Creative Directions",
        "",
        "Creative directions are generated from Asset DNA, Scene DNA, Commercial DNA, and distinctness checks.",
        "This phase does not generate images, use image APIs, add Google Sheets integration, or perform web research.",
        "",
    ]

    if creative_directions.empty:
        lines.append("No creative directions were generated.")
        return "\n".join(lines) + "\n"

    grouped = creative_directions.groupby(["asset", "buyer", "use_case"], sort=False)
    for (asset, buyer, use_case), group in grouped:
        lines.extend(
            [
                f"## {asset}",
                "",
                f"- **Buyer:** {buyer}",
                f"- **Use Case:** {use_case}",
                f"- **Creative Directions:** {len(group)}",
                "",
            ]
        )

        for _, row in group.iterrows():
            lines.extend(
                [
                    f"### {row['Version']}",
                    "",
                    f"- **Objective:** {row['commercial_objective']}",
                    f"- **Scene:** {row['scene']}",
                    f"- **Architecture:** {row['architecture']}",
                    f"- **Layout:** {row['layout']}",
                    f"- **Materials:** {row['materials']}",
                    f"- **Lighting:** {row['lighting']}",
                    f"- **Camera:** {row['camera']}",
                    f"- **Composition:** {row['composition']}",
                    f"- **Copy Space:** {row['copy_space']}",
                    f"- **Negative Constraints:** {row['negative_constraints']}",
                    f"- **Similarity To Previous:** {row['similarity_to_previous']}",
                    "",
                ]
            )

    return "\n".join(lines) + "\n"


def _build_candidate_pool(asset: pd.Series, dna: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    scenes = _filter_industry(dna["scene"], asset["industry"], "best_industries")
    materials = _filter_industry(dna["material"], asset["industry"], "best_industries")
    lighting = _rank_by_use_case(dna["lighting"], asset["use_case"], "best_use_case")
    cameras = _rank_by_use_case(dna["camera"], asset["use_case"], "best_use_case")
    compositions = _rank_by_use_case(dna["composition"], asset["use_case"], "best_use_case")
    commercial = _select_commercial(dna["commercial"], asset)

    candidates = []
    for scene_index, scene in scenes.iterrows():
        material = materials.iloc[scene_index % len(materials)]
        light = lighting.iloc[scene_index % len(lighting)]
        camera = cameras.iloc[scene_index % len(cameras)]
        composition = compositions.iloc[scene_index % len(compositions)]
        candidates.append(
            _build_direction(
                asset=asset,
                scene=scene,
                material=material,
                lighting=light,
                camera=camera,
                composition=composition,
                commercial=commercial,
            )
        )

    return candidates


def _build_direction(
    *,
    asset: pd.Series,
    scene: pd.Series,
    material: pd.Series,
    lighting: pd.Series,
    camera: pd.Series,
    composition: pd.Series,
    commercial: pd.Series,
) -> dict[str, object]:
    material_summary = (
        f"{_clean(material['material_set_name'])}: {_clean(material['primary_materials'])}; "
        f"finish: {_clean(material['finish'])}"
    )
    lighting_summary = (
        f"{_clean(lighting['lighting_name'])}: {_clean(lighting['contrast'])}, "
        f"{_clean(lighting['mood'])}"
    )
    camera_summary = (
        f"{_clean(camera['camera_name'])}: {_clean(camera['focal_length'])}, "
        f"{_clean(camera['angle'])}"
    )
    composition_summary = (
        f"{_clean(composition['composition_name'])}: product zone {_clean(composition['product_zone'])}, "
        f"copy space {_clean(composition['copy_space_position'])} "
        f"({_clean(composition['copy_space_percentage'])}%)"
    )

    return {
        "asset": _clean(asset["asset_name"]),
        "buyer": _clean(asset["buyer_persona"]),
        "use_case": _clean(asset["use_case"]),
        "commercial_objective": _clean(asset["commercial_objective"]),
        "scene": _clean(scene["scene_name"]),
        "architecture": _clean(scene["architecture_style"]),
        "layout": _clean(scene["spatial_layout"]),
        "materials": material_summary,
        "lighting": lighting_summary,
        "camera": camera_summary,
        "composition": composition_summary,
        "copy_space": (
            f"{_clean(asset['required_copy_space'])}; "
            f"{_clean(camera['copy_space_support'])}"
        ),
        "negative_constraints": (
            f"{_clean(asset['avoid'])}; {_clean(commercial['required_rules'])}"
        ),
        "spatial_layout": _clean(scene["spatial_layout"]),
        "props_styling": _clean(composition["product_zone"]),
        "color_mood": f"{_clean(scene['mood'])}; {_clean(material['mood'])}",
        "product_zone": _clean(asset["required_product_zone"]),
        "output_format": _clean(commercial["output_format"]),
    }


def _read_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"DNA file not found: {path}")

    dataframe = pd.read_csv(path).fillna("")
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    if len(dataframe) < 10:
        raise ValueError(f"{path.name} must include at least 10 rows.")
    return dataframe


def _prioritize_assets(assets: pd.DataFrame) -> pd.DataFrame:
    priority = (
        (assets["asset_name"] == "Pharmacy Product Display")
        & (assets["buyer_persona"] == "Pharmaceutical Brand Manager")
        & (assets["use_case"] == "Packaging Presentation")
    )
    return (
        assets.assign(_priority=priority.astype(int))
        .sort_values(by="_priority", ascending=False, kind="mergesort")
        .drop(columns=["_priority"])
        .reset_index(drop=True)
    )


def _filter_industry(dataframe: pd.DataFrame, industry: str, column: str) -> pd.DataFrame:
    industry_text = _clean(industry).lower()
    filtered = dataframe[dataframe[column].str.lower().str.contains(industry_text, regex=False)]
    if filtered.empty:
        return dataframe.reset_index(drop=True)
    return filtered.reset_index(drop=True)


def _rank_by_use_case(dataframe: pd.DataFrame, use_case: str, column: str) -> pd.DataFrame:
    use_case_text = _clean(use_case).lower()
    ranked = dataframe.copy()
    ranked["_match"] = ranked[column].str.lower().eq(use_case_text).astype(int)
    return ranked.sort_values(by="_match", ascending=False, kind="mergesort").drop(
        columns=["_match"]
    ).reset_index(drop=True)


def _select_commercial(commercial: pd.DataFrame, asset: pd.Series) -> pd.Series:
    buyer = _clean(asset["buyer_persona"]).lower()
    use_case = _clean(asset["use_case"]).lower()
    exact = commercial[
        (commercial["buyer"].str.lower() == buyer)
        & (commercial["use_case"].str.lower() == use_case)
    ]
    if not exact.empty:
        return exact.iloc[0]

    by_use_case = commercial[commercial["use_case"].str.lower() == use_case]
    if not by_use_case.empty:
        return by_use_case.iloc[0]

    return commercial.iloc[0]


def _version_label(index: int, scene_name: str) -> str:
    letter = chr(ord("A") + index)
    return f"Version {letter} — {scene_name}"


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
