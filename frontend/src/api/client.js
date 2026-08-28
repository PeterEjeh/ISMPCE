import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
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

  // Scenario overrides (only include if defined)
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
