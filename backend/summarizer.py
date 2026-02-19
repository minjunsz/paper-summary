import json
import asyncio
from openai import AsyncOpenAI
from backend.llm import get_openrouter_client
from backend.config import get_settings
from backend.utils import retry


DETAILED_PROMPT = """You are an expert academic paper analyst. Analyze the following paper thoroughly and provide a detailed summary in Korean. Cover all these aspects:

1. tackling problem (limitations of previous methods)
2. core idea
3. key contributions
4. methodologies (including details)
5. analysis or limitations
6. any other paper specific noteworthy points

Provide your analysis in Korean:"""

THREE_LINE_PROMPT = """Based on the following detailed paper analysis, summarize it into exactly 3 lines in Korean. Each line should be a complete thought:

{detailed_summary}

Provide exactly 3 lines, nothing more:"""

BULLET_PROMPT = """Based on the following detailed paper analysis, create a brief summary using bullet points in Korean:

{detailed_summary}

Provide 3-5 bullet points:"""


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
    return response.choices[0].message.content


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
    return response.choices[0].message.content


@retry(max_attempts=3, delay=2.0)
async def generate_bullet_summary(detailed_summary: str) -> list[str]:
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
                "content": BULLET_PROMPT.format(detailed_summary=detailed_summary),
            },
        ],
    )
    content = response.choices[0].message.content
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    return lines


async def generate_summaries(paper_text: str) -> tuple[str, str, list[str]]:
    detailed = await generate_detailed_summary(paper_text)
    three_line = await generate_three_line_summary(detailed)
    bullet = await generate_bullet_summary(detailed)
    return detailed, three_line, bullet
