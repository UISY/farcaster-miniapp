from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import requests
import time

app = FastAPI()

# Besucherzähler
visitors = 0

# ETH Preis Cache
last_price = None
last_update = 0

def fetch_eth_price():
    """
    Holt den aktuellen Ethereum-Preis von CoinGecko.
    Cached den Wert 30 Sekunden, um 429 Fehler zu vermeiden.
    """
    global last_price, last_update
    now = time.time()

    if last_price is None or (now - last_update) > 30:
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "ethereum", "vs_currencies": "usd"}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            last_price = data["ethereum"]["usd"]
            last_update = now
        except Exception as e:
            print("⚠️ Fehler bei CoinGecko:", e)
            if last_price is None:
                last_price = 0
    return last_price


@app.get("/", response_class=HTMLResponse)
def home():
    global visitors
    visitors += 1

    html_content = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Ethereum MiniApp</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f5f6fa;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .logo, .price-box {
                cursor: pointer;
                text-align: center;
            }
            .logo img {
                width: 150px;
                height: auto;
            }
            .price {
                font-size: 42px;
                font-weight: bold;
            }
            .visitors {
                margin-top: 10px;
                font-size: 18px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div id="content" class="logo" onclick="toggleView()">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/6f/Ethereum-icon-purple.svg" alt="Ethereum Logo">
        </div>

        <script>
            let showingPrice = false;
            async function toggleView() {
                const content = document.getElementById("content");
                if (showingPrice) {
                    // Zurück zum Logo
                    content.className = "logo";
                    content.innerHTML = '<img src="https://upload.wikimedia.org/wikipedia/commons/6/6f/Ethereum-icon-purple.svg" alt="Ethereum Logo">';
                    showingPrice = false;
                } else {
                    // ETH-Preis laden
                    try {
                        const res = await fetch('/price');
                        const data = await res.json();
                        content.className = "price-box";
                        content.innerHTML = `
                            <div class="price">$${data.price}</div>
                            <div class="visitors">Besucher: ${data.visitors}</div>
                        `;
                        showingPrice = true;
                    } catch (err) {
                        content.innerHTML = "<div>Fehler beim Laden des Preises</div>";
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/price", response_class=JSONResponse)
def get_price():
    price = fetch_eth_price()
    return {"price": price, "visitors": visitors}







