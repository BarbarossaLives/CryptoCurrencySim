from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.services.market_data import get_price
from app.services.portfolio import add_coin
from fastapi.responses import RedirectResponse
from app.models.db import Base, engine
from app.services.portfolio import get_portfolio
from app.services.portfolio import log_transaction
from app.services.portfolio import get_transactions
from fastapi import HTTPException


app = FastAPI()
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def homepage(request: Request):
    portfolio_data = await get_portfolio()
    transactions = get_transactions()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "portfolio": portfolio_data["coins"],
        "total_invested": portfolio_data["total_invested"],
        "total_current": portfolio_data["total_current"],
        "overall_roi": portfolio_data["overall_roi"],
        "top_gainer": portfolio_data["top_gainer"],
        "top_loser": portfolio_data["top_loser"],
        "transactions": transactions
    })


@app.post("/buy")
async def buy_coin(request: Request, symbol: str = Form(...), amount: float = Form(...)):
    price = await get_price(symbol)
    add_coin(symbol, amount, price)
    log_transaction(symbol, amount, price, "buy")
    return RedirectResponse(url="/", status_code=303)

@app.post("/sell")
async def sell_coin(request: Request, symbol: str = Form(...), amount: float = Form(...)):
    symbol = symbol.upper()
    coins = await get_portfolio()

    # Check if user has enough
    matching = next((c for c in coins if c["symbol"] == symbol), None)
    if not matching or matching["amount"] < amount:
        raise HTTPException(status_code=400, detail="Not enough holdings to sell.")

    price = await get_price(symbol)
    add_coin(symbol, -amount, price)  # negative amount reduces holdings
    log_transaction(symbol, -amount, price, "sell")
    return RedirectResponse(url="/", status_code=303)
