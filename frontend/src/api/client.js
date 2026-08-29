import axios from "axios";

// Determine API Base URL
let rawBase = import.meta.env.VITE_API_URL || "";

// If Render passed the internal service name 'ismpce-backend', fix it to the public domain
if (rawBase === "ismpce-backend" || rawBase === "https://ismpce-backend" || rawBase === "http://ismpce-backend") {
  rawBase = "https://ismpce-backend.onrender.com";
}

if (rawBase && !rawBase.startsWith("http://") && !rawBase.startsWith("https://")) {
  rawBase = `https://${rawBase}`;
}

rawBase = rawBase.replace(/\/+$/, "");

// Fallback to production Render backend if running on static production host without env
const API_BASE =
  rawBase ||
  (import.meta.env.DEV
    ? "http://127.0.0.1:8000"
    : "https://ismpce-backend.onrender.com");

console.log("[ISMPCE Client] Connecting to API Base:", API_BASE);

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 45000,
});

export async function fetchEmissions(params = {}) {
  const response = await api.get("/emissions", { params });
  return response.data;
}

export async function fetchPrediction(
  region = "Nigeria",
  forecastHorizon = 5,
  modelName = null,
  scenarioParams = {}
) {
  const body = {
    region,
    forecast_horizon: forecastHorizon,
  };
  if (modelName) body.model_name = modelName;

  if (scenarioParams.fossil_fuel_share_change != null)
    body.fossil_fuel_share_change = scenarioParams.fossil_fuel_share_change;
  if (scenarioParams.gdp_growth_rate != null)
    body.gdp_growth_rate = scenarioParams.gdp_growth_rate;
  if (scenarioParams.population_growth_rate != null)
    body.population_growth_rate = scenarioParams.population_growth_rate;

  const response = await api.post("/predict", body);
  return response.data;
}

export async function fetchModelMetrics() {
  const response = await api.get("/models/metrics");
  return response.data;
}

export async function fetchStatesContribution() {
  const response = await api.get("/states/contribution");
  return response.data;
}

export default api;
