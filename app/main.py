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




app = FastAPI()
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def homepage(request: Request):
    coins = get_portfolio()
    transactions = get_transactions()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "portfolio": coins,
        "transactions": transactions
    })



@app.post("/buy")
async def buy_coin(request: Request, symbol: str = Form(...), amount: float = Form(...)):
    price = await get_price(symbol)
    add_coin(symbol, amount, price)
    log_transaction(symbol, amount, price, "buy")
    return RedirectResponse(url="/", status_code=303)

