# Design Log: Make arXiv ID Clickable in Saved Papers Tab

Date: 2026-02-23

## Background

The saved papers tab in `frontend/app.py:187` displays arXiv ID as plain text. Since we already have the arXiv ID, we can make it a clickable link to the PDF on arXiv.

## Problem

Users viewing saved papers must manually copy the arXiv ID and search for it to access the PDF. This adds friction when they want to quickly open the paper.

## Questions and Answers

**Q: Which URL format to use?**
A: `https://arxiv.org/pdf/{arxiv_id}` - direct link to PDF

**Q: Should we link to abstract page or PDF?**
A: PDF is more useful since users typically want to read the full paper

## Design

### Change: `frontend/app.py:187`

```python
# Before
st.markdown(f"**arXiv ID:** {paper.get('arxiv_id')}")

# After
arxiv_id = paper.get('arxiv_id')
st.markdown(f"**arXiv ID:** [{arxiv_id}](https://arxiv.org/pdf/{arxiv_id})")
```

Rendered as: `arXiv ID: [2602.04315](https://arxiv.org/pdf/2602.04315)`

## Implementation Plan

1. Update line 187 in `frontend/app.py` to make arXiv ID a clickable markdown link

## Trade-offs

- ✅ Simple one-line change
- ✅ No database changes needed
- ✅ No API changes needed
