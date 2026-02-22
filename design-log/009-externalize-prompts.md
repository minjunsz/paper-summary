# 009: Externalize LLM Prompts and Models

## Background

The paper summary workflow uses 4 LLM calls with different prompts and models. These were hardcoded as module-level strings and constants in `backend/summarizer.py`, making it difficult for users to customize prompts or switch between different LLM configurations.

## Problem

- Hardcoded prompts in Python code require code changes to modify
- No clear way to swap between different prompt styles (e.g., different languages, detail levels)
- Models specified inline with LLM calls, not easily swappable

## Questions and Answers

**Q: Why not use YAML for prompts?**
> A: YAML is less flexible for complex prompt logic (slicing, conditional formatting). Python functions provide full flexibility with native type hints and IDE support.

**Q: Why not use Jinja2 templating?**
> A: Adds extra dependency. Python f-strings in functions are sufficient and simpler.

**Q: How do users switch prompts?**
> A: Either edit `prompts.py` directly, or create a custom module and set `PROMPTS_MODULE` env var.

## Design

### Approach: Python Config with Function-based Templates

```python
# backend/config/prompts.py

class PromptConfig(TypedDict):
    model: str
    system: str
    user: Callable[..., str]

def detailed_summary_user(paper_text: str) -> str:
    return f"""Analyze paper...

{paper_text[:15000]}"""

PROMPTS: dict[str, PromptConfig] = {
    "detailed_summary": {
        "model": "arcee-ai/trinity-large-preview:free",
        "system": "You are an expert academic paper analyst.",
        "user": detailed_summary_user,
    },
    ...
}

def get_prompt(name: str) -> PromptConfig:
    custom_module = os.getenv("PROMPTS_MODULE")
    if custom_module:
        module = importlib.import_module(custom_module)
        return module.PROMPTS[name]
    return PROMPTS[name]
```

### Usage in Code

```python
# backend/summarizer.py
config = get_prompt("detailed_summary")
response = await client.chat.completions.create(
    model=config["model"],
    messages=[
        {"role": "system", "content": config["system"]},
        {"role": "user", "content": config["user"](paper_text=paper_text)},
    ],
)
```

## Implementation Plan

1. Create `backend/config/__init__.py` (empty)
2. Create `backend/config/prompts.py` with:
   - `PromptConfig` TypedDict
   - 4 prompt functions (detailed_summary, translate, three_line_summary, bullet_summary)
   - `PROMPTS` dict
   - `get_prompt()` loader
3. Update `backend/summarizer.py` to use `get_prompt()`
4. Document in `.env.example` with `PROMPTS_MODULE` comment

## Examples

### Default Prompts (current)
- `backend/config/prompts.py` - Built-in Korean prompts

### Custom Prompts
Create `backend/config/prompts_custom.py`:
```python
from backend.config.prompts import PromptConfig

def english_summary_user(paper_text: str) -> str:
    return f"Analyze in English: {paper_text[:10000]}"

PROMPTS: dict[str, PromptConfig] = {
    "detailed_summary": {
        "model": "openai/gpt-4o",
        "system": "You are an analyst.",
        "user": english_summary_user,
    },
    ...
}
```

Set env: `PROMPTS_MODULE=backend.config.prompts_custom`

## Trade-offs

| Pros | Cons |
|------|------|
| Full Python flexibility | Not human-readable as YAML |
| Type hints work | No native multi-file support |
| Easy to test individual functions | Custom prompts need Python files |
| No extra dependencies | |
| IDE autocomplete support | |

## Implementation Results

- Created `backend/config/__init__.py`
- Created `backend/config/prompts.py` (84 lines)
- Updated `backend/summarizer.py` (removed 4 prompt constants, now uses `get_prompt()`)
- Added `PROMPTS_MODULE` to `.env.example`

All prompts verified working:
- `detailed_summary`: trinity-large-preview:free
- `translate`: trinity-large-preview:free
- `three_line_summary`: trinity-mini:free
- `bullet_summary`: trinity-mini:free
