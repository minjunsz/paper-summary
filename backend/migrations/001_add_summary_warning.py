"""Migration 001: Add summary_warning column to papers table

Run with: python -m backend.migrations.001_add_summary_warning
"""

from sqlalchemy import create_engine, text


def migrate():
    engine = create_engine("sqlite:///papers.db")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE papers ADD COLUMN summary_warning TEXT"))
        conn.commit()
    print("Migration 001 complete: added summary_warning column")


if __name__ == "__main__":
    migrate()
