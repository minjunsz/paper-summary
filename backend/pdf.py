import io
import httpx
import fitz


async def download_pdf(arxiv_id: str) -> bytes:
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)
