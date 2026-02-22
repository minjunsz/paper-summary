import logging
from openai import AsyncOpenAI
from backend.llm import get_openrouter_client
from backend.config.prompts import get_prompt
from backend.utils import retry

logger = logging.getLogger(__name__)


@retry(max_attempts=3, delay=2.0)
async def generate_detailed_summary(paper_text: str) -> str:
    client = get_openrouter_client()
    config = get_prompt("detailed_summary")
    response = await client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": config["system"]},
            {"role": "user", "content": config["user"](paper_text=paper_text)},
        ],
    )
    return response.choices[0].message.content or ""


@retry(max_attempts=3, delay=2.0)
async def translate_to_korean(text: str) -> str:
    client = get_openrouter_client()
    config = get_prompt("translate")
    response = await client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": config["system"]},
            {"role": "user", "content": config["user"](text=text)},
        ],
    )
    return response.choices[0].message.content or ""


@retry(max_attempts=3, delay=2.0)
async def generate_three_line_summary(detailed_summary: str) -> str:
    client = get_openrouter_client()
    config = get_prompt("three_line_summary")
    response = await client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": config["system"]},
            {
                "role": "user",
                "content": config["user"](detailed_summary=detailed_summary),
            },
        ],
    )
    return response.choices[0].message.content or ""


@retry(max_attempts=3, delay=2.0)
async def generate_bullet_summary(detailed_summary: str) -> list[str]:
    client = get_openrouter_client()
    config = get_prompt("bullet_summary")
    content = ""

    for attempt in range(3):
        response = await client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": config["system"]},
                {
                    "role": "user",
                    "content": config["user"](detailed_summary=detailed_summary),
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


LENGTH_WARNING_THRESHOLD = 100_000


async def generate_summaries(
    paper_text: str,
) -> tuple[str, str, list[str], str | None]:
    warning = None

    if len(paper_text) > LENGTH_WARNING_THRESHOLD:
        warning = (
            f"⚠️ Paper is long ({len(paper_text):,} chars), summary may be incomplete"
        )

    try:
        detailed = await generate_detailed_summary(paper_text)
        detailed_korean = await translate_to_korean(detailed)
        three_line = await generate_three_line_summary(detailed_korean)
        bullet = await generate_bullet_summary(detailed_korean)
    except Exception as e:
        error_msg = str(e)
        if "context" in error_msg.lower() or "tokens" in error_msg.lower():
            warning = f"⚠️ Context limit exceeded: {error_msg}"
        raise

    return detailed_korean, three_line, bullet, warning
