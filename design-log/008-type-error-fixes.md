# Design Log: Fix Type Errors

## Background

Running `pyright backend/ frontend/` reveals 16 type errors in the backend code. The frontend (Streamlit) has no errors.

## Problems

### 1. backend/arxiv.py (5 errors)
- **Issue**: `entry.find()` returns `Element | None`, but code accesses `.text` without null check
- **Locations**: lines 38, 41, 48

### 2. backend/config.py (1 error)
- **Issue**: `Settings()` called without required `openrouter_api_key` parameter
- **Location**: line 15

### 3. backend/database.py (9 errors)
- **Issue**: `Column[T]` assigned to `Mapped[T]` - wrong pattern for SQLAlchemy 2.0 declarative mapping
- **Locations**: lines 12-20

### 4. backend/summarizer.py (1 error)
- **Issue**: Variable `content` possibly unbound - used after loop that may not execute
- **Location**: line 137

## Questions and Answers

**Q: Should we use `Column` with type annotations or just `Mapped`?**
A: In SQLAlchemy 2.0, the recommended pattern is to use `Mapped[T]` with `mapped_column()`. However, for simplicity, we can keep `Column` and adjust the type annotation to `Column[T]` instead of `Mapped[T]`.

**Q: How to handle pydantic-settings requiring API key?**
A: The API key should come from environment variables. The error occurs because pyright doesn't understand pydantic-settings behavior. We can add a default factory or make it optional with a validation that raises if not provided.

## Design

### Fix 1: arxiv.py
Add null checks after `entry.find()` calls:
```python
title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
if title_elem is None or title_elem.text is None:
    raise ValueError(f"No title found for arxiv_id: {arxiv_id}")
title = title_elem.text.strip()
```

### Fix 2: config.py
Add `field_validator` or make the field have a default:
```python
openrouter_api_key: str = ""
```
Or better, use a validator that checks at runtime.

### Fix 3: database.py
Change `Mapped[T]` to `Column[T]`:
```python
id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
```

### Fix 4: summarizer.py
Initialize `content` before the loop:
```python
content = ""
for attempt in range(3):
    ...
```

## Implementation Plan

1. Fix `backend/arxiv.py` - add null checks for XML elements
2. Fix `backend/config.py` - add empty string default or runtime validation
3. Fix `backend/database.py` - change `Mapped` to `Column` types
4. Fix `backend/summarizer.py` - initialize `content` before loop
5. Run `pyright` to verify all fixes

## Examples

### Before (arxiv.py)
```python
title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
```

### After
```python
title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
if title_elem is None or title_elem.text is None:
    raise ValueError(f"No title found for arxiv_id: {arxiv_id}")
title = title_elem.text.strip()
```

## Trade-offs

- **Fix 1**: More verbose but explicit null handling
- **Fix 2**: Empty string default is a workaround; runtime validation is better but adds complexity
- **Fix 3**: Using `Column[T]` loses some SQLAlchemy 2.0 type benefits but is simpler
- **Fix 4**: Minor initialization overhead but satisfies type checker

## Implementation Results

**Type check result**: 0 errors, 0 warnings, 0 informations

### Summary of Changes

| File | Change |
|------|--------|
| `backend/arxiv.py` | Added explicit null checks for `title_elem.text`, `abstract_elem.text`, and `name.text` |
| `backend/config.py` | Added default empty string + `field_validator` for runtime validation |
| `backend/database.py` | Used SQLAlchemy 2.0 `mapped_column()` pattern instead of legacy `Column` |
| `backend/summarizer.py` | Initialized `content = ""` before the retry loop |

### Deviations from Original Design

- **Fix 3**: Initially tried using `Column[T]` as type annotations, but this created more type errors (Column is invariant). Switched to SQLAlchemy 2.0's `mapped_column()` which properly integrates with `Mapped[T]`.
- **Fix 2**: Used both default empty string AND field_validator for safety - empty string satisfies pyright, validator ensures runtime safety.
