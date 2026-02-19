# Design Log: BM25 Search for Saved Papers

## Background

The "Saved Papers" tab in the frontend currently displays all papers in a flat list ordered by `created_at.desc()`. Users have no way to search or filter through their saved papers. Adding BM25 full-text search will allow efficient keyword-based retrieval.

---

## Problem

- No search functionality in Saved Papers tab
- Users must manually scroll through all papers to find specific content
- Need a relevance-ranked search over paper metadata and summaries

---

## Questions and Answers

### Q1: What fields should be searched?

**Answer**: Search all text fields:
- `title` (highest weight)
- `abstract` (high weight)
- `detailed_summary` (medium weight)
- `three_line_summary` (medium weight)
- `authors` (lower weight, joined as string)

### Q2: Should search run on backend or frontend?

**Answer**: Backend. BM25 requires building an inverted index which is more efficient to manage server-side. Also keeps client lightweight.

### Q3: How to handle BM25 index updates?

**Answer**: Rebuild index on each search request for simplicity. Given small dataset (<1000 papers), this is fast enough. Alternative: rebuild on paper add/delete.

### Q4: Minimum query length?

**Answer**: Require at least 2 characters to avoid noisy results.

---

## Design

### Architecture

```
┌─────────────┐     GET /api/papers/search?q=query     ┌─────────────┐
│  Frontend   │ ─────────────────────────────────────► │   Backend   │
│  (Streamlit)│                                        │  (FastAPI)  │
│             │ ◄──────────────────────────────────── │             │
└─────────────┘     { papers: [PaperResponse, ...] }   └─────────────┘
```

### API Endpoint

```
GET /api/papers/search?q={query}&limit={limit}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query |
| `limit` | int | 20 | Max results to return |

**Response**:
```json
{
  "papers": [
    {
      "arxiv_id": "2602.16705",
      "title": "Attention Is All You Need",
      "authors": ["Ashish Vaswani", ...],
      "abstract": "...",
      "detailed_summary": "...",
      "three_line_summary": "...",
      "bullet_summary": [...],
      "created_at": "2026-02-20T10:00:00"
    }
  ]
}
```

### BM25 Implementation

- **Library**: `rank-bm25`
- **Tokenization**: Simple whitespace tokenization, lowercase
- **Index**: Built fresh on each request (corpus is small)
- **Scoring**: BM25Okapi with default parameters (k1=1.5, b=0.75)

### Code Structure

#### 1. Add dependency
`pyproject.toml`: Add `rank-bm25>=0.1.0`

#### 2. Backend endpoint
`backend/main.py`:
- Import `BM25Okapi` from `rank_bm25`
- New function `search_papers(query: str, limit: int = 20)`
- Tokenize and index all paper text fields
- Return ranked results

#### 3. Frontend integration
`frontend/app.py`:
- Add `st.text_input` for search query in Saved Papers tab
- Add debounced search (on Enter or button press)
- Call `GET /api/papers/search` endpoint
- Display results or "No results found"

---

## Implementation Plan

### Phase 1: Backend
1. Add `rank-bm25` to dependencies
2. Implement `/api/papers/search` endpoint in `backend/main.py`
3. Test with curl

### Phase 2: Frontend
1. Add search input in Saved Papers tab
2. Connect to search endpoint
3. Handle empty results
4. Test end-to-end

---

## Examples

### Good Search Queries
- `"transformer"` → Finds papers mentioning transformer architecture
- `"attention mechanism"` → Finds papers with attention in title/abstract
- `"强化学习"` → Finds Korean text in summaries

### Edge Cases
| Input | Expected Behavior |
|-------|-------------------|
| Empty query | Return all papers (or disable search) |
| `"a"` (1 char) | Show warning, require 2+ chars |
| No matches | Show "No papers found for query: X" |
| Special chars | Escape/reject, only allow alphanumeric + spaces |

---

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Rebuild index on each request | Simple code, fine for small datasets |
| Single search endpoint | No incremental index updates needed |
| Backend-only search | Keeps client lightweight |
| Default BM25 parameters | May need tuning for optimal results |

---

## Alternative Approaches Considered

1. **SQL LIKE queries**: Simpler but no relevance ranking, poor performance
2. **Full-text search with SQLite FTS5**: Built-in but requires table changes
3. **Elasticsearch/OpenSearch**: Overkill for single-user app
4. **Frontend filtering**: Would require loading all papers, no BM25 ranking

**Chose BM25** because it's lightweight, provides relevance ranking, and integrates easily with Python.

---

*Created: 2026-02-20*
*Status: Implemented*

---

## Implementation Results

### Phase 1: Backend ✅

1. **Dependency** - Added `rank-bm25>=0.2.2` to `pyproject.toml:14`

2. **Search endpoint** - `backend/main.py:208-253`
   - Added `tokenize()` helper function (lines 202-205)
   - Added `GET /api/papers/search?q={query}&limit=20` endpoint
   - Searches: title, abstract, detailed_summary, three_line_summary, authors
   - Returns BM25-ranked results

### Phase 2: Frontend ✅

1. **Search function** - `frontend/app.py:46-54`
   - Added `search_papers(query: str)` function

2. **Search UI** - `frontend/app.py:159-177`
   - Added search input in Saved Papers tab
   - Shows "Search results for: X" caption when searching
   - Shows "No papers found for query: X" when no matches

### Test Commands

```bash
# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8001

# Start frontend
streamlit run frontend/app.py

# Test search API
curl "http://localhost:8001/api/papers/search?q=transformer"
```

### Notes

- Search requires minimum 2 characters
- No search-on-type (user must press Enter or click elsewhere)
- Simple whitespace tokenization, lowercase
- Default BM25 parameters (k1=1.5, b=0.75)
