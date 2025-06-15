from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.services.market_data import get_price
from app.services.portfolio import add_coin, portfolio
from fastapi.responses import RedirectResponse



app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "portfolio": portfolio
    })


@app.post("/buy")
async def buy_coin(request: Request, symbol: str = Form(...), amount: float = Form(...)):
    price = await get_price(symbol)
    add_coin(symbol, amount, price)
    return RedirectResponse(url="/", status_code=303)

