portfolio = []

def add_coin(symbol: str, amount: float, price: float):
    value = round(amount * price, 2)
    entry = {"symbol": symbol.upper(), "amount": amount, "price_usd": price, "value_usd": value}
    portfolio.append(entry)
