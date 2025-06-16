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
from fastapi import Form


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
async def buy_coin(request: Request, symbol: str = Form(...), usd_amount: float = Form(...)):
    symbol = symbol.upper()
    price = await get_price(symbol)
    coin_amount = usd_amount / price

    add_coin(symbol, coin_amount, price)
    log_transaction(symbol, coin_amount, price, "buy")
    return RedirectResponse(url="/", status_code=303)


@app.post("/sell")
async def sell_coin(request: Request, symbol: str = Form(...), usd_amount: float = Form(...)):
    symbol = symbol.upper()
    price = await get_price(symbol)
    coin_amount = usd_amount / price

    portfolio = await get_portfolio()
    coins = portfolio["coins"]

    matching = next((c for c in coins if c["symbol"] == symbol), None)
    if not matching or matching["amount"] < coin_amount:
        raise HTTPException(status_code=400, detail="Not enough holdings to sell.")

    add_coin(symbol, -coin_amount, price)
    log_transaction(symbol, -coin_amount, price, "sell")
    return RedirectResponse(url="/", status_code=303)



@app.get("/assistant")
async def assistant_page(request: Request):
    return templates.TemplateResponse("assistant.html", {"request": request, "response": None})

@app.post("/assistant")
async def assistant_query(request: Request, question: str = Form(...)):
    portfolio_data = await get_portfolio()

    response = "I'm not sure how to answer that yet."

    q = question.lower()

    if "roi" in q:
        response = f"Your overall ROI is {portfolio_data['overall_roi']}%."

    elif "best" in q or "top" in q:
        top = portfolio_data["top_gainer"]
        if top:
            response = f"Your top performing coin is {top['symbol']} with ROI of {top['roi']}%."

    elif "worst" in q or "loss" in q:
        low = portfolio_data["top_loser"]
        if low:
            response = f"Your worst performing coin is {low['symbol']} with ROI of {low['roi']}%."

    else:
        # Try coin-specific lookup
        for coin in portfolio_data["coins"]:
            if coin["symbol"].lower() in q:
                response = (
                    f"{coin['symbol']} has an ROI of {coin['roi']}%, "
                    f"current value: ${coin['current_value']}."
                )
                break

    return templates.TemplateResponse("assistant.html", {
        "request": request,
        "response": response
    })

@app.get("/transactions")
def transactions_page(request: Request):
    txs = get_transactions()
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "transactions": txs
    })

