"""Office-style Streamlit workspace for Adobe Stock production."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
INTERNAL_OUTPUT = ROOT / "internal_output"
PRODUCTION_PROMPTS = ROOT / "production" / "02_Production_Prompts"
CURRENT_COLLECTION = PRODUCTION_PROMPTS / "Healthcare" / "Pharmacy Product Display.md"
STATUS_CSV = ROOT / "production" / "prompt_status.csv"

STATUS_OPTIONS = ["Todo", "Generated", "Selected", "Uploaded"]


st.set_page_config(page_title="Adobe Stock Studio", page_icon="ASI", layout="wide")


def main() -> None:
    apply_studio_style()

    opportunities = load_table(INTERNAL_OUTPUT / "opportunity_ranking.xlsx")
    creative_directions = load_table(INTERNAL_OUTPUT / "creative_directions.xlsx")
    prompt_sections = parse_prompt_file(CURRENT_COLLECTION)
    status = load_status()

    st.sidebar.title("Adobe Stock Studio")
    room = st.sidebar.radio(
        "Rooms",
        [
            "CEO Office",
            "Strategy Room",
            "Art Department",
            "Production Studio",
            "QA Room",
            "Upload Center",
            "Portfolio Room",
        ],
    )

    if room == "CEO Office":
        ceo_office(opportunities, prompt_sections, status)
    elif room == "Strategy Room":
        strategy_room(opportunities)
    elif room == "Art Department":
        art_department(creative_directions)
    elif room == "Production Studio":
        production_studio(prompt_sections, status)
    elif room == "QA Room":
        qa_room()
    elif room == "Upload Center":
        upload_center(opportunities)
    else:
        portfolio_room()


def ceo_office(opportunities: pd.DataFrame, prompts: list[dict[str, str]], status: pd.DataFrame) -> None:
    header("CEO Office", "Daily overview for the next Adobe Stock production decision.")
    top = first_row(opportunities)

    character_card(
        "Studio CEO",
        "Daily operator",
        "Keeps the studio focused on the next highest-value collection.",
        f"Create the {value(top, 'Asset')} collection next." if top is not None else "Run the pipeline to refresh studio data.",
    )

    generated = status_count(status, "Generated")
    selected = status_count(status, "Selected")
    uploaded = status_count(status, "Uploaded")

    cols = st.columns(5)
    cols[0].metric("Top Score", int(value(top, "Overall Score", 0)))
    cols[1].metric("Prompts Ready", len(prompts))
    cols[2].metric("Generated", generated)
    cols[3].metric("Selected", selected)
    cols[4].metric("Upload-ready", uploaded)

    st.markdown("### Recommended Next Collection")
    if top is None:
        st.warning("Run `python src/main.py` to generate opportunity intelligence.")
    else:
        card(
            f"**{value(top, 'Asset')}**\n\n"
            f"Buyer: {value(top, 'Primary Buyer')}\n\n"
            f"Use Case: {value(top, 'Primary Use Case')}\n\n"
            f"Collection: {value(top, 'Recommended Collection')}\n\n"
            f"Why now: {value(top, 'Reasoning')}"
        )

    st.markdown("### Next Action")
    st.success("Open Production Studio and generate Image 01 - Premium Contemporary Pharmacy.")
    st.button("Go make the next image prompt", type="primary")


def strategy_room(opportunities: pd.DataFrame) -> None:
    header("Strategy Room", "Decide what the studio should create next.")
    top = first_row(opportunities)
    character_card(
        "Strategy Director",
        "Opportunity strategist",
        "Ranks commercial opportunities before any production work begins.",
        f"{value(top, 'Opportunity')} should be created next because it has the strongest score and buyer fit."
        if top is not None
        else "Waiting for opportunity ranking data.",
    )

    if opportunities.empty:
        st.warning("Run `python src/main.py` to generate opportunity ranking data.")
        return

    st.subheader("Top 10 Opportunity Ranking")
    st.dataframe(
        opportunities[
            [
                "Rank",
                "Opportunity",
                "Primary Buyer",
                "Primary Use Case",
                "Recommended Collection",
                "Overall Score",
                "Recommendation",
            ]
        ].head(10),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Why This Should Be Created Next")
    card(
        f"Buyer: **{value(top, 'Primary Buyer')}**\n\n"
        f"Use Case: **{value(top, 'Primary Use Case')}**\n\n"
        f"Recommended Collection: **{value(top, 'Recommended Collection')}**\n\n"
        f"Reasoning: {value(top, 'Reasoning')}"
    )


def art_department(creative_directions: pd.DataFrame) -> None:
    header("Art Department", "Translate the collection into visual direction.")
    current = creative_directions[
        creative_directions.get("asset", pd.Series(dtype=str)) == "Pharmacy Product Display"
    ].head(10)
    first = first_row(current)

    character_card(
        "Art Director",
        "Visual quality lead",
        "Protects scene structure, realism, copy space, and commercial quality.",
        "Use distinct pharmacy scenes while preserving packaging presentation utility.",
    )

    st.subheader("Current Collection")
    st.write("**Pharmacy Product Display**")

    if current.empty:
        st.warning("Run `python src/main.py` to generate creative directions.")
        return

    selected_version = st.selectbox("Creative direction", current["Version"].tolist())
    row = current[current["Version"] == selected_version].iloc[0]

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Creative Direction Summary")
        facts = {
            "Scene": value(row, "scene"),
            "Architecture": value(row, "architecture"),
            "Materials": value(row, "materials"),
            "Lighting": value(row, "lighting"),
            "Camera": value(row, "camera"),
            "Copy Space": value(row, "copy_space"),
        }
        for label, content in facts.items():
            st.markdown(f"**{label}:** {content}")
    with right:
        st.subheader("Quality Checklist")
        st.checkbox("Clear product placement zone", value=True)
        st.checkbox("Strong copy space", value=True)
        st.checkbox("Realistic materials and lighting", value=True)
        st.checkbox("No logos or readable labels", value=True)
        st.checkbox("Distinct from other scene versions", value=True)


def production_studio(prompts: list[dict[str, str]], status: pd.DataFrame) -> None:
    header("Production Studio", "Generate the next image prompt one at a time.")
    character_card(
        "Production Assistant",
        "Prompt operator",
        "Queues ready-to-copy prompts and tracks production status.",
        "Start with Image 01, then work through the collection in order.",
    )

    if not prompts:
        st.warning("Run `python src/main.py` to generate production prompts.")
        return

    completed = sum(1 for prompt in prompts if status_for(status, prompt["key"]) != "Todo")
    st.progress(completed / len(prompts), text=f"{completed}/{len(prompts)} completed")

    selected_title = st.selectbox("Select image", [prompt["title"] for prompt in prompts])
    selected = next(prompt for prompt in prompts if prompt["title"] == selected_title)

    left, right = st.columns([2, 1])
    with left:
        st.subheader(selected["title"])
        st.text_area("Ready-to-copy prompt", selected["prompt"], height=300)
        st.code(selected["prompt"], language="text")
    with right:
        current_status = status_for(status, selected["key"])
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(current_status),
        )
        if st.button("Save prompt status", type="primary"):
            save_status(status, selected, new_status)
            st.success("Prompt status saved.")
        st.markdown(f"**Intended Use:** {selected['intended_use']}")
        st.markdown(f"**Notes:** {selected['notes']}")


def qa_room() -> None:
    header("QA Room", "Score generated images before selecting or uploading.")
    character_card(
        "Quality Inspector",
        "Image evaluator",
        "Checks commercial value, copy space, composition, realism, and Adobe risk.",
        "Score each generated candidate before moving it to Selected.",
    )

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
    st.caption("editable audit table placeholder")
    st.data_editor(pd.DataFrame(columns=columns), use_container_width=True, num_rows="dynamic")


def upload_center(opportunities: pd.DataFrame) -> None:
    header("Upload Center", "Prepare metadata and file readiness checks.")
    top = first_row(opportunities)
    character_card(
        "Metadata Assistant",
        "Upload preparation",
        "Prepares titles, descriptions, keywords, and readiness checks.",
        "Metadata generation is a placeholder until the next milestone.",
    )

    st.subheader("Metadata Placeholders")
    st.text_input("Title", value=f"{value(top, 'Asset', 'Production Image')} Commercial Marketing Background")
    st.text_area(
        "Description",
        value=(
            f"Commercial stock image for {value(top, 'Primary Use Case', 'marketing use')}, "
            f"designed for {value(top, 'Primary Buyer', 'commercial buyers')}."
        ),
        height=100,
    )
    st.text_area("Keywords", value="pharmacy, healthcare, product, packaging, marketing, retail, copyspace")

    st.subheader("File Readiness Checklist")
    st.checkbox("Final image selected")
    st.checkbox("No logos or readable text")
    st.checkbox("Commercial value confirmed")
    st.checkbox("Metadata reviewed")
    st.checkbox("Ready for Adobe Stock upload")


def portfolio_room() -> None:
    header("Portfolio Room", "Track portfolio health until real analytics are connected.")
    character_card(
        "Portfolio Manager",
        "Performance tracker",
        "Summarizes approved assets, downloads, revenue, and category performance.",
        "Portfolio metrics are placeholders until tracking data exists.",
    )

    cols = st.columns(6)
    cols[0].metric("Total images", 0)
    cols[1].metric("Approved", 0)
    cols[2].metric("Rejected", 0)
    cols[3].metric("Downloads", 0)
    cols[4].metric("Revenue", "$0")
    cols[5].metric("Best category", "Healthcare")

    st.info("Portfolio tracking will be connected in a future milestone.")


def header(room_name: str, caption: str) -> None:
    st.title(room_name)
    st.caption(caption)


def character_card(name: str, role: str, helps_with: str, recommendation: str) -> None:
    st.markdown(
        f"""
        <div class="studio-card character-card">
          <div class="character-name">{name}</div>
          <div class="character-role">{role}</div>
          <p>{helps_with}</p>
          <strong>Current recommendation</strong>
          <p>{recommendation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(markdown_text: str) -> None:
    st.markdown(f'<div class="studio-card">{markdown_text}</div>', unsafe_allow_html=True)


def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_excel(path)


def load_status() -> pd.DataFrame:
    if not STATUS_CSV.exists():
        return pd.DataFrame(columns=["prompt_key", "collection", "prompt_version", "status"])
    status = pd.read_csv(STATUS_CSV).fillna("")
    if "prompt_key" not in status.columns:
        status["prompt_key"] = status.get("collection", "") + ":" + status.get("version", "")
    return status


def save_status(status: pd.DataFrame, prompt: dict[str, str], new_status: str) -> None:
    updated = status.copy()
    if "prompt_key" not in updated.columns:
        updated["prompt_key"] = ""
    match = updated["prompt_key"] == prompt["key"]
    if match.any():
        updated.loc[match, "status"] = new_status
    else:
        updated = pd.concat(
            [
                updated,
                pd.DataFrame(
                    [
                        {
                            "prompt_key": prompt["key"],
                            "collection": "Pharmacy Product Display",
                            "prompt_version": prompt["title"],
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
    result = str(matched.iloc[0].get("status") or "Todo")
    return result if result in STATUS_OPTIONS else "Todo"


def parse_prompt_file(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    prompts = []
    for block in text.split("\n## Image ")[1:]:
        title_line, _, remainder = block.partition("\n")
        title = f"Image {title_line.strip()}"
        prompt = extract_between(remainder, "### Production Prompt", "### Intended Use")
        intended_use = extract_between(remainder, "### Intended Use", "### Notes")
        notes = extract_between(remainder, "### Notes", "---")
        prompts.append(
            {
                "key": f"Pharmacy Product Display:{title}",
                "title": title,
                "prompt": prompt.strip(),
                "intended_use": intended_use.strip(),
                "notes": notes.strip(),
            }
        )
    return prompts


def extract_between(text: str, start: str, end: str) -> str:
    _, _, after_start = text.partition(start)
    before_end, _, _ = after_start.partition(end)
    return before_end.strip()


def first_row(dataframe: pd.DataFrame) -> pd.Series | None:
    if dataframe.empty:
        return None
    return dataframe.iloc[0]


def value(row: pd.Series | None, column: str, default: object = "") -> object:
    if row is None:
        return default
    result = row.get(column, default)
    if pd.isna(result):
        return default
    return result


def status_count(status: pd.DataFrame, status_name: str) -> int:
    if status.empty or "status" not in status.columns:
        return 0
    return int((status["status"] == status_name).sum())


def apply_studio_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #111316;
            color: #f4f1ea;
        }
        [data-testid="stSidebar"] {
            background: #181b20;
            border-right: 1px solid #2b3038;
        }
        h1, h2, h3 {
            color: #f7f3ea;
        }
        .studio-card {
            background: #1d2229;
            border: 1px solid #303844;
            border-radius: 8px;
            padding: 18px;
            margin: 12px 0;
            color: #f4f1ea;
        }
        .character-card {
            border-left: 4px solid #d6a84f;
        }
        .character-name {
            font-size: 1.15rem;
            font-weight: 700;
        }
        .character-role {
            color: #d6a84f;
            font-weight: 600;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
