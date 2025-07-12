import yfinance as yf
import pandas as pd
import requests
import time
import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "SMA Telegram Bot is running!"

def send_alert(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# Top forex and crypto symbols with CHFJPY fixed
symbols = [
    "USDJPY=X", "GBPJPY=X", "USDCAD=X", "CHFJPY=X", "CADJPY=X", "EURGBP=X",
    "BTC-USD", "ETH-USD", "USDT-USD", "BNB-USD", "SOL-USD",
    "XRP-USD", "DOGE-USD", "TON11419-USD", "ADA-USD", "AVAX-USD",
    "GLD"
]

# ✅ 15-minute candles for faster testing
interval = "15m"
sma1_len = 7
sma2_len = 20
sma3_len = 60
last_alert_time = {}

def check_sma_strategy(symbol):
    global last_alert_time
    try:
        print(f"📥 Downloading data for {symbol}...")
        df = yf.download(symbol, interval=interval, period='5d', auto_adjust=False)

        df['sma1'] = df['Close'].rolling(sma1_len).mean()
        df['sma2'] = df['Close'].rolling(sma2_len).mean()
        df['sma3'] = df['Close'].rolling(sma3_len).mean()

        if df[['sma1', 'sma2', 'sma3']].isnull().any().any():
            print(f"⚠️ Skipping {symbol}: Not enough SMA data (NaNs still present)")
            return

        last = df.iloc[-1]
        prev = df.iloc[-2]
        current_time = df.index[-1]

        if last_alert_time.get(symbol) == current_time:
            print(f"⏩ Already alerted for {symbol} at {current_time}, skipping.")
            return

        sma1_now, sma2_now, sma3_now = last['sma1'], last['sma2'], last['sma3']
        sma1_prev, sma2_prev = prev['sma1'], prev['sma2']

        above = sma1_now > sma3_now and sma2_now > sma3_now
        below = sma1_now < sma3_now and sma2_now < sma3_now
        crossed_up = sma1_prev < sma2_prev and sma1_now > sma2_now
        crossed_down = sma1_prev > sma2_prev and sma1_now < sma2_now
        crossed = crossed_up or crossed_down

        if crossed and (above or below):
            direction = "📈 ABOVE" if above else "📉 BELOW"
            alert_msg = f"🔔 {symbol}\nSMA 7/20 crossover {direction} SMA 60 on 15M candle @ {current_time}"
            print(f"🚨 Triggered: {alert_msg}")
            send_alert(alert_msg)
            last_alert_time[symbol] = current_time
        else:
            print(f"✅ No crossover for {symbol} at {current_time}")

    except Exception as e:
        print(f"❌ Error for {symbol}: {e}")

def run_bot_loop():
    while True:
        print(f"\n🔄 Checking {len(symbols)} symbols at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for symbol in symbols:
            check_sma_strategy(symbol)
        print("⏳ Sleeping for 3 minutes...\n")
        time.sleep(180)

# ✅ Launch bot loop and Flask server correctly
if __name__ == "__main__":
    threading.Thread(target=run_bot_loop).start()
    send_alert("🔄 Bot restarted and is now live. Monitoring SMA 7/20 crossovers vs SMA 60 on 15M candles.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
