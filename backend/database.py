import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arxiv_id = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(1000), nullable=False)
    authors = Column(Text)
    abstract = Column(Text)
    detailed_summary = Column(Text)
    three_line_summary = Column(Text)
    bullet_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

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
