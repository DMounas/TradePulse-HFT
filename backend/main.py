import asyncio
import json
import numpy as np
import structlog
import websockets
from contextlib import asynccontextmanager
from collections import deque
from datetime import datetime
import os
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- ASYNC POSTGRES IMPORTS ---
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime, select

# --- CONFIGURATION ---
logger = structlog.get_logger()
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "trading_platform")

# ⚠️ CHANGE 'password' TO YOUR REAL POSTGRES PASSWORD ⚠️
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- DATABASE SETUP ---
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- MODELS ---
class TradeRecord(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # BUY or SELL
    price = Column(Float)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- DEPENDENCY ---
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- IN-MEMORY STATE (For High Speed Access) ---
# In a real app, this would be in Redis
portfolio = {"usd": 100000.0, "btc": 0.0}
price_history = deque(maxlen=100)  # Keep last 100 prices for stats

# --- WEBSOCKET MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# --- ANALYTICS ENGINE (NumPy) ---
def calculate_anomaly(current_price):
    if len(price_history) < 20:
        return {"status": "CALIBRATING", "z_score": 0, "mean_price": current_price}

    data = np.array(price_history)
    mean = np.mean(data)
    std_dev = np.std(data)

    if std_dev == 0:
        return {"status": "STABLE", "z_score": 0, "mean_price": mean}

    z_score = (current_price - mean) / std_dev
    status = "NORMAL"
    if z_score > 2.0: status = "PUMP_DETECTED 🚀"
    elif z_score < -2.0: status = "DUMP_DETECTED 🔻"

    return {"status": status, "z_score": round(z_score, 2), "mean_price": round(mean, 2)}

# --- MARKET LISTENER (Binance) ---
async def listen_to_crypto_market():
    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(url) as ws:
        logger.info("connected_to_binance")
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if "p" in data:
                    price = float(data["p"])
                    qty = float(data["q"])
                    volume = price * qty
                    
                    price_history.append(price)
                    stats = calculate_anomaly(price)
                    
                    # Detect Whale (> $50k volume)
                    is_whale = volume > 50000

                    payload = {
                        "price": price,
                        "stats": stats,
                        "volume": volume,
                        "is_whale": is_whale,
                        "timestamp": datetime.now().isoformat()
                    }
                    await manager.broadcast(payload)
                    
            except Exception as e:
                logger.error("feed_error", error=str(e))
                await asyncio.sleep(5)

# --- APP LIFECYCLE ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create DB Tables asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Start Background Feed
    task = asyncio.create_task(listen_to_crypto_market())
    yield
    # 3. Cleanup
    task.cancel()

app = FastAPI(title="TradePulse Pro", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/portfolio")
async def get_portfolio():
    return portfolio

@app.get("/trade/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    # Fetch last 10 trades from Postgres
    result = await db.execute(select(TradeRecord).order_by(TradeRecord.timestamp.desc()).limit(10))
    trades = result.scalars().all()
    return trades

@app.post("/trade/execute")
async def execute_trade(type: str, price: float, db: AsyncSession = Depends(get_db)):
    global portfolio
    amount = 0.1 # Trade size 0.1 BTC
    
    # 1. Update In-Memory Portfolio
    if type == "BUY":
        cost = price * amount
        if portfolio["usd"] < cost:
            raise HTTPException(status_code=400, detail="Insufficient Funds")
        portfolio["usd"] -= cost
        portfolio["btc"] += amount
    elif type == "SELL":
        if portfolio["btc"] < amount:
            raise HTTPException(status_code=400, detail="Insufficient BTC")
        revenue = price * amount
        portfolio["btc"] -= amount
        portfolio["usd"] += revenue

    # 2. Async Persist to PostgreSQL
    new_trade = TradeRecord(type=type, price=price, amount=amount)
    db.add(new_trade)
    await db.commit()
    await db.refresh(new_trade)
    
    logger.info("trade_executed", type=type, price=price, new_balance=portfolio["usd"])
    
    return {"status": "executed", "trade_id": new_trade.id, "portfolio": portfolio}

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)