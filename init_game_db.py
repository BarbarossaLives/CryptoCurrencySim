#!/usr/bin/env python3
"""
Initialize the game database tables
"""

from sqlalchemy import create_engine
from app.models.db import Base
from app.models.game import GameSession, Achievement, GameLeaderboard
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crypto.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    
    # Import all models to ensure they're registered
    from app.models.db import Coin, Transaction
    from app.models.game import GameSession, Achievement, GameLeaderboard
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print("Game tables:")
    print("  - game_sessions")
    print("  - achievements") 
    print("  - game_leaderboard")
    print("\nExisting tables:")
    print("  - coins")
    print("  - transactions")

if __name__ == "__main__":
    init_db()
