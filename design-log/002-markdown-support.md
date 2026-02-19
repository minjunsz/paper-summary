# Design Log: Markdown Support

## Background

User requested that summaries should be formatted in markdown and the frontend should render markdown properly.

## Problem

- Backend generates plain text summaries
- Frontend uses `st.write()` which displays plain text without markdown rendering
- Need to enable markdown formatting (headers, lists, bold, etc.)

## Questions and Answers

**Q: Which markdown elements should be supported?**
**A:** CommonMark standard (headers, bold, lists, numbered lists, code blocks)

**Q: Should 3-line summary use numbered list?**
**A:** Yes, user requested numbered list format (1., 2., 3.)

**Q: Any new dependencies needed?**
**A:** No. Streamlit's `st.markdown()` already supports CommonMark markdown.

## Design

### Architecture (No Change)

```
┌─────────────┐     ┌─────────────┐
│  Streamlit  │────▶│   FastAPI   │
│  (Frontend) │     │   (Backend) │
└─────────────┘     └─────────────┘
```

### Backend: Update LLM Prompts

| Summary Type | Prompt Change |
|--------------|---------------|
| Detailed | Add: "Use markdown formatting (## for headers, **bold**, - for bullet lists)" |
| 3-line | Add: "Use numbered list format: 1. ... 2. ... 3. ..." |
| Bullet | Add: "Use markdown bullet list format: - item" |

### Frontend: Use st.markdown()

Replace `st.write()` with `st.markdown()` for all summary outputs:

| Location | File:Line | Before | After |
|----------|-----------|--------|-------|
| 3-Line tab | app.py:~122 | `st.write(result.get("three_line_summary", ""))` | `st.markdown(result.get("three_line_summary", ""))` |
| Bullet tab | app.py:~127 | `st.write(f"• {b}")` | `st.markdown(f"- {b}")` |
| Detailed tab | app.py:~130 | `st.write(result.get("detailed_summary", ""))` | `st.markdown(result.get("detailed_summary", ""))` |
| Saved 3-line | app.py:~144 | `st.write(paper.get("three_line_summary", ""))` | `st.markdown(paper.get("three_line_summary", ""))` |
| Saved bullet | app.py:~148 | `st.write(f"• {b}")` | `st.markdown(f"- {b}")` |
| Saved detailed | app.py:~151 | `st.write(paper.get("detailed_summary"))` | `st.markdown(paper.get("detailed_summary"))` |

## Implementation Plan

### Phase 1: Backend
1. Update `DETAILED_PROMPT` in `backend/summarizer.py` to request markdown
2. Update `THREE_LINE_PROMPT` to request numbered list format
3. Update `BULLET_PROMPT` to request markdown bullet list format

### Phase 2: Frontend
1. Replace `st.write()` with `st.markdown()` in `frontend/app.py` for all summary displays

### Phase 3: Testing
1. Run backend and frontend
2. Verify markdown renders correctly in UI

## Examples

### 3-Line Summary (Expected Output)
```
1. 이 연구는 이전 방법의 한계를 지적하고 새로운 접근법을 제안합니다.
2. 핵심 아이디어는 ...을 활용하여 ...을 달성합니다.
3. 실험 결과, 기존 방법 대비 ...% 향상된 성능을 보였습니다.
```

### Bullet Summary (Expected Output)
- 새로운 프로포즈 방법론 제안
- 기존 baseline 대비 향상된 성능
- 제한점: 특정 케이스에서 ..."

### Detailed Summary (Expected Output)
## 문제
...

## 방법
...

## 결론
...

---

*Created: 2026-02-19*
*Status: Approved for implementation*
