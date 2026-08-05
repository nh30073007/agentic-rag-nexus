"""Initialize database tables."""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.base import Base
from app.db.session import engine


def init_db():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")


if __name__ == "__main__":
    init_db()