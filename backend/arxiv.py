import re
import httpx
from pydantic import BaseModel


class ArxivMetadata(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str


def extract_arxiv_id(input_str: str) -> str | None:
    input_str = input_str.strip()
    url_pattern = r"(?:arxiv\.org/abs/|arxiv\.org/pdf/)?(\d+\.\d+)"
    match = re.search(url_pattern, input_str)
    if match:
        return match.group(1)
    if re.match(r"^\d+\.\d+$", input_str):
        return input_str
    return None


async def fetch_arxiv_metadata(arxiv_id: str) -> ArxivMetadata:
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        xml_text = response.text

    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_text)
    entry = root.find("{http://www.w3.org/2005/Atom}entry")
    if entry is None:
        raise ValueError(f"No entry found for arxiv_id: {arxiv_id}")

    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
    if title_elem is None or title_elem.text is None:
        raise ValueError(f"No title found for arxiv_id: {arxiv_id}")
    title = title_elem.text.strip()
    title = re.sub(r"\s+", " ", title)

    abstract_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
    if abstract_elem is None or abstract_elem.text is None:
        raise ValueError(f"No abstract found for arxiv_id: {arxiv_id}")
    abstract = abstract_elem.text.strip()
    abstract = re.sub(r"\s+", " ", abstract)

    authors = []
    for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
        name = author.find("{http://www.w3.org/2005/Atom}name")
        if name is not None and name.text is not None:
            authors.append(name.text.strip())

    return ArxivMetadata(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
    )
