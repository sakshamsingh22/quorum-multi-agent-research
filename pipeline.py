"""Orchestrate Quorum's four research stages."""
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


def run_research_pipeline(topic: str) -> dict:
    """Run search, reading, report-writing and critique for a research topic."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic must not be empty.")
    topic = topic.strip()
    if len(topic) > 500:
        raise ValueError("Research topic must be 500 characters or fewer.")

    state = {"topic": topic}
    search_result = build_search_agent().invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = search_result["messages"][-1].content
    if not state["search_results"].strip():
        raise RuntimeError("Search stage returned no usable results.")

    reader_result = build_reader_agent().invoke({
        "messages": [("user",
            f"Choose the most relevant public URL from these results about '{topic}' "
            f"and extract useful content.\n\n{state['search_results'][:5000]}")]
    })
    state["scraped_content"] = reader_result["messages"][-1].content
    if not state["scraped_content"].strip():
        raise RuntimeError("Reader stage returned no usable content.")

    research = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SOURCE CONTENT:\n{state['scraped_content']}"
    )
    state["report"] = writer_chain.invoke({"topic": topic, "research": research})
    if not str(state["report"]).strip():
        raise RuntimeError("Writer stage returned an empty report.")
    state["feedback"] = critic_chain.invoke({"report": state["report"]})
    return state


if __name__ == "__main__":
    run_research_pipeline(input("Enter a research topic: "))
