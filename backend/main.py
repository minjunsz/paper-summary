import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, Paper
from backend.arxiv import extract_arxiv_id, fetch_arxiv_metadata
from backend.pdf import download_pdf, extract_text_from_pdf
from backend.summarizer import generate_summaries
from backend.utils import retry

app = FastAPI(title="Paper Summary API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PaperMetadata(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str


class PaperSummary(BaseModel):
    detailed_summary: str
    three_line_summary: str
    bullet_summary: list[str]
    created_at: datetime


class PaperResponse(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str | None = None
    detailed_summary: str | None = None
    three_line_summary: str | None = None
    bullet_summary: list[str] | None = None
    created_at: datetime | None = None


class PaperListResponse(BaseModel):
    papers: list[PaperResponse]


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/paper/{arxiv_id}/metadata", response_model=PaperMetadata)
@retry(max_attempts=3, delay=2.0)
async def get_paper_metadata(arxiv_id: str):
    extracted_id = extract_arxiv_id(arxiv_id)
    if not extracted_id:
        raise HTTPException(status_code=400, detail="Invalid arXiv ID")
    try:
        metadata = await fetch_arxiv_metadata(extracted_id)
        return metadata
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch metadata: {str(e)}"
        )


@app.post("/api/paper/{arxiv_id}/summarize", response_model=PaperResponse)
async def summarize_paper(arxiv_id: str, db: Session = Depends(get_db)):
    extracted_id = extract_arxiv_id(arxiv_id)
    if not extracted_id:
        raise HTTPException(status_code=400, detail="Invalid arXiv ID")

    existing = db.query(Paper).filter(Paper.arxiv_id == extracted_id).first()
    if existing:
        return PaperResponse(
            arxiv_id=existing.arxiv_id,
            title=existing.title,
            authors=existing.get_authors_list(),
            abstract=existing.abstract or "",
            detailed_summary=existing.detailed_summary,
            three_line_summary=existing.three_line_summary,
            bullet_summary=existing.get_bullet_summary_list(),
            created_at=existing.created_at,
        )

    try:
        metadata = await fetch_arxiv_metadata(extracted_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch metadata: {str(e)}"
        )

    try:
        pdf_bytes = await download_pdf(extracted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")

    try:
        paper_text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

    try:
        detailed, three_line, bullet = await generate_summaries(paper_text)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {str(e)}"
        )

    paper = Paper(
        arxiv_id=extracted_id,
        title=metadata.title,
        authors=json.dumps(metadata.authors),
        abstract=metadata.abstract,
        detailed_summary=detailed,
        three_line_summary=three_line,
        bullet_summary=json.dumps(bullet),
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    return PaperResponse(
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        authors=paper.get_authors_list(),
        abstract=paper.abstract or "",
        detailed_summary=paper.detailed_summary,
        three_line_summary=paper.three_line_summary,
        bullet_summary=paper.get_bullet_summary_list(),
        created_at=paper.created_at,
    )


@app.get("/api/paper/{arxiv_id}", response_model=PaperResponse)
async def get_paper(arxiv_id: str, db: Session = Depends(get_db)):
    extracted_id = extract_arxiv_id(arxiv_id)
    if not extracted_id:
        raise HTTPException(status_code=400, detail="Invalid arXiv ID")

    paper = db.query(Paper).filter(Paper.arxiv_id == extracted_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return PaperResponse(
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        authors=paper.get_authors_list(),
        abstract=paper.abstract or "",
        detailed_summary=paper.detailed_summary,
        three_line_summary=paper.three_line_summary,
        bullet_summary=paper.get_bullet_summary_list(),
        created_at=paper.created_at,
    )


@app.get("/api/papers", response_model=PaperListResponse)
async def list_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).order_by(Paper.created_at.desc()).all()
    return PaperListResponse(
        papers=[
            PaperResponse(
                arxiv_id=p.arxiv_id,
                title=p.title,
                authors=p.get_authors_list(),
                abstract=p.abstract or "",
                detailed_summary=p.detailed_summary,
                three_line_summary=p.three_line_summary,
                bullet_summary=p.get_bullet_summary_list(),
                created_at=p.created_at,
            )
            for p in papers
        ]
    )
