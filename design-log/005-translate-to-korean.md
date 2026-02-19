# Design Log: Translate to Korean Feature

## Background

The `generate_detailed_summary()` function in `backend/summarizer.py` asks for Korean output in the prompt, but the LLM (`arcee-ai/trinity-large-preview:free`) doesn't always comply. This results in non-Korean reports being generated from time to time.

## Problem

The current workflow:
1. Generate detailed analysis (requests Korean, but not always followed)
2. Generate 3-line summary from detailed analysis
3. Generate bullet summary from detailed analysis

Issue: LLM sometimes ignores the Korean language instruction in the prompt.

---

## Design

### Option A: Add separate translation step (Chosen)

Add a dedicated translation step after generating the detailed analysis:
1. Generate detailed analysis (in any language)
2. **Translate to Korean** using `arcee-ai/trinity-large-preview:free`
3. Generate 3-line summary from Korean translation
4. Generate bullet summary from Korean translation

### Option B: Improve prompt engineering

Modify the original prompt to be more explicit about Korean output.

**Decision**: Option A is more reliable - a separate translation step ensures Korean output.

---

## Implementation Plan

### Backend (backend/summarizer.py)

1. Add `TRANSLATE_PROMPT` template (lines 32-40):
   ```python
   TRANSLATE_PROMPT = """Translate the following academic paper analysis to Korean. 
   - Keep all technical terminologies in English
   - Translate all non-technical terms, sentences, and explanations to Korean
   - Preserve all markdown formatting (## headers, **bold**, bullet points, etc.)

   Original text:
   {text}

   Provide the Korean translation:"""
   ```

2. Add `translate_to_korean()` function (lines 56-72):
   - Use `arcee-ai/trinity-large-preview:free` model
   - Apply retry decorator

3. Update `generate_summaries()` function (lines 115-120):
   ```python
   async def generate_summaries(paper_text: str) -> tuple[str, str, list[str]]:
       detailed = await generate_detailed_summary(paper_text)
       detailed_korean = await translate_to_korean(detailed)
       three_line = await generate_three_line_summary(detailed_korean)
       bullet = await generate_bullet_summary(detailed_korean)
       return detailed_korean, three_line, bullet
   ```

### README.md

1. Update user story 1 (lines 9-11) to describe the 3-step LLM process
2. Update "How LLM should works" section (lines 20-29) to reflect the new workflow

---

## Expected Behavior

| Step | LLM Call | Output |
|------|-----------|--------|
| 1 | Generate detailed analysis | English (or any language) |
| 2 | Translate to Korean | Korean (technical terms in English) |
| 3 | 3-line summary | Korean |
| 4 | Bullet summary | Korean |

---

## Implementation Results

### Backend (✅ COMPLETE)
1. Added `TRANSLATE_PROMPT` template in `summarizer.py:32-40`
2. Added `translate_to_korean()` function in `summarizer.py:56-72`
3. Updated `generate_summaries()` to call translate step in `summarizer.py:115-120`
4. Fixed type hints: added `or ""` for all LLM response content returns

### README.md (✅ COMPLETE)
1. Updated user story 1 to describe 3-step LLM process (lines 9-11)
2. Updated "How LLM should works" section (lines 20-31)
3. Changed "four results" to "three results" to match DB (line 31)

---

## Test Results

Manual testing flow:
1. Enter arXiv ID → Summarize paper
2. Verify detailed analysis is in Korean (with English technical terms)
3. Verify 3-line summary is in Korean
4. Verify bullet summary is in Korean

---

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Separate translation step | Extra LLM call (cost + time); but more reliable |
| Use trinity-large-preview for translation | Higher quality translation than mini model |
| Keep technical terms in English | Better readability for Korean speakers |

---

## DB Schema

No changes needed. The DB already stores 3 results:
- `detailed_summary`: Korean detailed analysis (translated)
- `three_line_summary`: Korean 3-line summary
- `bullet_summary`: Korean bullet points

---

*Created: 2026-02-20*
*Status: Implemented*
