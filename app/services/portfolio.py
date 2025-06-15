from app.models.db import Coin, SessionLocal
from app.models.db import Transaction

def add_coin(symbol: str, amount: float, price: float):
    value = round(amount * price, 2)
    db = SessionLocal()
    coin = Coin(
        symbol=symbol.upper(),
        amount=amount,
        price_usd=price,
        value_usd=value
    )
    db.add(coin)
    db.commit()
    db.refresh(coin)
    db.close()

def get_portfolio():
    db = SessionLocal()
    coins = db.query(Coin).all()
    db.close()
    return coins

def log_transaction(symbol: str, amount: float, price: float, tx_type: str):
    db = SessionLocal()
    tx = Transaction(
        symbol=symbol.upper(),
        amount=amount,
        price_usd=price,
        type=tx_type
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.close()

def get_transactions():
    db = SessionLocal()
    txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    db.close()
    return txs
