# ---------- app.py ----------
from flask import Flask, request, jsonify
import os, time, hmac, hashlib, json, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("BYBIT_KEY")
API_SEC = os.getenv("BYBIT_SECRET")
SYMBOL  = os.getenv("SYMBOL", "BTCUSDT")
BASE    = "https://api.bybit.com"

def sign(ts, method, path, body=""):
    payload = f"{ts}{method}{path}{body}"
    return hmac.new(API_SEC.encode(), payload.encode(),
                    hashlib.sha256).hexdigest()

def bybit_req(method, path, payload=None):
    body = json.dumps(payload or {})
    ts   = str(int(time.time()*1000))
    head = {"X-BAPI-API-KEY":API_KEY,
            "X-BAPI-TIMESTAMP":ts,
            "X-BAPI-SIGN":sign(ts,method,path,body),
            "Content-Type":"application/json"}
    return requests.request(method, BASE+path, headers=head, data=body).json()

def market(side, qty, reduce=False):
    p = {"category":"linear","symbol":SYMBOL,"side":side,
         "orderType":"Market","qty":str(qty),
         "reduceOnly":reduce}
    return bybit_req("POST","/v5/order/create",p)

app = Flask(__name__)

# --- 헬스체크용 기본 경로 ---
@app.get("/")
def root():
    return "alive", 200

# --- TradingView 웹훅 경로 ---
@app.route("/hook", methods=["GET", "POST"])
def hook():
    if request.method == "GET":          # Render 헬스체크
        return "hook alive", 200

    txt = request.data.decode().lower().strip()
    parts = txt.split()
    if len(parts) < 3:
        return "format err", 400
    side   = "BUY" if parts[0].startswith("buy") else "SELL"
    qty    = parts[1]
    reduce = "reduceonly=true" in txt
    rsp    = market(side, qty, reduce)
    return jsonify(rsp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
# --------------------------------
