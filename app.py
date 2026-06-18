"""Local Streamlit MVP for Adobe Stock production workflow."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
INTERNAL_OUTPUT = ROOT / "internal_output"
PRODUCTION_PROMPTS = ROOT / "production" / "02_Production_Prompts"
STATUS_CSV = ROOT / "production" / "prompt_status.csv"


st.set_page_config(page_title="Adobe Stock Intelligence", layout="wide")


def main() -> None:
    st.title("Adobe Stock Intelligence")
    st.caption("Production workspace for deciding, generating, selecting, and preparing Adobe Stock assets.")

    opportunities = load_table(INTERNAL_OUTPUT / "opportunity_ranking.xlsx")
    prompt_status = load_status()
    production_files = sorted(PRODUCTION_PROMPTS.glob("*/*.md"))

    screen = st.sidebar.radio(
        "Workspace",
        ["Dashboard", "Production Room", "Office Characters", "Audit Room"],
    )

    if screen == "Dashboard":
        dashboard(opportunities, production_files)
    elif screen == "Production Room":
        production_room(production_files, prompt_status)
    elif screen == "Office Characters":
        office_characters(opportunities, production_files)
    else:
        audit_room()


def dashboard(opportunities: pd.DataFrame, production_files: list[Path]) -> None:
    st.header("Dashboard")
    if opportunities.empty:
        st.warning("Run `python src/main.py` to generate opportunity ranking data.")
        return

    top = opportunities.iloc[0]
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Top Opportunities")
        st.dataframe(
            opportunities[
                [
                    "Rank",
                    "Opportunity",
                    "Primary Buyer",
                    "Primary Use Case",
                    "Overall Score",
                    "Recommendation",
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.subheader("Recommended Next Collection")
        st.metric("Overall Score", int(top["Overall Score"]))
        st.write(f"**Collection:** {top['Recommended Collection']}")
        st.write(f"**Buyer:** {top['Primary Buyer']}")
        st.write(f"**Use Case:** {top['Primary Use Case']}")
        st.write(top["Reasoning"])

    st.subheader("Production Prompts")
    if production_files:
        for path in production_files:
            st.write(f"- `{path.relative_to(ROOT)}`")
    else:
        st.info("No production prompt files found yet.")

    office_character_cards(opportunities, production_files)
    audit_placeholder()


def production_room(production_files: list[Path], prompt_status: pd.DataFrame) -> None:
    st.header("Production Room")
    if not production_files:
        st.warning("Run `python src/main.py` to generate production prompt files.")
        return

    selected_path = st.selectbox(
        "Select collection",
        production_files,
        format_func=lambda path: path.stem,
    )
    sections = parse_prompt_file(selected_path)
    st.caption(str(selected_path.relative_to(ROOT)))

    if not sections:
        st.warning("No image prompts found in this collection file.")
        return

    prompt_labels = [section["title"] for section in sections]
    selected_label = st.selectbox("Select image prompt", prompt_labels)
    selected = next(section for section in sections if section["title"] == selected_label)

    st.subheader(selected["title"])
    st.text_area("Copy prompt", selected["prompt"], height=260)
    st.code(selected["prompt"], language="text")
    st.write(f"**Intended Use:** {selected['intended_use']}")
    st.write(f"**Notes:** {selected['notes']}")

    prompt_key = f"{selected_path.stem}:{selected['title']}"
    current_status = status_for(prompt_status, prompt_key)
    new_status = st.selectbox(
        "Prompt status",
        ["Todo", "Generated", "Selected", "Uploaded"],
        index=["Todo", "Generated", "Selected", "Uploaded"].index(current_status),
    )
    if st.button("Save status"):
        save_status(prompt_status, prompt_key, selected_path.stem, selected["title"], new_status)
        st.success("Status saved.")


def office_characters(opportunities: pd.DataFrame, production_files: list[Path]) -> None:
    st.header("Office Characters")
    office_character_cards(opportunities, production_files)


def office_character_cards(opportunities: pd.DataFrame, production_files: list[Path]) -> None:
    top = opportunities.iloc[0] if not opportunities.empty else None
    next_prompt = first_prompt(production_files)

    cols = st.columns(4)
    with cols[0]:
        st.subheader("Strategy Director")
        if top is not None:
            st.write(f"Top opportunity: **{top['Opportunity']}**")
            st.write(top["Reasoning"])
        else:
            st.write("Waiting for opportunity ranking data.")

    with cols[1]:
        st.subheader("Art Director")
        st.write("Quality checklist:")
        st.write("- clear product zone")
        st.write("- strong copy space")
        st.write("- realistic materials")
        st.write("- no logos or readable labels")

    with cols[2]:
        st.subheader("Production Assistant")
        if next_prompt:
            st.write(next_prompt["title"])
            st.text_area("Next prompt", next_prompt["prompt"], height=180, key="assistant_next_prompt")
        else:
            st.write("No prompt queued yet.")

    with cols[3]:
        st.subheader("Metadata Assistant")
        st.write("Placeholder for future titles, descriptions, and keywords.")


def audit_room() -> None:
    st.header("Audit Room")
    audit_placeholder()


def audit_placeholder() -> None:
    st.subheader("Audit Placeholder")
    columns = [
        "image_id",
        "prompt_version",
        "commercial_value",
        "copy_space",
        "composition",
        "realism",
        "adobe_risk",
        "final_score",
        "notes",
    ]
    st.data_editor(pd.DataFrame(columns=columns), use_container_width=True, num_rows="dynamic")


def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_excel(path)


def load_status() -> pd.DataFrame:
    if not STATUS_CSV.exists():
        return pd.DataFrame(columns=["prompt_key", "collection", "prompt_version", "status"])
    status = pd.read_csv(STATUS_CSV).fillna("")
    if "prompt_key" not in status.columns:
        status["prompt_key"] = status["collection"] + ":" + status["version"]
    if "prompt_version" not in status.columns and "version" in status.columns:
        status["prompt_version"] = status["version"]
    return status


def save_status(
    status: pd.DataFrame,
    prompt_key: str,
    collection: str,
    prompt_version: str,
    new_status: str,
) -> None:
    updated = status.copy()
    if "prompt_key" not in updated.columns:
        updated["prompt_key"] = ""
    match = updated["prompt_key"] == prompt_key
    if match.any():
        updated.loc[match, "status"] = new_status
    else:
        updated = pd.concat(
            [
                updated,
                pd.DataFrame(
                    [
                        {
                            "prompt_key": prompt_key,
                            "collection": collection,
                            "prompt_version": prompt_version,
                            "status": new_status,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    STATUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    updated.to_csv(STATUS_CSV, index=False)


def status_for(status: pd.DataFrame, prompt_key: str) -> str:
    if status.empty or "prompt_key" not in status.columns:
        return "Todo"
    matched = status[status["prompt_key"] == prompt_key]
    if matched.empty:
        return "Todo"
    value = str(matched.iloc[0].get("status") or "Todo")
    return value if value in {"Todo", "Generated", "Selected", "Uploaded"} else "Todo"


def parse_prompt_file(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    sections = []
    for block in text.split("\n## Image ")[1:]:
        title_line, _, remainder = block.partition("\n")
        title = f"Image {title_line.strip()}"
        prompt = extract_between(remainder, "### Production Prompt", "### Intended Use")
        intended_use = extract_between(remainder, "### Intended Use", "### Notes")
        notes = extract_between(remainder, "### Notes", "---")
        sections.append(
            {
                "title": title,
                "prompt": prompt.strip(),
                "intended_use": intended_use.strip(),
                "notes": notes.strip(),
            }
        )
    return sections


def first_prompt(production_files: list[Path]) -> dict[str, str] | None:
    if not production_files:
        return None
    sections = parse_prompt_file(production_files[0])
    return sections[0] if sections else None


def extract_between(text: str, start: str, end: str) -> str:
    _, _, after_start = text.partition(start)
    before_end, _, _ = after_start.partition(end)
    return before_end.strip()


if __name__ == "__main__":
    main()
