export default function ModelComparison({ metrics }) {
  if (!metrics) {
    return (
      <div className="card">
        <h2 className="card-title">Model Performance</h2>
        <p className="card-subtitle">Loading model metrics...</p>
      </div>
    );
  }

  const formatMetric = (value) => {
    if (value === null || value === undefined) return "-";
    return Number(value).toFixed(4);
  };

  const modelLabels = {
    random_forest: "Random Forest",
    xgboost: "XGBoost",
    lstm: "LSTM",
  };

  return (
    <div className="card">
      <h2 className="card-title">Model Comparison</h2>
      <p className="card-subtitle">
        Performance metrics across validation and test sets
      </p>
      <div className="model-cards">
        {metrics.models.map((model) => (
          <div
            key={model.model_name}
            className={`model-card ${model.is_best ? "model-card--best" : ""}`}
          >
            <div className="model-card-header">
              <h3 className="model-name">
                {modelLabels[model.model_name] || model.model_name}
              </h3>
              {model.is_best && <span className="badge badge--primary">Best</span>}
            </div>
            <div className="metrics-grid">
              <div className="metric-group">
                <span className="metric-group-label">Validation</span>
                <div className="metric-row">
                  <span className="metric-label">R2</span>
                  <span className="metric-value">{formatMetric(model.validation.r2)}</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">MAE</span>
                  <span className="metric-value">{formatMetric(model.validation.mae)}</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">RMSE</span>
                  <span className="metric-value">{formatMetric(model.validation.rmse)}</span>
                </div>
              </div>
              <div className="metric-group">
                <span className="metric-group-label">Test</span>
                <div className="metric-row">
                  <span className="metric-label">R2</span>
                  <span className="metric-value">{formatMetric(model.test.r2)}</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">MAE</span>
                  <span className="metric-value">{formatMetric(model.test.mae)}</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">RMSE</span>
                  <span className="metric-value">{formatMetric(model.test.rmse)}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
