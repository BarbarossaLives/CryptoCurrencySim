import httpx

async def get_price(symbol: str) -> float:
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol.upper()}&tsyms=USD"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    data = response.json()
    return data["USD"]
