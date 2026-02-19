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


def summarize_paper(arxiv_id: str):
    try:
        resp = httpx.post(f"{API_BASE}/api/paper/{arxiv_id}/summarize", timeout=600)
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
                    if st.button("Retry"):
                        st.rerun()
                else:
                    progress_placeholder.success("Summarization complete!")

                    st.session_state.result = result
                    st.session_state.show_result = True

            if st.session_state.get("show_result") and st.session_state.get("result"):
                result = st.session_state.result

                st.markdown("### Summary Results")

                tab3, tab4, tab5 = st.tabs(["3-Line", "Bullet", "Detailed"])

                with tab3:
                    st.write(result.get("three_line_summary", ""))

                with tab4:
                    bullets = result.get("bullet_summary", [])
                    for b in bullets:
                        st.write(f"• {b}")

                with tab5:
                    st.write(result.get("detailed_summary", ""))

with tab2:
    st.subheader("Saved Papers")
    papers = get_all_papers()

    if not papers:
        st.info("No papers saved yet.")
    else:
        for paper in papers:
            with st.expander(f"{paper.get('title', paper.get('arxiv_id'))}"):
                st.markdown(f"**arXiv ID:** {paper.get('arxiv_id')}")
                st.markdown(f"**Authors:** {', '.join(paper.get('authors', []))}")
                st.markdown("**3-Line Summary:**")
                st.write(paper.get("three_line_summary", ""))
                if paper.get("bullet_summary"):
                    st.markdown("**Bullet Summary:**")
                    for b in paper.get("bullet_summary", []):
                        st.write(f"• {b}")
                if paper.get("detailed_summary"):
                    with st.expander("Detailed Summary"):
                        st.write(paper.get("detailed_summary"))
