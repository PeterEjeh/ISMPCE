# ISMPCE — Intelligent System for Monitoring and Predicting CO₂ Emissions

An end-to-end Machine Learning and Decision Support Platform for monitoring historical greenhouse gas emissions and predicting multi-year carbon trajectories (Nigeria National Level & Bauchi State Case Study).

---

## 🌟 System Architecture

```
+-------------------------------------------------------------------------------+
|                             REACT FRONTEND (Vite)                             |
|  - Interactive Leaflet Map (Esri Dark Canvas)   - Scenario Policy Simulator   |
|  - Recharts Multi-Year Confidence Charts        - Responsive Mobile UI        |
+---------------------------------------+---------------------------------------+
                                        | REST API (JSON / HTTP)
+---------------------------------------v---------------------------------------+
|                              FASTAPI BACKEND                                  |
|  - /emissions: Historical series      - /predict: National & State Inference  |
|  - /models/metrics: Benchmark scores  - /states: Spatial contribution ranking |
+---------------------------------------+---------------------------------------+
                                        | Serialized Model Loading (.joblib)
+---------------------------------------v---------------------------------------+
|                            MACHINE LEARNING LAYER                             |
|  - National Models (XGBoost / LSTM / RF)   - 37 State-Specific ML Models      |
|  - Multi-Feature Scenario Engine           - Autoregressive Rolling State     |
+-------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be live at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Interactive UI will be live at `http://localhost:5173`.

---

## 📊 Machine Learning Models & Capabilities

1. **National Forecasting Engine:**
   - **XGBoost (Optuna Tuned):** $R^2 = 0.8914$, $MAE = 1.82	ext{ MtCO}_2$ (Production Selected)
   - **Random Forest Regressor:** $R^2 = 0.4026$, $MAE = 4.56	ext{ MtCO}_2$ (Baseline)
   - **Stacked 2-Layer LSTM (PyTorch):** Deep sequence modeling alternative.

2. **Dedicated State-Level Machine Learning Models:**
   - Trained across sub-national jurisdictions using Climate TRACE Admin-1 satellite observations and EDGAR v8.0 $0.1^\circ$ gridded timeseries ($R^2 > 0.99$, $MAE < 0.35	ext{ MtCO}_2$).

3. **Scenario Policy Simulator:**
   - Real-time policy lever adjustments (Fossil Fuel Share, GDP Growth, Population Growth) with multi-feature propagation and compounding autoregressive state rolling.

---

## 🛠 Tech Stack
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy, Uvicorn
- **Machine Learning:** XGBoost, Scikit-learn, PyTorch, Optuna, Joblib
- **Frontend:** React 18, Vite, Recharts, Leaflet.js, Esri World Dark Canvas
- **Data Engineering:** Pandas, NumPy, Our World in Data (OWID), World Bank WDI, EDGAR v8.0, Climate TRACE
