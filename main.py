import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

CMC_API_KEY = "bedbba74-aaab-49db-8db4-0717b6ee983d"

last_price = None  # globale Variable

@app.get("/miniapp", response_class=HTMLResponse)
def miniapp():
    global last_price

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "ETH", "convert": "USD"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        eth_price = data["data"]["ETH"]["quote"]["USD"]["price"]

        formatted_price = f"${eth_price:,.2f}"

        # Standardfarbe
        color = "black"
        if last_price is not None:
            if eth_price > last_price:
                color = "green"
            elif eth_price < last_price:
                color = "red"

        last_price = eth_price  # Preis speichern

        html_content = f"""
        <html>
            <head>
                <title>ETH Preis</title>
                <!-- 👇 Auto-Refresh alle 3 Sekunden -->
                <meta http-equiv="refresh" content="3">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        margin-top: 50px;
                        background-color: #f4f4f9;
                    }}
                    h1 {{
                        font-size: 48px;
                        color: {color};
                    }}
                    h2 {{
                        font-size: 36px;
                        color: {color};
                    }}
                    img {{
                        width: 80px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <img src="https://assets.coingecko.com/coins/images/279/large/ethereum.png" alt="Ethereum Logo">
                <h2>Ethereum (ETH)</h2>
                <h1>{formatted_price}</h1>
            </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(content=f"<p>Error: {str(e)}</p>", status_code=500)








