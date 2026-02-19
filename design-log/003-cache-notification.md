# Design Log: Visual Notification for Previously Summarized Papers

## Background

When a user requests summarization for a paper that already exists in the database, the system currently returns the cached summary silently without informing the user. Users should be notified when they're viewing a previously summarized paper.

## Problem

Currently, the API returns the same response format whether the paper was just summarized or retrieved from cache. Users have no way to know if the summary is fresh or from a previous session.

---

## Design

### Backend Changes

Modify `PaperResponse` in `backend/main.py`:
- Add `is_cached: bool = False` field

Update the `/api/paper/{arxiv_id}/summarize` endpoint:
- When returning existing paper: set `is_cached=True`
- When creating new paper: set `is_cached=False`

### Frontend Changes

In `frontend/app.py`:
1. Check `is_cached` flag in API response
2. If `True`, display notification with `created_at` timestamp
3. Add a "Regenerate Summary" button to allow users to regenerate even if cached

---

## Implementation Results

### Phase 1: Backend (✅ COMPLETE)
1. Added `is_cached: bool = False` to `PaperResponse` model
2. Set `is_cached=True` when returning existing paper
3. Set `is_cached=False` when creating new paper

### Phase 2: Frontend (✅ COMPLETE)
1. Check `is_cached` flag in API response
2. Display notification using `st.info()` with timestamp
3. Added "Regenerate Summary" button when cached

---

## Questions Answered

1. **Should notification appear in Saved Papers tab?** → No (keep it simple, only show on summarize action)
2. **Should users be able to regenerate cached summaries?** → Yes (added button)

---

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Add flag to backend | Requires API change; explicit and reliable |
| Use st.info() | Simple; matches Streamlit patterns |
| Regenerate button | More UX options; slightly more complex flow |

---

*Created: 2026-02-19*
*Status: Implemented*
