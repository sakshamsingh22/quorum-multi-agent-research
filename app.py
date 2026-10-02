"""Quorum: Multi-Agent AI Research Assistant - Streamlit front end.

Run with:  streamlit run app.py
"""

import html
import re
import time
from datetime import datetime

import streamlit as st

from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain

APP_NAME = "Quorum"
APP_TAGLINE = "Multi-Agent AI Research Assistant"

# key, name, initial, what the agent does, who it hands off to
AGENTS = [
    ("search", "Search Agent", "S", "Finds recent, reliable sources on the web.", "passed to the Reader Agent"),
    ("read", "Reader Agent", "R", "Picks the best source and extracts its content.", "passed to the Writer Agent"),
    ("write", "Writer Agent", "W", "Drafts the report from all the research.", "passed to the Critic Agent"),
    ("review", "Critic Agent", "C", "Reviews the draft and gives feedback.", "of review delivered"),
]

EXAMPLE_TOPICS = [
    "Solid-state batteries in electric vehicles",
    "How UPI changed digital payments in India",
    "Progress in quantum error correction",
]

st.set_page_config(page_title=f"{APP_NAME}: {APP_TAGLINE}", page_icon="🔷", layout="wide")


# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');

:root {
  --qr-accent: #5B7FEE;
  --qr-accent-fill: #3D63DD;
  --qr-accent-soft: rgba(91, 127, 238, 0.14);
  --qr-green: #2F9E44;
  --qr-green-soft: rgba(47, 158, 68, 0.14);
  --qr-red: #E03131;
  --qr-red-soft: rgba(224, 49, 49, 0.12);
  --qr-line: rgba(128, 128, 128, 0.24);
  --qr-soft: rgba(128, 128, 128, 0.10);
  --qr-font: 'Instrument Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1060px; padding-top: 2.6rem; padding-bottom: 4rem; }

.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.stTextInput input, .stButton button, .stDownloadButton button,
div[data-testid="stFormSubmitButton"] button, .stTabs button p {
  font-family: var(--qr-font);
}

/* Top bar */
.qr-bar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; padding-bottom: 1.1rem; border-bottom: 1px solid var(--qr-line); margin-bottom: 2.6rem; font-family: var(--qr-font); }
.qr-brand { display: flex; align-items: center; gap: 0.6rem; font-weight: 700; font-size: 1.15rem; letter-spacing: -0.01em; }
.qr-logo { display: grid; grid-template-columns: 9px 9px; gap: 3px; }
.qr-logo i { width: 9px; height: 9px; border-radius: 3px; background: var(--qr-accent-fill); display: block; }
.qr-logo i:nth-child(2) { opacity: 0.75; } .qr-logo i:nth-child(3) { opacity: 0.55; } .qr-logo i:nth-child(4) { opacity: 0.35; }
.qr-tag { font-size: 0.88rem; opacity: 0.65; }

/* Hero */
.qr-hero h1 { font-family: var(--qr-font); font-weight: 700; font-size: clamp(1.8rem, 4.6vw, 2.75rem); letter-spacing: -0.025em; line-height: 1.12; margin: 0 0 0.7rem 0; padding: 0; max-width: 20ch; }
.qr-hero p { font-size: 1.05rem; line-height: 1.6; opacity: 0.72; margin: 0 0 1.6rem 0; max-width: 62ch; }

/* Form */
div[data-testid="stForm"] { border: 1px solid var(--qr-line); border-radius: 14px; padding: 0.9rem; background: var(--qr-soft); }
.stTextInput input { font-size: 1rem; padding: 0.72rem 0.9rem; }
.stTextInput div[data-baseweb="input"] { border-radius: 9px; }
.stTextInput div[data-baseweb="input"]:focus-within { border-color: var(--qr-accent); }
div[data-testid="stFormSubmitButton"] button {
  width: 100%; background: var(--qr-accent-fill); color: #fff; border: 0; border-radius: 9px;
  font-weight: 600; padding: 0.66rem 1rem;
}
div[data-testid="stFormSubmitButton"] button:hover { background: #3557C7; color: #fff; }
div[data-testid="stFormSubmitButton"] button:active { background: #2D4AAD; color: #fff; }
button:focus-visible { outline: 2px solid var(--qr-accent); outline-offset: 2px; }

/* Secondary buttons */
.stButton button, .stDownloadButton button {
  width: 100%; border-radius: 9px; border: 1px solid var(--qr-line); background: transparent;
  font-size: 0.88rem; font-weight: 500;
}
.stButton button:hover, .stDownloadButton button:hover { border-color: var(--qr-accent); color: var(--qr-accent); }
section[data-testid="stSidebar"] .stButton button { justify-content: flex-start; text-align: left; }
.qr-label { font-family: var(--qr-font); font-size: 0.85rem; opacity: 0.6; margin: 0.5rem 0 0.2rem 0; }

/* Agent team */
.qr-team { font-family: var(--qr-font); margin: 2.4rem 0 0.6rem 0; }
.qr-team-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; margin-bottom: 0.6rem; }
.qr-team-head h2 { font-family: var(--qr-font); font-size: 1.1rem; font-weight: 700; letter-spacing: -0.01em; margin: 0; padding: 0; }
.qr-team-head span { font-size: 0.85rem; opacity: 0.65; }
.qr-meter { height: 4px; border-radius: 2px; background: var(--qr-line); overflow: hidden; margin-bottom: 1rem; }
.qr-meter b { display: block; height: 100%; background: var(--qr-accent-fill); border-radius: 2px; transition: width 0.4s ease; }

.qr-agents { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem; }
.qr-agent { position: relative; border: 1px solid var(--qr-line); border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; transition: border-color 0.25s ease, box-shadow 0.25s ease; }
.qr-agent:not(:last-child)::after { content: ""; position: absolute; top: 50%; right: calc(-0.625rem - 4px); width: 7px; height: 7px; border-top: 2px solid var(--qr-line); border-right: 2px solid var(--qr-line); transform: translateY(-50%) rotate(45deg); }
.qr-agent.done:not(:last-child)::after { border-color: var(--qr-green); }
.qr-agent-top { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
.qr-avatar { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; font-weight: 700; font-size: 0.95rem; background: var(--qr-soft); opacity: 0.8; }
.qr-chip { font-size: 0.78rem; font-weight: 500; padding: 0.18rem 0.55rem; border-radius: 999px; background: var(--qr-soft); display: inline-flex; align-items: center; gap: 0.4rem; white-space: nowrap; }
.qr-agent-name { font-weight: 600; font-size: 1rem; margin-top: 0.8rem; }
.qr-agent-role { font-size: 0.88rem; line-height: 1.45; opacity: 0.68; margin-top: 0.2rem; flex: 1; }
.qr-agent-foot { font-size: 0.8rem; opacity: 0.6; border-top: 1px solid var(--qr-line); margin-top: 0.85rem; padding-top: 0.6rem; min-height: 2.6em; }

.qr-agent.running { border-color: var(--qr-accent); box-shadow: 0 0 0 3px var(--qr-accent-soft); }
.qr-agent.running .qr-avatar { background: var(--qr-accent-soft); color: var(--qr-accent); opacity: 1; }
.qr-agent.running .qr-chip { background: var(--qr-accent-soft); color: var(--qr-accent); }
.qr-agent.done .qr-avatar { background: var(--qr-green-soft); color: var(--qr-green); opacity: 1; }
.qr-agent.done .qr-chip { background: var(--qr-green-soft); color: var(--qr-green); }
.qr-agent.done .qr-agent-foot { opacity: 0.85; }
.qr-agent.failed { border-color: var(--qr-red); }
.qr-agent.failed .qr-avatar, .qr-agent.failed .qr-chip { background: var(--qr-red-soft); color: var(--qr-red); opacity: 1; }

.qr-spin { width: 10px; height: 10px; border-radius: 50%; border: 2px solid var(--qr-accent-soft); border-top-color: var(--qr-accent); animation: qr-spin 0.8s linear infinite; }
@keyframes qr-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .qr-spin { animation: none; } .qr-meter b, .qr-agent { transition: none; } }

/* Results */
.qr-result { border-top: 1px solid var(--qr-line); margin-top: 2rem; padding-top: 1.7rem; font-family: var(--qr-font); }
.qr-result h2 { font-family: var(--qr-font); font-weight: 700; font-size: clamp(1.3rem, 3.4vw, 1.7rem); letter-spacing: -0.02em; line-height: 1.25; margin: 0 0 0.25rem 0; padding: 0; }
.qr-result span { font-size: 0.88rem; opacity: 0.62; }
.qr-by { font-family: var(--qr-font); font-size: 0.85rem; opacity: 0.6; margin: 0.4rem 0 1rem 0; }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--qr-accent); }
.stTabs button[aria-selected="true"] p, .stTabs button:hover p { color: var(--qr-accent); }
.stTabs .stMarkdown { max-width: 80ch; }
.stTabs .stMarkdown p, .stTabs .stMarkdown li { line-height: 1.7; }

@media (max-width: 900px) {
  .qr-agents { grid-template-columns: 1fr 1fr; gap: 0.9rem; }
  .qr-agent:not(:last-child)::after { display: none; }
}
@media (max-width: 520px) {
  .block-container { padding: 1.4rem 1rem 3rem 1rem; }
  .qr-bar { margin-bottom: 1.8rem; }
  .qr-agents { grid-template-columns: 1fr; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def to_text(result) -> str:
    """Return plain text whether a chain gives back a string or a message."""
    content = getattr(result, "content", result)
    if isinstance(content, list):
        parts = []
        for block in content:
            parts.append(block.get("text", "") if isinstance(block, dict) else str(block))
        return "\n".join(p for p in parts if p)
    return str(content)


def word_count(text: str) -> int:
    return len(text.split())


@st.cache_resource(show_spinner=False)
def get_search_agent():
    return build_search_agent()


@st.cache_resource(show_spinner=False)
def get_reader_agent():
    return build_reader_agent()


def render_team(slot, status: dict, timings: dict, words: dict) -> None:
    """Draw the four agent cards with their current state."""
    finished = sum(1 for key, *_ in AGENTS if status.get(key) == "done")
    running = next((name for key, name, *_ in AGENTS if status.get(key) == "running"), None)
    if running:
        summary = f"{running} is working, {finished} of {len(AGENTS)} finished"
    elif finished == len(AGENTS):
        summary = "All 4 agents finished"
    elif any(status.get(key) == "failed" for key, *_ in AGENTS):
        summary = "Stopped before finishing"
    else:
        summary = "Ready when you are"

    cards = []
    for key, name, initial, role, handoff in AGENTS:
        state = status.get(key, "waiting")
        if state == "running":
            chip = '<span class="qr-spin"></span>Working'
            foot = "Working on it now"
        elif state == "done":
            chip = f"Done in {timings.get(key, 0):.0f}s"
            foot = f"{words.get(key, 0):,} words {handoff}"
        elif state == "failed":
            chip = "Failed"
            foot = "This agent could not finish"
        else:
            chip = "Waiting"
            foot = "Waiting for its turn"
        cards.append(
            f'<div class="qr-agent {state}">'
            f'<div class="qr-agent-top"><div class="qr-avatar">{initial}</div>'
            f'<span class="qr-chip">{chip}</span></div>'
            f'<div class="qr-agent-name">{name}</div>'
            f'<div class="qr-agent-role">{role}</div>'
            f'<div class="qr-agent-foot">{foot}</div></div>'
        )

    percent = int(100 * finished / len(AGENTS))
    slot.markdown(
        '<div class="qr-team">'
        f'<div class="qr-team-head"><h2>Agent team</h2><span>{summary}</span></div>'
        f'<div class="qr-meter"><b style="width:{percent}%"></b></div>'
        f'<div class="qr-agents">{"".join(cards)}</div></div>',
        unsafe_allow_html=True,
    )


def run_pipeline_live(topic: str, slot) -> dict:
    """Same four steps as pipeline.run_research_pipeline, with live UI updates."""
    status = {key: "waiting" for key, *_ in AGENTS}
    timings: dict = {}
    words: dict = {}
    state = {"topic": topic}

    def run_step(key, fn, extract):
        status[key] = "running"
        render_team(slot, status, timings, words)
        started = time.perf_counter()
        try:
            text = to_text(extract(fn()))
        except Exception as exc:
            status[key] = "failed"
            render_team(slot, status, timings, words)
            raise RuntimeError(key) from exc
        timings[key] = time.perf_counter() - started
        words[key] = word_count(text)
        status[key] = "done"
        render_team(slot, status, timings, words)
        return text

    last_message = lambda result: result["messages"][-1]
    as_is = lambda result: result

    # Agent 1 - search
    state["search_results"] = run_step(
        "search",
        lambda: get_search_agent().invoke(
            {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]}
        ),
        last_message,
    )

    # Agent 2 - reader
    state["scraped_content"] = run_step(
        "read",
        lambda: get_reader_agent().invoke(
            {
                "messages": [
                    (
                        "user",
                        f"Based on the following search results about '{topic}', "
                        f"pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{state['search_results'][:800]}",
                    )
                ]
            }
        ),
        last_message,
    )

    # Agent 3 - writer
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )
    state["report"] = run_step(
        "write",
        lambda: writer_chain.invoke({"topic": topic, "research": research_combined}),
        as_is,
    )

    # Agent 4 - critic
    state["feedback"] = run_step(
        "review",
        lambda: critic_chain.invoke({"report": state["report"]}),
        as_is,
    )

    state["status"] = status
    state["timings"] = timings
    state["words"] = words
    state["finished_at"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
    return state


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "report"


def full_bundle(run: dict) -> str:
    return (
        f"# {run['topic']}\n\n_Generated by {APP_NAME} ({APP_TAGLINE}) on {run['finished_at']}_\n\n"
        f"## Report (Writer Agent)\n\n{run['report']}\n\n"
        f"## Review (Critic Agent)\n\n{run['feedback']}\n\n"
        f"## Search findings (Search Agent)\n\n{run['search_results']}\n\n"
        f"## Source content (Reader Agent)\n\n{run['scraped_content']}\n"
    )


def set_topic(value: str) -> None:
    st.session_state.topic_input = value


def open_run(index: int) -> None:
    st.session_state.active = index


def clear_history() -> None:
    st.session_state.runs = []
    st.session_state.active = None


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
st.session_state.setdefault("runs", [])
st.session_state.setdefault("active", None)
st.session_state.setdefault("topic_input", "")


# ----------------------------------------------------------------------------
# Sidebar - report history
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("**History**")
    if st.session_state.runs:
        for i, past in enumerate(st.session_state.runs):
            st.button(past["topic"], key=f"run_{i}", on_click=open_run, args=(i,), help=past["finished_at"])
        st.divider()
        st.button("Clear history", on_click=clear_history)
    else:
        st.caption("Reports you generate in this session appear here.")


# ----------------------------------------------------------------------------
# Top bar, hero and topic form
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="qr-bar">'
    f'<div class="qr-brand"><span class="qr-logo"><i></i><i></i><i></i><i></i></span>{APP_NAME}</div>'
    f'<div class="qr-tag">{APP_TAGLINE}</div></div>'
    '<div class="qr-hero"><h1>Research any topic with a team of AI agents.</h1>'
    "<p>Four agents work in sequence: one searches the web, one reads the best source, "
    "one writes the report and one reviews it before you see it.</p></div>",
    unsafe_allow_html=True,
)

with st.form("research_form"):
    input_col, button_col = st.columns([4, 1.2], vertical_alignment="bottom")
    with input_col:
        st.text_input(
            "Research topic",
            key="topic_input",
            placeholder="Enter a topic, e.g. AI tutors in school education",
            label_visibility="collapsed",
        )
    with button_col:
        submitted = st.form_submit_button("Generate report")

st.markdown('<div class="qr-label">Examples</div>', unsafe_allow_html=True)
example_cols = st.columns(len(EXAMPLE_TOPICS))
for col, example in zip(example_cols, EXAMPLE_TOPICS):
    col.button(example, key=f"ex_{example}", on_click=set_topic, args=(example,))


# ----------------------------------------------------------------------------
# Agent team + run
# ----------------------------------------------------------------------------
team_slot = st.empty()
topic = st.session_state.topic_input.strip()

if submitted and not topic:
    st.warning("Enter a topic, then select Generate report.")

if submitted and topic:
    try:
        new_run = run_pipeline_live(topic, team_slot)
    except RuntimeError as err:
        failed_name = next(name for key, name, *_ in AGENTS if key == str(err))
        st.error(
            f"The {failed_name} failed: {err.__cause__}\n\n"
            "Check your API keys and internet connection, then generate the report again."
        )
        st.stop()
    st.session_state.runs.insert(0, new_run)
    st.session_state.active = 0
    st.toast("Report generated")

active = st.session_state.active
run = st.session_state.runs[active] if active is not None and active < len(st.session_state.runs) else None

if run:
    render_team(team_slot, run["status"], run["timings"], run["words"])
elif not submitted:
    render_team(team_slot, {}, {}, {})


# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
if run:
    total = sum(run["timings"].values())
    report_words = run["words"].get("write", 0)
    st.markdown(
        f'<div class="qr-result"><h2>{html.escape(run["topic"])}</h2>'
        f'<span>Generated {run["finished_at"]} by 4 agents in {total:.0f} seconds, '
        f"{report_words:,} word report</span></div>",
        unsafe_allow_html=True,
    )

    slug = slugify(run["topic"])
    dl_report, dl_all, _ = st.columns([1, 1, 2])
    dl_report.download_button(
        "Download report",
        data=run["report"],
        file_name=f"{slug}.md",
        mime="text/markdown",
        key=f"dl_report_{active}",
    )
    dl_all.download_button(
        "Download all sections",
        data=full_bundle(run),
        file_name=f"{slug}-full.md",
        mime="text/markdown",
        key=f"dl_all_{active}",
    )

    tab_report, tab_review, tab_search, tab_source = st.tabs(
        ["Report", "Review", "Search findings", "Source content"]
    )
    with tab_report:
        st.markdown('<div class="qr-by">Written by the Writer Agent</div>', unsafe_allow_html=True)
        st.markdown(run["report"])
    with tab_review:
        st.markdown('<div class="qr-by">Feedback from the Critic Agent</div>', unsafe_allow_html=True)
        st.markdown(run["feedback"])
    with tab_search:
        st.markdown('<div class="qr-by">Collected by the Search Agent</div>', unsafe_allow_html=True)
        st.markdown(run["search_results"])
    with tab_source:
        st.markdown('<div class="qr-by">Extracted by the Reader Agent</div>', unsafe_allow_html=True)
        st.markdown(run["scraped_content"])