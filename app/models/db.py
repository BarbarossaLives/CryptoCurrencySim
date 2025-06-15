from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import DateTime
from datetime import datetime


DATABASE_URL = "sqlite:///./crypto.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Coin(Base):
    __tablename__ = "coins"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    amount = Column(Float)
    price_usd = Column(Float)
    value_usd = Column(Float)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    amount = Column(Float)
    price_usd = Column(Float)
    type = Column(String)  # "buy" or "sell"
    timestamp = Column(DateTime, default=datetime.utcnow)