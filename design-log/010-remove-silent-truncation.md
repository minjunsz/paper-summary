# Design Log: Remove Silent Truncation & Add Warning System

Date: 2026-02-23

## Background

Currently, `backend/config/prompts.py` line 23 silently truncates paper text to 15,000 characters before sending to LLM. This was likely added as a rough heuristic to avoid context limits, but:

- Model has 131K token context (~300K chars conservative estimate)
- Silent truncation loses data without user awareness
- No error visibility when context limit is actually reached

## Problem

1. **Silent truncation**: Users don't know when paper content is cut
2. **No error visibility**: Context limit errors aren't stored, so users may retry failing papers
3. **Unnecessary limit**: 15K chars is too conservative for 131K context model

## Questions and Answers

**Q: What threshold should trigger warning?**
A: 100K characters (about 1/3 of conservative 300K estimate, safe margin)

**Q: How to handle existing DB?**
A: Add nullable `summary_warning` column - SQLite handles automatically, backward compatible

**Q: What happens on context limit error?**
A: Store error message in warning field so it's visible when user queries paper again

## Design

### 1. Database Schema Change

Add `summary_warning: str | None` column to `Paper` model.

```python
class Paper(Base):
    # ... existing fields ...
    summary_warning: Mapped[str | None] = mapped_column(Text)
```

### 2. Prompts Change

Remove truncation from `detailed_summary_user`:

```python
def detailed_summary_user(paper_text: str) -> str:
    return f"""...{paper_text}"""  # No truncation
```

### 3. Summarizer Logic

```python
async def generate_summaries(paper_text: str) -> tuple[str, str, list[str], str | None]:
    warning = None
    
    # Check paper length
    if len(paper_text) > 100_000:
        warning = "⚠️ Paper is long (>{100K} chars), summary may be incomplete"
    
    try:
        detailed = await generate_detailed_summary(paper_text)
        # ... rest of generation ...
    except Exception as e:
        error_msg = str(e)
        if "context" in error_msg.lower() or "tokens" in error_msg.lower():
            warning = f"⚠️ Context limit exceeded: {error_msg}"
        raise
    
    return detailed, three_line, bullet, warning
```

### 4. API Response Change

```python
class PaperResponse(BaseModel):
    # ... existing fields ...
    summary_warning: str | None = None
```

### 5. Frontend Display

```python
# In display section, after summary title:
if result.get("summary_warning"):
    st.warning(result["summary_warning"])
```

## Implementation Plan

1. **Phase 1**: Update `backend/database.py` - add column
2. **Phase 2**: Update `backend/config/prompts.py` - remove truncation
3. **Phase 3**: Update `backend/summarizer.py` - add warning logic & error handling
4. **Phase 4**: Update `backend/main.py` - wire warning through
5. **Phase 5**: Update `frontend/app.py` - display warning

## Examples

### Warning Display
- Paper > 100K chars → "⚠️ Paper is long (>100K chars), summary may be incomplete"
- Context limit error → "⚠️ Context limit exceeded: [error details]"

### Good ✅
- Normal paper (10K chars) → No warning, full summary
- Long paper (150K chars) → Warning shown, partial summary still generated

### Bad ❌
- Silent truncation at 15K chars (current behavior)
- No visibility when summary fails

## Trade-offs

| Aspect | Before | After |
|--------|--------|-------|
| Long paper handling | Silent truncation | Warning + attempt anyway |
| Error visibility | Only on first failure | Stored in DB |
| Context usage | Max 15K chars | Up to 100K+ chars |
| Risk | Lost content | Potentially incomplete summary |

## Implementation Notes

- SQLite: Adding nullable column requires no migration (works out of box)
- Warning threshold: 100K characters is conservative (1/3 of 300K conservative estimate)
- Error handling: Catch exceptions with "context" or "tokens" in message to identify context limit issues

---

## Implementation Results

### Files Modified

| File | Change |
|------|--------|
| `backend/database.py:22` | Added `summary_warning` column to Paper model |
| `backend/config/prompts.py:23` | Removed `[:15000]` truncation |
| `backend/summarizer.py:97-122` | Added length warning (>100K chars) + context error handling |
| `backend/main.py` | Added `summary_warning` to all PaperResponse endpoints |
| `frontend/app.py` | Added warning display in Summarize tab and Saved Papers |

### Migration

- Created `backend/migrations/001_add_summary_warning.py` to add the new column
- Ran migration successfully - column added to existing DB

### Test Results

- Test warning flag added to paper `2602.12684` and verified in frontend
- Warning displayed correctly in both new summary and saved papers views
- Warning flag removed after verification

### Test Results: ✅ All passing

### Deviations from Design

None - implementation followed the design log exactly.
