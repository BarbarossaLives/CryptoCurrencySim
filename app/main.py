from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form
from app.services.market_data import get_price
from app.services.portfolio import add_coin
from fastapi.responses import RedirectResponse, HTMLResponse
from app.models.db import Base, engine
from app.models.game import GameSession, Achievement, GameLeaderboard
from app.services.portfolio import get_portfolio
from app.services.portfolio import log_transaction
from app.services.portfolio import get_transactions
from app.services.llm_service import llm_service
from app.services.game_service import game_service
from app.models.game import GameMode
from fastapi import HTTPException
from fastapi import Form
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


app = FastAPI()
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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

    # Update game progress
    portfolio_data = await get_portfolio()
    game_service.update_game_progress(portfolio_data, {"profit": 0})

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

    # Update game progress
    portfolio_data = await get_portfolio()
    game_service.update_game_progress(portfolio_data, {"profit": usd_amount})

    return RedirectResponse(url="/", status_code=303)



@app.get("/assistant")
async def assistant_page(request: Request):
    return templates.TemplateResponse("assistant.html", {"request": request, "response": None})

@app.post("/assistant")
async def assistant_query(request: Request, question: str = Form(...)):
    portfolio_data = await get_portfolio()
    transactions = get_transactions()
    game_stats = game_service.get_game_stats()

    # Get AI-powered response with game context
    response = await llm_service.get_trading_advice(question, portfolio_data, transactions, game_stats)

    # Record AI interaction for game
    if game_stats:
        game_service.record_ai_interaction(followed_suggestion=True)

    return templates.TemplateResponse("assistant.html", {
        "request": request,
        "response": response,
        "question": question,
        "game_stats": game_stats
    })

@app.get("/transactions")
def transactions_page(request: Request):
    txs = get_transactions()
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "transactions": txs
    })

@app.get("/visualize", response_class=HTMLResponse)
async def visualize_portfolio(request: Request):
    portfolio_data = await get_portfolio()
    return templates.TemplateResponse("visualize.html", {
        "request": request,
        "portfolio": portfolio_data
    })


@app.get("/game", response_class=HTMLResponse)
async def game_dashboard(request: Request):
    game_stats = game_service.get_game_stats()
    portfolio_data = await get_portfolio()

    return templates.TemplateResponse("game.html", {
        "request": request,
        "game_stats": game_stats,
        "portfolio": portfolio_data
    })


@app.post("/game/start")
async def start_new_game(
    request: Request,
    player_name: str = Form("Anonymous Trader"),
    mode: str = Form("roi_target"),
    difficulty: str = Form("Normal")
):
    # Convert string mode to enum
    game_mode = GameMode.ROI_TARGET
    if mode == "net_worth_target":
        game_mode = GameMode.NET_WORTH_TARGET
    elif mode == "time_challenge":
        game_mode = GameMode.TIME_CHALLENGE

    # Start new game
    game_service.start_new_game(player_name, game_mode, difficulty)

    return RedirectResponse(url="/game", status_code=303)


@app.get("/game/leaderboard", response_class=HTMLResponse)
async def game_leaderboard(request: Request):
    leaderboard = game_service.get_leaderboard(limit=20)

    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "leaderboard": leaderboard
    })

