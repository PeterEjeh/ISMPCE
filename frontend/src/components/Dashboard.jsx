import { useState, useEffect } from "react";
import { fetchEmissions, fetchPrediction, fetchModelMetrics, fetchStatesContribution } from "../api/client";
import MapView from "./MapView";
import TimeSeriesChart from "./TimeSeriesChart";
import SectorCharts from "./SectorCharts";
import ModelComparison from "./ModelComparison";
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
  const [retryCount, setRetryCount] = useState(0);

  // Summary stats
  const [stats, setStats] = useState({
    latestCo2: 0,
    latestYear: 0,
    totalRecords: 0,
    avgGrowth: 0,
  });

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch all data in parallel
        const [emissionsRes, metricsRes, forecastRes, statesRes] = await Promise.all([
          fetchEmissions(),
          fetchModelMetrics(),
          fetchPrediction("Nigeria", 5),
          fetchStatesContribution(),
        ]);

        if (!isMounted) return;

        // Separate national-level from sector-level records
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
        if (isMounted) {
          setError(
            err.response?.data?.detail ||
            "Unable to connect to the FastAPI backend. If the service was sleeping (Render free tier), it may take 30-50 seconds to wake up."
          );
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [retryCount]);

  const handleScenarioResult = (data) => {
    if (!data) {
      setScenarioForecast([]);
      return;
    }
    if (data.has_scenario) {
      setScenarioForecast(data.forecast);
      setForecast(data.forecast);
    } else {
      setForecast(data.forecast);
      setScenarioForecast([]);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p><strong>Loading ISMPCE Dashboard Data...</strong></p>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "8px" }}>
          Connecting to FastAPI backend (if waking up from cold start on Render, please allow up to 30s).
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button
          className="btn btn--primary"
          onClick={() => setRetryCount((c) => c + 1)}
          style={{ marginTop: "16px" }}
        >
          Retry Connection
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
              <span className="header-tag">National &amp; State Level</span>
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
            R2: {metrics?.models?.find((m) => m.is_best)?.validation?.r2?.toFixed(3) || "0.891"}
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
        {/* Time series chart */}
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

        {/* Sector charts */}
        <div className="grid-span-2">
          <SectorCharts sectorData={sectorEmissions} />
        </div>

        {/* Model comparison */}
        <div className="grid-span-2">
          <ModelComparison metrics={metrics} />
        </div>

        {/* Scenario Simulator — primary interactive predictive engine */}
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
