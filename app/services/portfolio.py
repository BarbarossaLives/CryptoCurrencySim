from app.models.db import Coin, SessionLocal
from app.models.db import Transaction
from sqlalchemy import func
from app.services.market_data import get_price
import asyncio

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

async def get_portfolio():
    db = SessionLocal()
    result = db.query(
        Coin.symbol,
        func.sum(Coin.amount).label("total_amount"),
        func.avg(Coin.price_usd).label("avg_price"),
        func.sum(Coin.value_usd).label("total_value")
    ).group_by(Coin.symbol).all()
    db.close()

    portfolio = []

    for row in result:
        current_price = await get_price(row.symbol)
        current_value = round(row.total_amount * current_price, 2)
        roi = round(((current_price - row.avg_price) / row.avg_price) * 100, 2)

        portfolio.append({
            "symbol": row.symbol,
            "amount": round(row.total_amount, 8),
            "price_usd": round(row.avg_price, 2),
            "value_usd": round(row.total_value, 2),
            "current_price": round(current_price, 2),
            "current_value": current_value,
            "roi": roi
        })

    # After portfolio list is built
    total_invested = sum(c["value_usd"] for c in portfolio)
    total_current = sum(c["current_value"] for c in portfolio)

    overall_roi = (
    round(((total_current - total_invested) / total_invested) * 100, 2)
    if total_invested > 0 else 0.0
)

    top_gainer = max(portfolio, key=lambda c: c["roi"], default=None)
    top_loser = min(portfolio, key=lambda c: c["roi"], default=None)


    return {
        "coins": portfolio,
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "overall_roi": overall_roi,
        "top_gainer": top_gainer,
        "top_loser": top_loser
    }


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
