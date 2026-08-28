import { useState, useEffect } from "react";
import { fetchEmissions, fetchPrediction, fetchModelMetrics, fetchStatesContribution } from "../api/client";
import MapView from "./MapView";
import TimeSeriesChart from "./TimeSeriesChart";
import SectorCharts from "./SectorCharts";
import ModelComparison from "./ModelComparison";
import PredictionPanel from "./PredictionPanel";
import ScenarioSimulator from "./ScenarioSimulator";

export default function Dashboard() {
  const [emissions, setEmissions] = useState([]);
  const [sectorEmissions, setSectorEmissions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [scenarioForecast, setScenarioForecast] = useState([]);
  const [stateContributions, setStateContributions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Summary stats
  const [stats, setStats] = useState({
    latestCo2: 0,
    latestYear: 0,
    totalRecords: 0,
    avgGrowth: 0,
  });

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);

        // Fetch all data in parallel
        const [emissionsRes, metricsRes, forecastRes, statesRes] = await Promise.all([
          fetchEmissions(),
          fetchModelMetrics(),
          fetchPrediction("Nigeria", 5),
          fetchStatesContribution(),
        ]);

        // Separate national-level (no sector) from sector-level records
        const national = emissionsRes.data.filter((d) => !d.sector);
        const sectors = emissionsRes.data.filter((d) => d.sector);

        setEmissions(national);
        setSectorEmissions(sectors);
        setMetrics(metricsRes);
        setForecast(forecastRes.forecast);
        setStateContributions(statesRes.states || []);

        // Compute summary stats
        if (national.length > 0) {
          const latest = national[national.length - 1];
          const co2Values = national.map((d) => d.co2_value);
          const changes = [];
          for (let i = 1; i < co2Values.length; i++) {
            if (co2Values[i - 1] > 0) {
              changes.push(
                ((co2Values[i] - co2Values[i - 1]) / co2Values[i - 1]) * 100
              );
            }
          }
          const avgGrowth =
            changes.length > 0
              ? changes.reduce((a, b) => a + b, 0) / changes.length
              : 0;

          setStats({
            latestCo2: latest.co2_value,
            latestYear: latest.year,
            totalRecords: emissionsRes.total,
            avgGrowth: avgGrowth,
          });
        }
      } catch (err) {
        console.error("Failed to load data:", err);
        setError("Failed to connect to the API. Ensure the backend is running on port 8000.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handlePrediction = (data) => {
    setForecast(data.forecast);
    // Clear scenario when a new baseline prediction is made
    setScenarioForecast([]);
  };

  const handleScenarioResult = (data) => {
    if (!data) {
      setScenarioForecast([]);
      return;
    }
    // Pass scenario data to the time series chart
    if (data.has_scenario) {
      setScenarioForecast(data.forecast);
      // Also update the baseline forecast from the same response
      setForecast(data.forecast);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button className="btn btn--primary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div>
            <h1 className="header-title">ISMPCE</h1>
            <p className="header-subtitle">
              An Intelligent System for Monitoring and Predicting Nigeria's CO2 Emissions
              <span className="header-tag">National Study</span>
            </p>
          </div>
        </div>
      </header>

      {/* Summary cards */}
      <div className="summary-row">
        <div className="summary-card">
          <span className="summary-label">Latest National CO2</span>
          <span className="summary-value">{stats.latestCo2.toFixed(1)} Mt</span>
          <span className="summary-detail">Year {stats.latestYear}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Average Annual Growth</span>
          <span className="summary-value">{stats.avgGrowth.toFixed(1)}%</span>
          <span className="summary-detail">1990–{stats.latestYear}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Best Model</span>
          <span className="summary-value">
            {metrics?.best_model === "xgboost"
              ? "XGBoost"
              : metrics?.best_model === "random_forest"
              ? "Random Forest"
              : "LSTM"}
          </span>
          <span className="summary-detail">
            R2: {metrics?.models?.find((m) => m.is_best)?.validation?.r2?.toFixed(3) || "-"}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Data Points</span>
          <span className="summary-value">{stats.totalRecords}</span>
          <span className="summary-detail">Across all records</span>
        </div>
      </div>

      {/* Main grid */}
      <div className="dashboard-grid">
        {/* Time series chart – full width */}
        <div className="grid-span-2">
          <TimeSeriesChart
            historical={emissions}
            forecast={forecast}
            scenarioForecast={scenarioForecast}
          />
        </div>

        {/* Map with state contribution bar chart */}
        <div className="grid-span-2">
          <MapView stateContributions={stateContributions} />
        </div>

        {/* Sector charts – full width */}
        <div className="grid-span-2">
          <SectorCharts sectorData={sectorEmissions} />
        </div>

        {/* Model comparison */}
        <div className="grid-span-1">
          <ModelComparison metrics={metrics} />
        </div>

        {/* Prediction panel */}
        <div className="grid-span-1">
          <PredictionPanel onPrediction={handlePrediction} />
        </div>

        {/* Scenario Simulator – full width */}
        <div className="grid-span-2">
          <ScenarioSimulator onScenarioResult={handleScenarioResult} />
        </div>
      </div>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>
          ISMPCE v1.0 &mdash; Final Year Project &mdash; An Intelligent System for
          Monitoring and Predicting Nigeria's CO2 Emissions
        </p>
      </footer>
    </div>
  );
}
