from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import requests, time

app = FastAPI()

# --- Besucherzähler (im Speicher; reset bei Neustart/Deploy) ---
visitors = 0

# --- Preis-Cache gegen Rate-Limit ---
_last_price = None
_last_update = 0  # epoch seconds

def fetch_eth_price():
    """ETH-USD von CoinGecko, mit 30s Cache & Fallback."""
    global _last_price, _last_update
    now = time.time()

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
            print("⚠️ CoinGecko-Fehler:", e)
            if _last_price is None:
                _last_price = 0.0
    return _last_price

# ------------------------------
# Deine bestehende Web-App (/)
# ------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    global visitors
    visitors += 1

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
    <img id="logo"
         src="https://assets.coingecko.com/coins/images/279/large/ethereum.png?1696501628"
         alt="Ethereum" />

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

    wrap.addEventListener('click', async () => {{
      showing = !showing;
      if (showing) {{
        logo.style.display = 'none';
        panel.style.display = 'block';

        await updatePrice();
        if (!timerId) timerId = setInterval(updatePrice, 5000);
      }} else {{
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

        priceEl.textContent = new Intl.NumberFormat('en-US', {{
          style: 'currency', currency: 'USD', maximumFractionDigits: 2
        }}).format(newPrice);

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

# ------------------------------
# Neuer Teil: Farcaster Frame
# ------------------------------

@app.get("/frame", response_class=HTMLResponse)
def frame():
    vercel = "https://farcaster-miniapp-xaz5.vercel.app"  # deine Domain

    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta property="og:title" content="ETH MiniApp" />
        <meta property="og:image" content="{vercel}/static/eth.png" />
        <meta name="fc:frame" content="vNext" />
        <meta name="fc:frame:image" content="{vercel}/static/eth.png" />
        <meta name="fc:frame:button:1" content="Preis anzeigen" />
        <meta name="fc:frame:post_url" content="{vercel}/api/frame" />
      </head>
      <body></body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/api/frame")
async def frame_interaction():
    global visitors
    visitors += 1
    price = fetch_eth_price()

    return {
        "image": f"https://dummyimage.com/600x400/ffffff/000000.png&text=Ethereum+${price:.2f}+👥{visitors}",
        "buttons": [{"label": "Zurück", "action": "post"}],
        "post_url": "https://farcaster-miniapp-xaz5.vercel.app/api/frame_back"
    }

@app.post("/api/frame_back")
async def frame_back():
    return {
        "image": "https://farcaster-miniapp-xaz5.vercel.app/static/eth.png",
        "buttons": [{"label": "Preis anzeigen", "action": "post"}],
        "post_url": "https://farcaster-miniapp-xaz5.vercel.app/api/frame"
    }
