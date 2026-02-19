# Design Log: Regenerate Summary Functionality

## Background

When a user clicks "Regenerate Summary" on a cached paper, the current implementation only clears session state and triggers a rerun. No network request is made to the backend, so:
1. No loading indicator is shown
2. The new summary is never generated (cached data is returned)
3. The user cannot see whether regeneration is in progress

## Problem

The "Regenerate Summary" button in `frontend/app.py` (lines 109-112) does not actually trigger regeneration:
- It only clears session state and calls `st.rerun()`
- The summarize flow re-fetches cached data from the API
- No loading state is displayed to the user

Additionally, the backend `/api/paper/{arxiv_id}/summarize` endpoint always returns cached data if the paper exists - there's no way to force regeneration.

---

## Design

### Option A: Add `force` parameter to existing endpoint (Chosen)

Modify the existing `/api/paper/{arxiv_id}/summarize` endpoint:
- Add optional query parameter: `force: bool = False`
- When `force=True` and paper exists: delete existing record, generate fresh summary
- When `force=False` (default): current behavior (return cached if exists)

### Option B: New `/regenerate` endpoint

Create dedicated endpoint `POST /api/paper/{arxiv_id}/regenerate`:
- Explicitly handles regeneration case
- More RESTful but requires additional endpoint

**Decision**: Option A is simpler and reuses existing logic.

---

## Implementation Plan

### Backend (backend/main.py)

1. Add `force: bool = False` query parameter to `summarize_paper` endpoint (line 81)
2. After `extract_arxiv_id`, add logic:
   ```python
   if force:
       existing = db.query(Paper).filter(Paper.arxiv_id == extracted_id).first()
       if existing:
           db.delete(existing)
           db.commit()
   ```
3. The rest of the flow remains the same (generate summary, save to DB)

### Frontend (frontend/app.py)

1. Update `summarize_paper()` function (line 17-23):
   - Add `force: bool = False` parameter
   - Pass as query param: `f"{API_BASE}/api/paper/{arxiv_id}/summarize?force={force}"`

2. Update regenerate button handler (lines 109-112):
   ```python
   if st.button("Regenerate Summary", key="regen_cached"):
       progress_placeholder = st.empty()
       progress_placeholder.info("Regenerating summary...")
       
       result = summarize_paper(st.session_state.arxiv_id, force=True)
       
       if "error" in result:
           progress_placeholder.error(f"Error: {result['error']}")
       else:
           progress_placeholder.success("Summary regenerated!")
           st.session_state.result = result
           st.session_state.show_result = True
   ```

---

## Expected Behavior

| Step | User Sees |
|------|-----------|
| 1 | User views cached summary, clicks "Regenerate Summary" |
| 2 | Loading spinner appears: "Regenerating summary..." |
| 3 | Backend deletes old record, generates new summary, saves to DB |
| 4 | Success message: "Summary regenerated!" |
| 5 | Updated summary displayed with new content |

---

## Implementation Results

### Backend (✅ COMPLETE)
1. Added `force: bool = False` query parameter to `summarize_paper` endpoint (main.py:82)
2. Added logic to delete existing paper when `force=True` (main.py:88-92)
3. When force=True, the endpoint proceeds to generate fresh summary and save to DB

### Frontend (✅ COMPLETE)
1. Updated `summarize_paper()` function to accept `force` parameter (app.py:17)
2. Pass `force` as query parameter to API call (app.py:20)
3. Added loading spinner "Regenerating summary..." during regeneration (app.py:113)
4. Handle success/error responses properly (app.py:117-122)
5. Added `st.rerun()` after regeneration to refresh the UI (app.py:123)

---

## Test Results

Manual testing flow:
1. Enter arXiv ID → Summarize paper (cached)
2. Click "Regenerate Summary"
3. Loading spinner should appear
4. New summary should be generated and displayed

---

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Add force param to existing endpoint | Simple change; backward compatible |
| Delete + regenerate vs update | Simpler (no partial state); ensures fresh summary |
| Loading spinner in frontend | Provides clear UX feedback |

---

*Created: 2026-02-19*
*Status: Implemented*
