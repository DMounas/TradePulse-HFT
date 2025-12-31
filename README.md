# TradePulse: Real-Time High-Frequency Trading Engine

TradePulse is a distributed financial intelligence platform designed to ingest, analyze, and visualize cryptocurrency market data in real-time.

## 🚀 Key Features

*   **High-Frequency Ingestion:** Consumes live trade data via Binance WebSockets (AsyncIO).
*   **Statistical Anomaly Detection:** Real-time Z-Score calculation using **NumPy** to detect market volatility (2-sigma events).
*   **Persistent State Management:** Asynchronous storage of trade history using **PostgreSQL** and **SQLAlchemy**.
*   **Interactive Terminal:** A React.js dashboard with live Recharts visualization and sub-millisecond updates.

## 🛠️ Tech Stack

*   **Backend:** Python 3.10+, FastAPI, AsyncPG, NumPy, Websockets.
*   **Frontend:** React (Vite), Recharts, Axios.
*   **Database:** PostgreSQL (Async).
*   **DevOps:** Docker support (Ready for containerization).

## 🏃‍♂️ How to Run

1.  **Backend:**
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

2.  **Frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## 📸 Screenshots
*<img width="1275" height="622" alt="Screenshot 2025-12-31 151120" src="https://github.com/user-attachments/assets/ec337d8e-234a-4380-badd-3e701c0de57a" />*
