import json
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, sessionmaker

Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    arxiv_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authors: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    detailed_summary: Mapped[str | None] = mapped_column(Text)
    three_line_summary: Mapped[str | None] = mapped_column(Text)
    bullet_summary: Mapped[str | None] = mapped_column(Text)
    summary_warning: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def get_authors_list(self) -> list[str]:
        if not self.authors:
            return []
        try:
            return json.loads(self.authors)
        except json.JSONDecodeError:
            return []

    def get_bullet_summary_list(self) -> list[str]:
        if not self.bullet_summary:
            return []
        try:
            return json.loads(self.bullet_summary)
        except json.JSONDecodeError:
            return []


engine = create_engine("sqlite:///papers.db", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
