import { useState } from "react";
import { fetchPrediction } from "../api/client";

const NIGERIAN_STATES = [
  "Nigeria (National)",
  "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
  "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti",
  "Enugu", "FCT Abuja", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano",
  "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger",
  "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
  "Taraba", "Yobe", "Zamfara",
];

export default function PredictionPanel({ onPrediction }) {
  const [region, setRegion] = useState("Nigeria (National)");
  const [horizon, setHorizon] = useState(5);
  const [model, setModel] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // "Nigeria (National)" maps to "Nigeria" for the API; other state names
      // are passed as-is and used by the backend as a display label only.
      const apiRegion = region === "Nigeria (National)" ? "Nigeria" : region;
      const data = await fetchPrediction(apiRegion, horizon, model || null);
      setResult(data);
      if (onPrediction) onPrediction(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">CO2 Emission Prediction</h2>
      <p className="card-subtitle">
        Configure forecast parameters and generate predictions
      </p>
      <form className="prediction-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="pred-region" className="form-label">State / Region</label>
            <select
              id="pred-region"
              className="form-select"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              {NIGERIAN_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="pred-horizon" className="form-label">
              Forecast Horizon: {horizon} years
            </label>
            <input
              id="pred-horizon"
              type="range"
              className="form-range"
              min="1"
              max="10"
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            />
            <div className="range-labels">
              <span>1 yr</span>
              <span>10 yrs</span>
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="pred-model" className="form-label">Model</label>
            <select
              id="pred-model"
              className="form-select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="">Best (Auto)</option>
              <option value="random_forest">Random Forest</option>
              <option value="xgboost">XGBoost</option>
              <option value="lstm">LSTM</option>
            </select>
          </div>
          <div className="form-group form-group--button">
            <button
              type="submit"
              className="btn btn--primary"
              disabled={loading}
            >
              {loading ? "Generating..." : "Generate Forecast"}
            </button>
          </div>
        </div>

        <p className="scenario-note">
          State selection is a display label only. The forecast always uses the national
          Nigeria model — no state-level CO2 dataset exists publicly for Nigeria. For
          policy scenario analysis, use the Scenario Simulator below.
        </p>
      </form>

      {error && <div className="alert alert--error">{error}</div>}

      {result && (
        <div className="prediction-results">
          <div className="result-header">
            <span className="result-label">Region: {result.region}</span>
            <span className="result-label">Model: {result.model_used}</span>
          </div>
          <div className="result-table-wrapper">
            <table className="result-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Predicted CO2 (Mt)</th>
                  <th>Lower Bound</th>
                  <th>Upper Bound</th>
                </tr>
              </thead>
              <tbody>
                {result.forecast.map((f) => (
                  <tr key={f.year}>
                    <td>{f.year}</td>
                    <td>{f.predicted_co2}</td>
                    <td>{f.confidence_lower}</td>
                    <td>{f.confidence_upper}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
