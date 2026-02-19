# Design Log: Paper Summary AI Workflow

## Background

Users want to summarize arXiv papers using LLM. They provide an arXiv link or ID, and the system:
1. Downloads the PDF
2. Parses it to text
3. Generates three types of summaries using Openrouter LLM
4. Stores results for later retrieval

## Problem

Need a system that:
- Fetches arXiv metadata for user verification
- Processes PDF files reliably
- Generates consistent summaries in Korean
- Provides reactive UI with progress visibility
- Persists results for future access

## Questions and Answers

### Tech Stack
**Q: What language and framework should we use?**
**A:** Python with FastAPI for backend, Streamlit for prototyping frontend.

**Q: Why separate frontend and backend?**
**A:** User may pivot to Vue.js later, so keep them decoupled via REST API.

### PDF Processing
**Q: Which library for PDF parsing?**
**A:** pymupdf (fitz)

**Q: Should PDFs be cached locally?**
**A:** No, discard after processing.

### Database
**Q: What fields to store?**
**A:** arxiv_id, title, authors, detailed_summary, three_line_summary, bullet_summary, created_at

### Metadata
**Q: What metadata to show for user verification?**
**A:** title, authors, abstract

### LLM Configuration
**Q: What model and settings?**
**A:** 
- Detailed analysis: `arcee-ai/trinity-large-preview:free`
- 3-line & bullet summary: `arcee-ai/trinity-mini:free`
- Keep default temperature/max_tokens

**Q: All summaries in Korean?**
**A:** Yes, all three outputs should be in Korean.

### Error Handling
**Q: Retry strategy?**
**A:** Retry 3 times with backoff

### UI Requirements
- Show metadata before summarizing (user verification)
- Show progress: download → parse → detailed → 3-line/bullet
- Display error messages per step with retry
- Reactive UI during processing
- Results: show 3-line first, expandable for others

---

## Design

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Streamlit  │────▶│   FastAPI   │────▶│  Openrouter │
│  (Frontend) │     │   (Backend) │     │     LLM     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   SQLite    │
                    │   (DB)      │
                    └─────────────┘
```

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET | /api/health` | Health check |
| `GET | /api/paper/{arxiv_id}/metadata` | Fetch paper metadata |
| `POST | /api/paper/{arxiv_id}/summarize` | Run full summarization |
| `GET | /api/paper/{arxiv_id}` | Get stored summary |
| `GET | /api/papers` | List all papers |

### Database Schema

```sql
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,  -- JSON array
    abstract TEXT,
    detailed_summary TEXT,
    three_line_summary TEXT,
    bullet_summary TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation Plan

### Phase 1: Backend Core
1. Setup FastAPI project structure
2. Implement config loading from .env
3. Create SQLite database model
4. Implement arXiv metadata fetching
5. Implement PDF download and parsing with pymupdf
6. Implement Openrouter LLM client
7. Implement summarization logic (detailed → 3-line → bullet)
8. Implement REST API endpoints
9. Add retry logic (3 attempts)

### Phase 2: Frontend (Streamlit)
1. Setup Streamlit project
2. Implement API client
3. Create input form (arxiv link/ID)
4. Display metadata for verification
5. Implement progress display
6. Display results (tabs/expandable)
7. List all saved papers

### Phase 3: Error Handling & Polish
1. Add per-step error messages
2. Add retry buttons
3. Health check endpoint

---

## Examples

### API Response: Get Metadata
```json
GET /api/paper/2602.16705/metadata
{
  "arxiv_id": "2602.16705",
  "title": "Paper Title",
  "authors": ["Author One", "Author Two"],
  "abstract": "Paper abstract text..."
}
```

### API Response: Summarize
```json
POST /api/paper/2602.16705/summarize
{
  "detailed_summary": "긴细致的 분석...",
  "three_line_summary": "첫 번째 줄...\n두 번째 줄...\n세 번째 줄...",
  "bullet_summary": ["- 포인트 1", "- 포인트 2", "- 포인트 3"],
  "created_at": "2026-02-19T10:00:00Z"
}
```

---

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| SQLite | Simple, no setup, fine for single-user prototype; not scalable |
| pymupdf | Fast, reliable; may miss some complex layouts |
| Streamlit | Fast prototyping; limited customization |
| Free LLM models | No cost; may have rate limits, quality varies |

---

*Created: 2026-02-19*
*Status: Approved for implementation*
