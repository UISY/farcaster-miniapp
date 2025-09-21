from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import requests, time

app = FastAPI()

# --- Besucherzähler (einfach, im Speicher; reset bei Neustart/Deploy) ---
visitors = 0

# --- Preis-Cache gegen Rate-Limit ---
_last_price = None
_last_update = 0  # epoch seconds

def fetch_eth_price():
    """ETH-USD von CoinGecko, mit 30s Cache & robustem Fallback."""
    global _last_price, _last_update
    now = time.time()

    # Nur alle 30s extern anfragen
    if _last_price is None or (now - _last_update) > 30:
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "ethereum", "vs_currencies": "usd"}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            _last_price = float(data["ethereum"]["usd"])
            _last_update = now
        except Exception as e:
            # Bei Fehler: letzten bekannten Wert behalten; wenn keiner, 0.0
            print("⚠️ CoinGecko-Fehler:", e)
            if _last_price is None:
                _last_price = 0.0
    return _last_price


@app.get("/", response_class=HTMLResponse)
def home():
    global visitors
    visitors += 1  # zählt Seitenaufrufe (nur unter Preis anzeigen)

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <title>Ethereum MiniApp</title>
  <style>
    :root {{
      --bg:#f4f4f9; --text:#1f2937; --up:#16a34a; --down:#dc2626;
    }}
    html,body {{ height:100%; margin:0; }}
    body {{
      display:flex; align-items:center; justify-content:center;
      background:var(--bg);
      font-family: "Arial Black", Arial, Helvetica, sans-serif;
      color:var(--text);
    }}
    .wrap {{ text-align:center; user-select:none; }}
    #logo {{
      width: 160px; height:auto; display:block; margin:0 auto;
    }}
    #panel {{ display:none; }}
    #price {{
      font-size: clamp(32px,7vw,64px);
      font-weight: 700; margin: 0 0 8px 0;
    }}
    #vis {{ font-size: clamp(14px,4vw,20px); color:#6b7280; margin:0; }}

    @keyframes flashUp   {{ 0%{{color:var(--up)}}   100%{{color:var(--text)}} }}
    @keyframes flashDown {{ 0%{{color:var(--down)}} 100%{{color:var(--text)}} }}
  </style>
</head>
<body>
  <div class="wrap" id="wrap">
    <!-- Start: nur Logo -->
    <img id="logo"
         src="https://assets.coingecko.com/coins/images/279/large/ethereum.png?1696501628"
         onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/6/6f/Ethereum-icon-purple.svg'"
         alt="Ethereum" />

    <!-- Preis-Panel (versteckt bis zum Klick) -->
    <div id="panel">
      <div id="price">$0.00</div>
      <p id="vis">👥 {visitors} Besucher</p>
    </div>
  </div>

  <script>
    let showing = false;
    let timerId = null;
    let lastPrice = null;

    const wrap  = document.getElementById('wrap');
    const logo  = document.getElementById('logo');
    const panel = document.getElementById('panel');
    const priceEl = document.getElementById('price');
    const visEl = document.getElementById('vis');

    // Toggle auf JEDEN Klick im zentralen Bereich
    wrap.addEventListener('click', async () => {{
      showing = !showing;
      if (showing) {{
        // Logo aus, Panel an
        logo.style.display = 'none';
        panel.style.display = 'block';

        await updatePrice();                // sofort
        if (!timerId) timerId = setInterval(updatePrice, 5000); // dann alle 5s
      }} else {{
        // Panel aus, Logo an
        panel.style.display = 'none';
        logo.style.display = 'block';
        if (timerId) {{ clearInterval(timerId); timerId = null; }}
      }}
    }});

    async function updatePrice() {{
      try {{
        const res = await fetch('/price');
        const data = await res.json();
        const newPrice = Number(data.price || 0);

        // Animation je nach Bewegung
        if (lastPrice !== null) {{
          if (newPrice > lastPrice) {{
            priceEl.style.animation = 'flashUp 0.5s';
          }} else if (newPrice < lastPrice) {{
            priceEl.style.animation = 'flashDown 0.5s';
          }} else {{
            priceEl.style.animation = 'none';
          }}
        }}
        lastPrice = newPrice;

        // Formatierte Ausgabe
        priceEl.textContent = new Intl.NumberFormat('en-US', {{
          style: 'currency', currency: 'USD', maximumFractionDigits: 2
        }}).format(newPrice);

        // Besucherzahl wird nur im Panel gezeigt (steht schon drin)
        // visEl bleibt sichtbar, Logo-Ansicht zeigt sie nicht
      }} catch (e) {{
        console.error(e);
      }}
    }}
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/price", response_class=JSONResponse)
def price():
    p = fetch_eth_price()
    return {"price": p}







