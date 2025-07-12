import yfinance as yf
import pandas as pd
import requests
import time
import os

# === CONFIG ===
symbols = [
    "JPY=X", "GBPJPY=X", "XAUUSD=X", "CAD=X",
    "CNYJPY=X", "CADJPY=X", "EURGBP=X",
    "BTC-USD", "ETH-USD", "USDT-USD", "BNB-USD", "SOL-USD",
    "XRP-USD", "DOGE-USD", "TON11419-USD", "ADA-USD", "AVAX-USD"
]

interval = "1h"
sma1_len = 7
sma2_len = 20
sma3_len = 60

telegram_token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("CHAT_ID")
last_alert_time = {}

def send_alert(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

def check_sma_strategy(symbol):
    global last_alert_time
    try:
        df = yf.download(symbol, interval=interval, period='2d')
        df.dropna(inplace=True)
        df['sma1'] = df['Close'].rolling(sma1_len).mean()
        df['sma2'] = df['Close'].rolling(sma2_len).mean()
        df['sma3'] = df['Close'].rolling(sma3_len).mean()
        last = df.iloc[-1]; prev = df.iloc[-2]
        current_time = df.index[-1]
        if last_alert_time.get(symbol) == current_time:
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
            alert_msg = f"🔔 {symbol}\nSMA 7/20 crossover {direction} SMA 60 on 1H candle @ {current_time}"
            send_alert(alert_msg)
            last_alert_time[symbol] = current_time
    except Exception as e:
        print(f"Error for {symbol}:", e)

while True:
    for sym in symbols:
        check_sma_strategy(sym)
    time.sleep(180)
