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

    st.markdown('<div class="studio-topbar">Adobe Stock Studio</div>', unsafe_allow_html=True)
    rooms = st.tabs(
        [
            "CEO Office",
            "Strategy Room",
            "Art Department",
            "Production Studio",
            "QA Room",
            "Upload Center",
            "Portfolio Room",
        ]
    )

    with rooms[0]:
        ceo_office(opportunities, prompt_sections, status)
    with rooms[1]:
        strategy_room(opportunities)
    with rooms[2]:
        art_department(creative_directions)
    with rooms[3]:
        production_studio(prompt_sections, status)
    with rooms[4]:
        qa_room()
    with rooms[5]:
        upload_center(opportunities)
    with rooms[6]:
        portfolio_room()


def ceo_office(opportunities: pd.DataFrame, prompts: list[dict[str, str]], status: pd.DataFrame) -> None:
    header("CEO Office", "Daily focus for the next production move.")
    top = first_row(opportunities)
    completed = sum(1 for prompt in prompts if status_for(status, prompt["key"]) != "Todo")

    character_card(
        "Studio CEO",
        "Daily operator",
        f"Create the {value(top, 'Asset')} collection next." if top is not None else "Refresh studio data.",
        "Resume production from the first unfinished prompt.",
    )

    st.markdown("### Today's Focus")
    if top is None:
        st.warning("Run `python src/main.py` to generate opportunity intelligence.")
    else:
        focus_cols = st.columns([2, 1, 1])
        with focus_cols[0]:
            card(
                f"**Current Collection**\n\n"
                f"{value(top, 'Asset')}\n\n"
                f"{value(top, 'Recommended Collection')}"
            )
        with focus_cols[1]:
            st.metric("Top Score", int(value(top, "Overall Score", 0)))
        with focus_cols[2]:
            st.metric("Progress", f"{completed}/{len(prompts)}")

        st.markdown("### Progress")
        progress_value = completed / len(prompts) if prompts else 0
        st.progress(progress_value, text=f"{completed} / {len(prompts)} completed")

    st.markdown("### Next Action")
    card("Open Production Studio. Generate the first unfinished prompt, then mark it Generated.")
    st.button("Resume production")


def strategy_room(opportunities: pd.DataFrame) -> None:
    header("Strategy Room", "Decide what the studio should create next.")
    top = first_row(opportunities)
    character_card(
        "Strategy Director",
        "Opportunity strategist",
        f"{value(top, 'Opportunity')} should be created next because it has the strongest score and buyer fit."
        if top is not None
        else "Waiting for opportunity ranking data.",
        "Review the top opportunity and keep production aligned with buyer demand.",
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
        "Use distinct pharmacy scenes while preserving packaging presentation utility.",
        "Check scene structure, materials, lighting, camera, and copy space.",
    )

    st.subheader("Current Collection")
    st.write("**Pharmacy Product Display**")

    if current.empty:
        st.warning("Run `python src/main.py` to generate creative directions.")
        return

    selected_version = st.selectbox("Creative direction", current["Version"].tolist())
    row = current[current["Version"] == selected_version].iloc[0]

    left, right = st.columns([3, 1])
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
    header("Production Studio", "Prompt-first workspace for daily image generation.")
    character_card(
        "Production Assistant",
        "Prompt operator",
        "Start with Image 01, then work through the collection in order.",
        "Copy the prompt, generate the image manually, then update its status.",
    )

    if not prompts:
        st.warning("Run `python src/main.py` to generate production prompts.")
        return

    completed = sum(1 for prompt in prompts if status_for(status, prompt["key"]) != "Todo")
    st.markdown("### Collection Progress")
    st.caption(f"{completed} / {len(prompts)} completed")
    st.progress(completed / len(prompts), text="")

    if "production_index" not in st.session_state:
        st.session_state.production_index = 0

    list_col, prompt_col, action_col = st.columns([1.05, 3.2, 1.2])
    with list_col:
        st.subheader("Image List")
        selected_title = st.radio(
            "Select prompt",
            [prompt["title"] for prompt in prompts],
            index=min(st.session_state.production_index, len(prompts) - 1),
            label_visibility="collapsed",
        )
        st.session_state.production_index = [prompt["title"] for prompt in prompts].index(selected_title)

    selected = prompts[st.session_state.production_index]

    with prompt_col:
        st.subheader("Prompt Workspace")
        st.caption(selected["title"])
        st.text_area("Ready-to-copy prompt", selected["prompt"], height=460, key="production_prompt_area")

    with action_col:
        st.subheader("Actions / Notes")
        current_status = status_for(status, selected["key"])
        st.caption(f"Status: {current_status}")
        if st.button("Copy Prompt", use_container_width=True):
            st.info("Prompt is ready in the workspace. Select the text area and copy.")
        if st.button("Mark Generated", use_container_width=True):
            save_status(status, selected, "Generated")
            st.success("Marked Generated.")
        if st.button("Mark Selected", use_container_width=True):
            save_status(status, selected, "Selected")
            st.success("Marked Selected.")
        if st.button("Next Image", use_container_width=True):
            st.session_state.production_index = min(st.session_state.production_index + 1, len(prompts) - 1)
            st.rerun()
        st.divider()
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(current_status),
        )
        if st.button("Save Status", use_container_width=True):
            save_status(status, selected, new_status)
            st.success("Status saved.")
        st.markdown(f"**Intended Use**\n\n{selected['intended_use']}")
        st.markdown(f"**Notes**\n\n{selected['notes']}")


def qa_room() -> None:
    header("QA Room", "Score generated images before selecting or uploading.")
    character_card(
        "Quality Inspector",
        "Image evaluator",
        "Score each generated candidate before moving it to Selected.",
        "Review generated candidates with the editable audit table.",
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
        "Metadata generation is a placeholder until the next milestone.",
        "Prepare title, description, keywords, and file readiness checks.",
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
        "Portfolio metrics are placeholders until tracking data exists.",
        "Review placeholder portfolio health and future tracking needs.",
    )

    cols = st.columns(6)
    cols[0].metric("Total images", 0)
    cols[1].metric("Approved", 0)
    cols[2].metric("Rejected", 0)
    cols[3].metric("Downloads", 0)
    cols[4].metric("Revenue", "$0")
    cols[5].metric("Best category", "Healthcare")

    card("Portfolio tracking will be connected in a future milestone.")


def header(room_name: str, caption: str) -> None:
    st.title(room_name)
    st.caption(caption)


def character_card(name: str, role: str, recommendation: str, current_task: str) -> None:
    st.markdown(
        f"""
        <div class="studio-card character-card">
          <div class="character-name">{name}</div>
          <div class="character-role">{role}</div>
          <div class="character-grid">
            <div>
              <span class="card-label">Next recommendation</span>
              <p>{recommendation}</p>
            </div>
            <div>
              <span class="card-label">Current task</span>
              <p>{current_task}</p>
            </div>
          </div>
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
        :root {
            --studio-bg: #0f0f10;
            --studio-surface: #171717;
            --studio-surface-2: #1f1f1f;
            --studio-border: #303030;
            --studio-text: #f2f2f2;
            --studio-muted: #a3a3a3;
            --studio-subtle: #737373;
            --studio-radius: 16px;
        }
        .stApp {
            background: var(--studio-bg);
            color: var(--studio-text);
            font-family: Inter, Geist, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .block-container {
            max-width: 1520px;
            padding-top: 28px;
            padding-left: 40px;
            padding-right: 40px;
        }
        [data-testid="stSidebar"] {
            display: none;
        }
        h1, h2, h3 {
            color: var(--studio-text);
            letter-spacing: 0;
        }
        h1 {
            margin-top: 24px;
            margin-bottom: 8px;
        }
        h2, h3 {
            margin-top: 32px;
        }
        .studio-topbar {
            border-bottom: 1px solid var(--studio-border);
            padding: 18px 0 22px 0;
            margin-bottom: 28px;
            color: var(--studio-text);
            font-size: 0.95rem;
            font-weight: 600;
            letter-spacing: 0;
        }
        .studio-card {
            background: var(--studio-surface);
            border: 1px solid var(--studio-border);
            border-radius: var(--studio-radius);
            padding: 20px;
            margin: 18px 0;
            color: var(--studio-text);
        }
        .character-card {
            border-left: 1px solid var(--studio-border);
        }
        .character-name {
            font-size: 1.15rem;
            font-weight: 700;
        }
        .character-role {
            color: var(--studio-muted);
            font-weight: 600;
            margin-bottom: 8px;
        }
        .character-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            margin-top: 12px;
        }
        .card-label {
            color: var(--studio-subtle);
            font-size: 0.78rem;
            text-transform: uppercase;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid var(--studio-border);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: var(--studio-muted);
            border-radius: 0;
            padding: 12px 14px;
        }
        .stTabs [aria-selected="true"] {
            color: var(--studio-text);
            border-bottom: 1px solid var(--studio-text);
        }
        div[data-testid="stMetric"] {
            background: var(--studio-surface);
            border: 1px solid var(--studio-border);
            border-radius: var(--studio-radius);
            padding: 16px;
        }
        .stButton button {
            background: var(--studio-surface-2);
            border: 1px solid var(--studio-border);
            color: var(--studio-text);
            border-radius: 8px;
        }
        .stProgress > div > div > div > div {
            background-color: var(--studio-muted);
        }
        textarea, input {
            background: var(--studio-surface) !important;
            color: var(--studio-text) !important;
            border-color: var(--studio-border) !important;
        }
        textarea {
            font-family: "JetBrains Mono", "Cascadia Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important;
            line-height: 1.55 !important;
            font-size: 0.92rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
