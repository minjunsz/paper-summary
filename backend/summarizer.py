import json
import asyncio
import logging
from openai import AsyncOpenAI
from backend.llm import get_openrouter_client
from backend.config import get_settings
from backend.utils import retry

logger = logging.getLogger(__name__)


DETAILED_PROMPT = """You are an expert academic paper analyst. Analyze the following paper thoroughly and provide a detailed summary in Korean. Cover all these aspects:

1. tackling problem (limitations of previous methods)
2. core idea
3. key contributions
4. methodologies (including details)
5. analysis or limitations
6. any other paper specific noteworthy points

Use markdown formatting (## for headers, **bold**, - for bullet lists). Provide your analysis in Korean:"""

THREE_LINE_PROMPT = """Based on the following detailed paper analysis, summarize it into exactly 3 lines in Korean. Use numbered list format (1., 2., 3.). Each line should be a complete thought:

{detailed_summary}

Provide exactly 3 lines in numbered format, nothing more:"""

BULLET_PROMPT = """Based on the following detailed paper analysis, create a brief summary using bullet points in Korean. Use markdown bullet list format (- item):

{detailed_summary}

Provide 3-5 bullet points in markdown format. 
IMPORTANT: Only return the bullet points, no introductory text or explanations. Start directly with the bullet points."""

TRANSLATE_PROMPT = """Translate the following academic paper analysis to Korean. 
- Keep all technical terminologies in English
- Translate all non-technical terms, sentences, and explanations to Korean
- Preserve all markdown formatting (## headers, **bold**, bullet points, etc.)

Original text:
{text}

Provide the Korean translation:"""


@retry(max_attempts=3, delay=2.0)
async def generate_detailed_summary(paper_text: str) -> str:
    client = get_openrouter_client()
    response = await client.chat.completions.create(
        model="arcee-ai/trinity-large-preview:free",
        messages=[
            {"role": "system", "content": "You are an expert academic paper analyst."},
            {"role": "user", "content": f"{DETAILED_PROMPT}\n\n{paper_text[:15000]}"},
        ],
    )
    return response.choices[0].message.content or ""


@retry(max_attempts=3, delay=2.0)
async def translate_to_korean(text: str) -> str:
    client = get_openrouter_client()
    response = await client.chat.completions.create(
        model="arcee-ai/trinity-large-preview:free",
        messages=[
            {
                "role": "system",
                "content": "You are a professional translator specializing in academic papers.",
            },
            {
                "role": "user",
                "content": TRANSLATE_PROMPT.format(text=text),
            },
        ],
    )
    return response.choices[0].message.content or ""


@retry(max_attempts=3, delay=2.0)
async def generate_three_line_summary(detailed_summary: str) -> str:
    client = get_openrouter_client()
    response = await client.chat.completions.create(
        model="arcee-ai/trinity-mini:free",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes in Korean.",
            },
            {
                "role": "user",
                "content": THREE_LINE_PROMPT.format(detailed_summary=detailed_summary),
            },
        ],
    )
    return response.choices[0].message.content or ""


@retry(max_attempts=3, delay=2.0)
async def generate_bullet_summary(detailed_summary: str) -> list[str]:
    client = get_openrouter_client()
    content = ""

    for attempt in range(3):
        response = await client.chat.completions.create(
            model="arcee-ai/trinity-mini:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes in Korean.",
                },
                {
                    "role": "user",
                    "content": BULLET_PROMPT.format(detailed_summary=detailed_summary),
                },
            ],
        )
        content = response.choices[0].message.content or ""

        # Filter to only include lines starting with "- " (markdown bullet format)
        lines = [
            line.strip()[2:].strip()
            for line in content.split("\n")
            if line.strip().startswith("- ")
        ]

        if lines:
            logger.info(
                f"Bullet summary generated successfully on attempt {attempt + 1}"
            )
            return lines

        logger.warning(
            f"No valid bullet points found on attempt {attempt + 1}, retrying..."
        )

    # Fallback: return all non-empty lines if still no valid bullets after 3 retries
    logger.warning("No valid bullet points found after 3 retries, using fallback")
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    return lines


async def generate_summaries(paper_text: str) -> tuple[str, str, list[str]]:
    detailed = await generate_detailed_summary(paper_text)
    detailed_korean = await translate_to_korean(detailed)
    three_line = await generate_three_line_summary(detailed_korean)
    bullet = await generate_bullet_summary(detailed_korean)
    return detailed_korean, three_line, bullet
