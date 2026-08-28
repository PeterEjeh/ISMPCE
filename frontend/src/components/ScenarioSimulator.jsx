import { useState } from "react";
import { fetchPrediction } from "../api/client";

// Only empirical/validated states from Climate TRACE & EDGAR datasets + National
const AVAILABLE_REGIONS = [
  "Nigeria (National)",
  "Bauchi (Case Study)",
  "Lagos",
  "Rivers",
  "Delta",
  "Akwa Ibom",
  "Kano",
  "Ogun",
  "Kaduna",
  "Oyo",
  "FCT Abuja",
  "Kogi",
  "Borno",
];

const PRESETS = [
  {
    label: "10% Renewable Increase",
    values: { fossil_fuel_share_change: -10, gdp_growth_rate: null, population_growth_rate: null },
  },
  {
    label: "5% GDP Growth",
    values: { fossil_fuel_share_change: null, gdp_growth_rate: 5, population_growth_rate: null },
  },
  {
    label: "High Population Growth",
    values: { fossil_fuel_share_change: null, gdp_growth_rate: null, population_growth_rate: 3.5 },
  },
  {
    label: "Green Transition",
    values: { fossil_fuel_share_change: -20, gdp_growth_rate: 4, population_growth_rate: 2 },
  },
];

export default function ScenarioSimulator({ onScenarioResult }) {
  const [region, setRegion] = useState("Nigeria (National)");
  const [horizon, setHorizon] = useState(5);
  const [model, setModel] = useState("");
  const [fossilChange, setFossilChange] = useState(0);
  const [gdpGrowth, setGdpGrowth] = useState(0);
  const [popGrowth, setPopGrowth] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const applyPreset = (preset) => {
    if (preset.values.fossil_fuel_share_change != null)
      setFossilChange(preset.values.fossil_fuel_share_change);
    if (preset.values.gdp_growth_rate != null)
      setGdpGrowth(preset.values.gdp_growth_rate);
    if (preset.values.population_growth_rate != null)
      setPopGrowth(preset.values.population_growth_rate);
  };

  const handleReset = () => {
    setFossilChange(0);
    setGdpGrowth(0);
    setPopGrowth(0);
    setResult(null);
    setError(null);
    if (onScenarioResult) onScenarioResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const scenarioParams = {
        fossil_fuel_share_change: fossilChange !== 0 ? fossilChange : null,
        gdp_growth_rate: gdpGrowth !== 0 ? gdpGrowth : null,
        population_growth_rate: popGrowth !== 0 ? popGrowth : null,
      };

      // Clean region name for API
      let apiRegion = region;
      if (region === "Nigeria (National)") apiRegion = "Nigeria";
      else if (region === "Bauchi (Case Study)") apiRegion = "Bauchi";

      const data = await fetchPrediction(
        apiRegion,
        horizon,
        model || null,
        scenarioParams
      );
      setResult(data);
      if (onScenarioResult) onScenarioResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Scenario request failed");
    } finally {
      setLoading(false);
    }
  };

  const isStateSelected = region !== "Nigeria (National)" && region !== "Nigeria";

  return (
    <div className="card scenario-card">
      <h2 className="card-title">Scenario Simulator</h2>
      <p className="card-subtitle">
        Adjust policy levers to see how changes affect projected CO2 emissions in real-time.
      </p>

      {/* Preset buttons */}
      <div className="preset-row">
        <span className="preset-label">Quick Scenarios:</span>
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            className="preset-btn"
            onClick={() => applyPreset(p)}
          >
            {p.label}
          </button>
        ))}
        <button
          type="button"
          className="preset-btn preset-btn--reset"
          onClick={handleReset}
        >
          Reset All
        </button>
      </div>

      <form onSubmit={handleSubmit} className="scenario-form">
        {/* Controls row */}
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="scen-region" className="form-label">
              Target Level / Validated State
            </label>
            <select
              id="scen-region"
              className="form-select"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              {AVAILABLE_REGIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="scen-model" className="form-label">Model Engine</label>
            <select
              id="scen-model"
              className="form-select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="">Best (Auto / State Calibrated)</option>
              <option value="xgboost">XGBoost</option>
              <option value="random_forest">Random Forest</option>
              <option value="lstm">LSTM (Neural Network)</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="scen-horizon" className="form-label">
              Horizon: {horizon} years
            </label>
            <input
              id="scen-horizon"
              type="range"
              className="form-range"
              min="1" max="10"
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            />
            <div className="range-labels"><span>1 yr</span><span>10 yrs</span></div>
          </div>
        </div>

        <div className="scenario-badge-box">
          {isStateSelected ? (
            <span className="state-mode-badge active">
              ✓ <strong>State-Level Model Active:</strong> Running machine learning model trained on empirical <em>{region}</em> observations (Climate TRACE &amp; EDGAR gridded timeseries).
            </span>
          ) : (
            <span className="state-mode-badge national">
              🏛 <strong>National Master Model Active:</strong> Running national macro model trained on Nigeria OWID/World Bank historical dataset.
            </span>
          )}
        </div>

        {/* Scenario sliders */}
        <div className="slider-group">
          <div className="slider-row">
            <label className="slider-label">
              Fossil Fuel Share Change
              <span className="slider-value">{fossilChange > 0 ? "+" : ""}{fossilChange} pp</span>
            </label>
            <input
              type="range" className="form-range"
              min="-30" max="30" step="1"
              value={fossilChange}
              onChange={(e) => setFossilChange(Number(e.target.value))}
            />
            <div className="range-labels">
              <span>-30 pp (more renewable)</span>
              <span>+30 pp (more fossil)</span>
            </div>
          </div>

          <div className="slider-row">
            <label className="slider-label">
              GDP Growth Rate
              <span className="slider-value">{gdpGrowth > 0 ? "+" : ""}{gdpGrowth}%</span>
            </label>
            <input
              type="range" className="form-range"
              min="-5" max="15" step="0.5"
              value={gdpGrowth}
              onChange={(e) => setGdpGrowth(Number(e.target.value))}
            />
            <div className="range-labels"><span>-5%</span><span>+15%</span></div>
          </div>

          <div className="slider-row">
            <label className="slider-label">
              Population Growth Rate
              <span className="slider-value">{popGrowth > 0 ? "+" : ""}{popGrowth}%</span>
            </label>
            <input
              type="range" className="form-range"
              min="0" max="5" step="0.1"
              value={popGrowth}
              onChange={(e) => setPopGrowth(Number(e.target.value))}
            />
            <div className="range-labels"><span>0%</span><span>5%</span></div>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn--primary btn--full"
          disabled={loading}
        >
          {loading ? "Running Machine Learning Prediction..." : `Run Scenario Forecast for ${region}`}
        </button>
      </form>

      {error && <div className="alert alert--error">{error}</div>}

      {result && (
        <div className="prediction-results">
          <div className="result-header">
            <span className="result-label"><strong>Target:</strong> {result.region}</span>
            <span className="result-label"><strong>Engine:</strong> {result.model_used}</span>
            {result.has_scenario && (
              <span className="result-label result-label--scenario">Policy Override Applied</span>
            )}
          </div>
          <div className="result-table-wrapper">
            <table className="result-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Baseline CO2 (Mt)</th>
                  {result.has_scenario && <th>Scenario CO2 (Mt)</th>}
                  {result.has_scenario && <th>Policy Delta (Mt)</th>}
                  <th>Lower (95% CI)</th>
                  <th>Upper (95% CI)</th>
                </tr>
              </thead>
              <tbody>
                {result.forecast.map((f) => {
                  const diff =
                    f.scenario_co2 != null
                      ? (f.scenario_co2 - f.predicted_co2).toFixed(2)
                      : null;
                  return (
                    <tr key={f.year}>
                      <td><strong>{f.year}</strong></td>
                      <td>{f.predicted_co2}</td>
                      {result.has_scenario && (
                        <td className="scenario-cell">{f.scenario_co2 ?? "-"}</td>
                      )}
                      {result.has_scenario && (
                        <td className={diff < 0 ? "diff-negative" : "diff-positive"}>
                          {diff !== null ? (diff > 0 ? "+" : "") + diff + " Mt" : "-"}
                        </td>
                      )}
                      <td>{f.confidence_lower}</td>
                      <td>{f.confidence_upper}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
