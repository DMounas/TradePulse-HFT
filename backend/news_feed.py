import requests
import time
import random

# This script simulates the "Real World" generating news
API_URL = "http://127.0.0.1:8000/ingest/news"

tickers = ["BTC", "ETH", "AAPL", "TSLA", "GOOGL", "NVDA"]

templates = [
    ("surge hits record high", "POSITIVE"),
    ("faces massive lawsuit", "NEGATIVE"),
    ("announces new product line", "POSITIVE"),
    ("price drops significantly", "NEGATIVE"),
    ("CEO steps down", "NEGATIVE"),
    ("quarterly profits exceed expectations", "POSITIVE"),
    ("remains stable", "NEUTRAL"),
    ("market bulls are buying", "POSITIVE"),
    ("bears take control of market", "NEGATIVE")
]

print("🚀 Starting NEXUS Data Feed...")

while True:
    ticker = random.choice(tickers)
    phrase, _ = random.choice(templates)
    headline = f"{ticker} {phrase} amid market volatility."
    
    payload = {
        "ticker": ticker,
        "headline": headline
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        print(f"📡 Sent: {headline} [{response.status_code}]")
    except Exception as e:
        print("❌ Error sending data. Is Backend running?")
    
    # Send a new headline every 1 to 3 seconds
    time.sleep(random.uniform(1, 3))