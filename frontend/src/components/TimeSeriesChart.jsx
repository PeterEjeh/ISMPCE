import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  ComposedChart,
  ResponsiveContainer,
} from "recharts";

export default function TimeSeriesChart({ historical, forecast, scenarioForecast }) {
  // Merge historical and forecast data for a single continuous chart
  const historicalData = (historical || []).map((d) => ({
    year: d.year,
    co2: d.co2_value,
  }));

  const lastHistorical =
    historicalData.length > 0
      ? historicalData[historicalData.length - 1]
      : null;

  // Bridge point: last historical year appears in both forecast series
  const baselineForecastData = [];
  if (lastHistorical) {
    baselineForecastData.push({
      year: lastHistorical.year,
      predicted: lastHistorical.co2,
      lower: lastHistorical.co2,
      upper: lastHistorical.co2,
    });
  }

  (forecast || []).forEach((d) => {
    baselineForecastData.push({
      year: d.year,
      predicted: d.predicted_co2,
      lower: d.confidence_lower,
      upper: d.confidence_upper,
    });
  });

  // Scenario forecast data (optional)
  const hasScenario = scenarioForecast && scenarioForecast.length > 0;
  const scenarioData = [];
  if (hasScenario && lastHistorical) {
    scenarioData.push({ year: lastHistorical.year, scenario: lastHistorical.co2 });
  }
  (scenarioForecast || []).forEach((d) => {
    if (d.scenario_co2 != null) {
      scenarioData.push({ year: d.year, scenario: d.scenario_co2 });
    }
  });

  // Combine into one dataset
  const allYears = new Set([
    ...historicalData.map((d) => d.year),
    ...baselineForecastData.map((d) => d.year),
    ...scenarioData.map((d) => d.year),
  ]);
  const chartData = Array.from(allYears)
    .sort()
    .map((year) => {
      const hist = historicalData.find((d) => d.year === year);
      const fc = baselineForecastData.find((d) => d.year === year);
      const sc = scenarioData.find((d) => d.year === year);
      return {
        year,
        historical: hist ? hist.co2 : null,
        predicted: fc ? fc.predicted : null,
        lower: fc ? fc.lower : null,
        upper: fc ? fc.upper : null,
        band: fc ? [fc.lower, fc.upper] : null,
        scenario: sc ? sc.scenario : null,
      };
    });

  return (
    <div className="card">
      <h2 className="card-title">CO2 Emissions Trend and Forecast – Nigeria</h2>
      <p className="card-subtitle">
        Historical data (solid) with projected baseline forecast and confidence interval
        {hasScenario && " — Scenario forecast shown in orange"}
      </p>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={360}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="year"
              tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
              stroke="var(--border)"
            />
            <YAxis
              tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
              stroke="var(--border)"
              label={{
                value: "CO2 (Mt)",
                angle: -90,
                position: "insideLeft",
                fill: "var(--text-secondary)",
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-primary)",
              }}
              formatter={(value, name) => {
                if (value === null || value === undefined) return ["-", name];
                return [`${Number(value).toFixed(2)} Mt`, name];
              }}
            />
            <Legend
              wrapperStyle={{ color: "var(--text-secondary)", fontSize: 12 }}
            />
            {/* Confidence interval band */}
            <Area
              dataKey="band"
              fill="var(--accent)"
              fillOpacity={0.1}
              stroke="none"
              name="Confidence Interval"
              connectNulls={false}
            />
            {/* Historical line */}
            <Line
              type="monotone"
              dataKey="historical"
              stroke="var(--primary)"
              strokeWidth={2}
              dot={{ r: 3, fill: "var(--primary)" }}
              name="Historical CO2"
              connectNulls={false}
            />
            {/* Baseline forecast line */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="var(--accent)"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={{ r: 3, fill: "var(--accent)" }}
              name="Baseline Forecast"
              connectNulls={false}
            />
            {/* Scenario forecast line (only rendered when scenario data exists) */}
            {hasScenario && (
              <Line
                type="monotone"
                dataKey="scenario"
                stroke="#f97316"
                strokeWidth={2}
                strokeDasharray="4 2"
                dot={{ r: 3, fill: "#f97316" }}
                name="Scenario Forecast"
                connectNulls={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
