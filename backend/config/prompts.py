import os
from typing import Callable, TypedDict


class PromptConfig(TypedDict):
    model: str
    system: str
    user: Callable[..., str]


def detailed_summary_user(paper_text: str) -> str:
    return f"""You are an expert academic paper analyst. Analyze the following paper thoroughly and provide a detailed summary in Korean. Cover all these aspects:

1. tackling problem (limitations of previous methods)
2. core idea
3. key contributions
4. methodologies (including details)
5. analysis or limitations
6. any other paper specific noteworthy points

Use markdown formatting (## for headers, **bold**, - for bullet lists). Provide your analysis in Korean:

{paper_text}"""


def translate_user(text: str) -> str:
    return f"""Translate the following academic paper analysis to Korean. 
- Keep all technical terminologies in English
- Translate all non-technical terms, sentences, and explanations to Korean
- Preserve all markdown formatting (## headers, **bold**, bullet points, etc.)

Original text:
{text}

Provide the Korean translation:"""


def three_line_summary_user(detailed_summary: str) -> str:
    return f"""Based on the following detailed paper analysis, summarize it into exactly 3 lines in Korean. Use numbered list format (1., 2., 3.). Each line should be a complete thought:

{detailed_summary}

Provide exactly 3 lines in numbered format, nothing more:"""


def bullet_summary_user(detailed_summary: str) -> str:
    return f"""Based on the following detailed paper analysis, create a brief summary using bullet points in Korean. Use markdown bullet list format (- item):

{detailed_summary}

Provide bullet points in markdown format that capture the core ideas. The number of bullets should be whatever is needed for a compact but detailed summary - more than a 3-line summary but much more concise than the detailed analysis: 
IMPORTANT: Only return the bullet points, no introductory text or explanations. Start directly with the bullet points."""


PROMPTS: dict[str, PromptConfig] = {
    "detailed_summary": {
        "model": "arcee-ai/trinity-large-preview:free",
        "system": "You are an expert academic paper analyst.",
        "user": detailed_summary_user,
    },
    "translate": {
        "model": "arcee-ai/trinity-large-preview:free",
        "system": "You are a professional translator specializing in academic papers.",
        "user": translate_user,
    },
    "three_line_summary": {
        "model": "arcee-ai/trinity-mini:free",
        "system": "You are a helpful assistant that summarizes in Korean.",
        "user": three_line_summary_user,
    },
    "bullet_summary": {
        "model": "arcee-ai/trinity-mini:free",
        "system": "You are a helpful assistant that summarizes in Korean.",
        "user": bullet_summary_user,
    },
}


def get_prompt(name: str) -> PromptConfig:
    """Get prompt config by name. Supports custom prompts via PROMPTS_MODULE env var."""
    custom_module = os.getenv("PROMPTS_MODULE")
    if custom_module:
        import importlib

        module = importlib.import_module(custom_module)
        return module.PROMPTS[name]
    return PROMPTS[name]
