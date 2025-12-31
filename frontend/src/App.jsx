import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { AreaChart, Area, YAxis, ResponsiveContainer, ReferenceLine } from 'recharts';

function App() {
  const [data, setData] = useState([]);
  const [currentStats, setCurrentStats] = useState({ price: 0, stats: { status: "INIT", z_score: 0 } });
  const [trades, setTrades] = useState([]); 
  const [connection, setConnection] = useState("DISCONNECTED");
  const [portfolio, setPortfolio] = useState({ usd: 0, btc: 0 });
  const [history, setHistory] = useState([]);

  // Fetch initial data
  useEffect(() => {
    fetchPortfolio();
    fetchHistory();
  }, []);

  // WebSocket Connection
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws/stream");

    socket.onopen = () => setConnection("CONNECTED");
    socket.onclose = () => setConnection("DISCONNECTED");

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      setCurrentStats(payload);

      // Chart Data
      setData(prev => [...prev, {
        price: payload.price, 
        mean: payload.stats.mean_price,
        timestamp: new Date().toLocaleTimeString() 
      }].slice(-100)); // Keep last 100

      // Tape (Whales only or random sample)
      if (payload.is_whale || Math.random() > 0.95) {
        setTrades(prev => [{
          id: Math.random(),
          price: payload.price,
          volume: payload.volume,
          is_whale: payload.is_whale,
          time: new Date().toLocaleTimeString()
        }, ...prev].slice(0, 50));
      }
    };

    return () => socket.close();
  }, []);

  // API Calls
  const fetchPortfolio = async () => {
    const res = await axios.get('http://localhost:8000/portfolio');
    setPortfolio(res.data);
  };

  const fetchHistory = async () => {
    const res = await axios.get('http://localhost:8000/trade/history');
    setHistory(res.data);
  };

  const executeTrade = async (type) => {
    try {
      await axios.post(`http://localhost:8000/trade/execute?type=${type}&price=${currentStats.price}`);
      fetchPortfolio(); // Refresh UI
      fetchHistory();   // Refresh Table
    } catch (err) {
      alert("Trade Failed: " + err.response.data.detail);
    }
  };

  // Helper for Colors
  const getStatusColor = () => {
    const s = currentStats.stats.status;
    if (s && s.includes("PUMP")) return "#00ff41";
    if (s && s.includes("DUMP")) return "#ff0055";
    return "#333";
  };

  return (
    <div style={styles.dashboard}>
      
      {/* HEADER */}
      <header style={styles.header}>
        <div style={styles.logo}>TRADEPULSE <span style={styles.beta}>PRO</span></div>
        <div style={styles.marketStatus}>
          BINANCE FEED <span style={{color: connection === "CONNECTED" ? '#00ff41' : 'red'}}>● {connection}</span>
        </div>
      </header>

      <div style={styles.grid}>
        
        {/* LEFT: METRICS & TRADING */}
        <div style={styles.col}>
          {/* Live Stats */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>LIVE METRICS</div>
            <div style={styles.metricBox}>
              <div style={styles.label}>LAST PRICE</div>
              <div style={styles.bigValue}>${currentStats.price?.toLocaleString()}</div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>Z-SCORE (VOLATILITY)</div>
              <div style={{...styles.value, color: Math.abs(currentStats.stats.z_score) > 2 ? 'yellow' : '#888'}}>
                {currentStats.stats.z_score} σ
              </div>
            </div>
            <div style={{...styles.statusBadge, backgroundColor: getStatusColor()}}>
              {currentStats.stats.status}
            </div>
          </div>

          {/* Portfolio & Execution */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>EXECUTION TERMINAL</div>
            <div style={styles.metricBox}>
              <div style={styles.label}>AVAILABLE CASH</div>
              <div style={styles.value}>${portfolio.usd?.toLocaleString()}</div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>BTC HOLDINGS</div>
              <div style={styles.value}>{portfolio.btc?.toFixed(4)} BTC</div>
            </div>
            <div style={styles.btnRow}>
              <button style={styles.buyBtn} onClick={() => executeTrade("BUY")}>BUY 0.1</button>
              <button style={styles.sellBtn} onClick={() => executeTrade("SELL")}>SELL 0.1</button>
            </div>
          </div>
        </div>

        {/* CENTER: CHART */}
        <div style={styles.chartCol}>
          <div style={styles.card}>
            <div style={styles.cardTitle}>PRICE ACTION (REAL-TIME)</div>
            <div style={{flex: 1, minHeight: 0}}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00f2ea" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00f2ea" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <YAxis domain={['auto', 'auto']} hide />
                  <ReferenceLine y={currentStats.stats.mean_price} stroke="#555" strokeDasharray="3 3" />
                  <Area type="monotone" dataKey="price" stroke="#00f2ea" strokeWidth={2} fill="url(#colorPrice)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Trade History Table */}
          <div style={{...styles.card, flex: 0.5, marginTop: 20, overflow: 'hidden'}}>
            <div style={styles.cardTitle}>RECENT EXECUTIONS (POSTGRESQL)</div>
            <div style={{overflowY: 'auto', padding: 10}}>
              <table style={{width: '100%', fontSize: '0.8rem', textAlign: 'left', color: '#aaa'}}>
                <thead>
                  <tr><th>TYPE</th><th>PRICE</th><th>AMT</th><th>TIME</th></tr>
                </thead>
                <tbody>
                  {history.map(h => (
                    <tr key={h.id} style={{borderBottom: '1px solid #222'}}>
                      <td style={{color: h.type === "BUY" ? '#00ff41' : '#ff0055'}}>{h.type}</td>
                      <td>${h.price.toFixed(2)}</td>
                      <td>{h.amount}</td>
                      <td>{new Date(h.timestamp).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* RIGHT: TAPE */}
        <div style={styles.col}>
          <div style={{...styles.card, height: '100%'}}>
            <div style={styles.cardTitle}>MARKET TAPE (WHALE DETECTOR)</div>
            <div style={{overflowY: 'auto', flex: 1}}>
              {trades.map(t => (
                <div key={t.id} style={{...styles.tradeRow, backgroundColor: t.is_whale ? 'rgba(255, 215, 0, 0.1)' : 'transparent'}}>
                  <span style={{color: '#666'}}>{t.time}</span>
                  <span style={{fontWeight: t.is_whale ? 'bold' : 'normal', color: t.is_whale ? 'gold' : '#fff'}}>
                    ${t.price.toFixed(1)}
                  </span>
                  <span style={{color: '#888', fontSize: '0.7em'}}>
                    ${(t.volume).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// DARK THEME STYLES
const styles = {
  dashboard: { backgroundColor: "#050505", color: "#e0e0e0", height: "100vh", fontFamily: "'JetBrains Mono', monospace", display: "flex", flexDirection: "column" },
  header: { display: "flex", justifyContent: "space-between", padding: "15px 30px", borderBottom: "1px solid #222", backgroundColor: "#0a0a0a" },
  logo: { fontSize: "1.2rem", fontWeight: "bold", letterSpacing: "2px", color: "#fff" },
  beta: { fontSize: "0.6rem", backgroundColor: "#00f2ea", color: "#000", padding: "2px 6px", borderRadius: "2px", marginLeft: "10px" },
  grid: { display: "flex", gap: "20px", padding: "20px", flex: 1, overflow: "hidden" },
  col: { width: "300px", display: "flex", flexDirection: "column", gap: "20px" },
  chartCol: { flex: 1, display: "flex", flexDirection: "column" },
  card: { backgroundColor: "#0a0a0a", border: "1px solid #222", borderRadius: "4px", display: "flex", flexDirection: "column", flex: 1 },
  cardTitle: { padding: "10px 15px", borderBottom: "1px solid #222", fontSize: "0.7rem", color: "#666", letterSpacing: "1px" },
  metricBox: { padding: "15px", borderBottom: "1px solid #222" },
  label: { fontSize: "0.7rem", color: "#444", marginBottom: "5px" },
  bigValue: { fontSize: "1.8rem", fontWeight: "bold", color: "#fff" },
  value: { fontSize: "1.2rem", color: "#fff" },
  statusBadge: { padding: "10px", textAlign: "center", color: "#000", fontWeight: "bold", margin: "10px", borderRadius: "4px" },
  btnRow: { display: "flex", gap: "10px", padding: "15px" },
  buyBtn: { flex: 1, padding: "10px", backgroundColor: "#00ff41", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: "bold" },
  sellBtn: { flex: 1, padding: "10px", backgroundColor: "#ff0055", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: "bold", color: "#fff" },
  tradeRow: { display: "flex", justifyContent: "space-between", padding: "5px 10px", fontSize: "0.75rem", borderBottom: "1px solid #111" }
};

export default App;