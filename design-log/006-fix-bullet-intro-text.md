# Design Log: Fix Bullet Summary Introductory Text

## Background

The `generate_bullet_summary()` function in `backend/summarizer.py` sometimes returns LLM introductory text (e.g., "아래는 해당 논문의 핵심 요약입니다:") before the actual bullet points. This causes the first bullet to render incorrectly in the UI.

## Problem

- LLM returns introductory text before bullet points
- Current code includes ALL non-empty lines in the result (line 111)
- Intro text renders as the first bullet item in the UI

---

## Design

### Solution: Filter bullets + retry logic

1. **Update prompt**: Add explicit instruction to not include introductory text
2. **Filter lines**: Only include lines starting with `- ` (markdown bullet format)
3. **Retry logic**: Retry up to 3 times if no valid bullets found
4. **Logging**: Log retry attempts for debugging

### Code Changes

#### 1. Update BULLET_PROMPT (lines 26-30)
```python
BULLET_PROMPT = """Based on the following detailed paper analysis, create a brief summary using bullet points in Korean. Use markdown bullet list format (- item):

{detailed_summary}

Provide 3-5 bullet points in markdown format. 
IMPORTANT: Only return the bullet points, no introductory text or explanations. Start directly with the bullet points."""
```

#### 2. Update generate_bullet_summary function (lines 94-112)
- Add internal retry loop (max 3 attempts)
- Filter to only lines starting with `- `
- Strip `- ` prefix from each line
- Add logging for retry attempts
- Fallback: return all non-empty lines if still no valid bullets after 3 retries

---

## Implementation Plan

1. Update `BULLET_PROMPT` template in `backend/summarizer.py`
2. Rewrite `generate_bullet_summary()` with retry logic and filtering
3. Test manually

---

## Expected Behavior

| Attempt | Result |
|---------|--------|
| 1 | LLM called, filter bullets, return if valid |
| 2 | If no valid bullets, retry LLM |
| 3 | If still no valid bullets, retry one more time |
| Fallback | Return all non-empty lines (original behavior) |

---

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Retry up to 3 times | Extra LLM calls (cost), but more reliable |
| Fallback to all lines | Still shows something if LLM completely fails |
| Add logging | Helps debug issues, slight performance overhead |

---

## Implementation Results

### Backend (✅ COMPLETE)

1. Updated `BULLET_PROMPT` in `backend/summarizer.py:29-34`
   - Added "IMPORTANT: Only return the bullet points..." instruction

2. Updated `generate_bullet_summary()` in `backend/summarizer.py:98-138`
   - Added internal retry loop (up to 3 attempts)
   - Added filtering to only include lines starting with `- `
   - Added logging for successful attempts and retries
   - Added fallback to return all non-empty lines if still no valid bullets after 3 retries

3. Added logging import in `backend/summarizer.py:3,9`
   - Added `import logging`
   - Added `logger = logging.getLogger(__name__)`

---

## Test Results

Manual testing:
1. Enter arXiv ID → Summarize paper
2. Check Bullet Summary tab
3. Verify no introductory text appears before bullet points
4. Check logs for retry attempts (if any)

---

*Created: 2026-02-20*
*Status: Implemented*
