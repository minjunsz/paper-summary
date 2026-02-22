import streamlit as st
import httpx
import time

API_BASE = "http://localhost:8001"


def get_metadata(arxiv_id: str):
    try:
        resp = httpx.get(f"{API_BASE}/api/paper/{arxiv_id}/metadata", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def summarize_paper(arxiv_id: str, force: bool = False):
    try:
        resp = httpx.post(
            f"{API_BASE}/api/paper/{arxiv_id}/summarize?force={force}", timeout=600
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_paper(arxiv_id: str):
    try:
        resp = httpx.get(f"{API_BASE}/api/paper/{arxiv_id}", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_all_papers():
    try:
        resp = httpx.get(f"{API_BASE}/api/papers", timeout=30)
        resp.raise_for_status()
        return resp.json().get("papers", [])
    except Exception as e:
        return []


def search_papers(query: str):
    try:
        resp = httpx.get(
            f"{API_BASE}/api/papers/search", params={"q": query}, timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("papers", [])
    except Exception as e:
        return []


def check_health():
    try:
        resp = httpx.get(f"{API_BASE}/api/health", timeout=10)
        return resp.status_code == 200
    except:
        return False


st.set_page_config(page_title="Paper Summary AI", page_icon="📄")

if not check_health():
    st.error("Backend is not running. Please start the API server first.")
    st.code("uvicorn backend.main:app --host 0.0.0.0 --port 8001", language="bash")
    st.stop()

st.title("📄 Paper Summary AI")

tab1, tab2 = st.tabs(["Summarize", "Saved Papers"])

with tab1:
    input_str = st.text_input(
        "Enter arXiv link or ID",
        placeholder="https://arxiv.org/abs/2602.16705 or 2602.16705",
    )

    if input_str:
        import re

        match = re.search(r"(\d+\.\d+)", input_str)
        if match:
            arxiv_id = match.group(1)
            st.session_state.arxiv_id = arxiv_id
        else:
            st.error("Invalid arXiv ID format")
            st.session_state.arxiv_id = None
    else:
        st.session_state.arxiv_id = None

    if st.session_state.arxiv_id:
        with st.spinner("Fetching metadata..."):
            metadata = get_metadata(st.session_state.arxiv_id)

        if "error" in metadata:
            st.error(f"Failed to fetch metadata: {metadata['error']}")
        else:
            st.subheader("Paper Metadata")
            st.markdown(f"**Title:** {metadata.get('title', '')}")
            st.markdown(f"**Authors:** {', '.join(metadata.get('authors', []))}")
            with st.expander("Abstract"):
                st.write(metadata.get("abstract", ""))

            st.markdown("---")

            if st.button("Summarize Paper", type="primary"):
                progress_placeholder = st.empty()
                progress_placeholder.info("Starting summarization...")

                progress_placeholder.info("Downloading PDF...")
                result = summarize_paper(st.session_state.arxiv_id)

                if "error" in result:
                    progress_placeholder.error(f"Error: {result['error']}")
                else:
                    progress_placeholder.success("Summarization complete!")
                    st.session_state.result = result
                    st.session_state.show_result = True

            if st.session_state.get("show_result") and st.session_state.get("result"):
                result = st.session_state.result

                if result.get("is_cached"):
                    st.info("📌 이 논문은 이미 요약되어 있습니다")
                    if st.button("Regenerate Summary", key="regen_cached"):
                        progress_placeholder = st.empty()
                        progress_placeholder.info("Regenerating summary...")

                        result = summarize_paper(st.session_state.arxiv_id, force=True)

                        if "error" in result:
                            progress_placeholder.error(f"Error: {result['error']}")
                        else:
                            progress_placeholder.success("Summary regenerated!")
                            st.session_state.result = result
                        st.rerun()

                st.markdown("### Summary Results")

                if result.get("summary_warning"):
                    st.warning(result["summary_warning"])

                tab3, tab4, tab5 = st.tabs(["3-Line", "Bullet", "Detailed"])

                with tab3:
                    st.markdown(result.get("three_line_summary", ""))

                with tab4:
                    bullets = result.get("bullet_summary", [])
                    for b in bullets:
                        st.markdown(f"- {b}")

                with tab5:
                    st.markdown(result.get("detailed_summary", ""))

with tab2:
    st.subheader("Saved Papers")

    search_query = st.text_input(
        "Search papers",
        placeholder="Search by title, abstract, or summary...",
        key="paper_search",
    )

    if search_query and len(search_query.strip()) >= 2:
        papers = search_papers(search_query)
        search_info = f'Search results for "{search_query}"'
    else:
        papers = get_all_papers()
        search_info = None

    if search_info:
        st.caption(search_info)

    if not papers:
        if search_info:
            st.info(f"No papers found for query: {search_query}")
        else:
            st.info("No papers saved yet.")
    else:
        for paper in papers:
            with st.expander(f"{paper.get('title', paper.get('arxiv_id'))}"):
                st.markdown(f"**arXiv ID:** {paper.get('arxiv_id')}")
                st.markdown(f"**Authors:** {', '.join(paper.get('authors', []))}")
                if paper.get("summary_warning"):
                    st.warning(paper["summary_warning"])
                st.markdown("**3-Line Summary:**")
                st.markdown(paper.get("three_line_summary", ""))
                if paper.get("bullet_summary"):
                    st.markdown("**Bullet Summary:**")
                    for b in paper.get("bullet_summary", []):
                        st.markdown(f"- {b}")
                if paper.get("detailed_summary"):
                    with st.expander("Detailed Summary"):
                        st.markdown(paper.get("detailed_summary"))
