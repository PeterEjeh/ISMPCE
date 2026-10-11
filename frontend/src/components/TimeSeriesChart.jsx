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
import { NIGERIA_REGIONS, cleanRegionName, isNationalRegion } from "../constants/regions";

export default function TimeSeriesChart({
  historical,
  forecast,
  scenarioForecast,
  region = "Nigeria (National)",
  onRegionChange,
  availableRegions = NIGERIA_REGIONS,
  loading = false,
}) {
  const isNational = isNationalRegion(region);
  const cleanName = cleanRegionName(region);

  // Merge historical and forecast data for a single continuous chart
  const historicalData = (historical || []).map((d) => ({
    year: d.year,
    co2: Number(d.co2_value || d.co2 || 0),
  }));

  const lastHistorical =
    historicalData.length > 0
      ? historicalData[historicalData.length - 1]
      : null;

  // Bridge point: last historical year appears in both forecast series for seamless connection
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
    const pred = d.predicted_co2 != null ? Number(d.predicted_co2) : null;
    const low = d.confidence_lower != null ? Number(d.confidence_lower) : pred;
    const upp = d.confidence_upper != null ? Number(d.confidence_upper) : pred;
    baselineForecastData.push({
      year: d.year,
      predicted: pred,
      lower: low,
      upper: upp,
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
      scenarioData.push({ year: d.year, scenario: Number(d.scenario_co2) });
    }
  });

  // Combine into one dataset
  const allYears = new Set([
    ...historicalData.map((d) => d.year),
    ...baselineForecastData.map((d) => d.year),
    ...scenarioData.map((d) => d.year),
  ]);

  const chartData = Array.from(allYears)
    .sort((a, b) => a - b)
    .map((year) => {
      const hist = historicalData.find((d) => d.year === year);
      const fc = baselineForecastData.find((d) => d.year === year);
      const sc = scenarioData.find((d) => d.year === year);

      const hasValidCI =
        fc &&
        fc.lower != null &&
        fc.upper != null &&
        !isNaN(fc.lower) &&
        !isNaN(fc.upper);

      return {
        year,
        historical: hist ? hist.co2 : null,
        predicted: fc ? fc.predicted : null,
        lower: fc ? fc.lower : null,
        upper: fc ? fc.upper : null,
        band: hasValidCI ? [fc.lower, fc.upper] : null,
        scenario: sc ? sc.scenario : null,
      };
    });

  return (
    <div className="card">
      <div className="chart-header-row">
        <div>
          <div className="chart-header-title-row">
            <h2 className="card-title">
              CO2 Emissions Trend &amp; Forecast &ndash; {region}
            </h2>
            <span
              className={`region-badge ${
                isNational ? "region-badge--national" : "region-badge--state"
              }`}
            >
              {isNational ? "National Total (Nigeria)" : `State Model (${cleanName})`}
            </span>
          </div>
          <p className="card-subtitle">
            {isNational ? (
              <>
                Nigeria aggregated historical emissions (1990&ndash;2024 solid line) with national machine learning baseline forecast (2025&ndash;2034 dashed line) and 95% confidence interval.
              </>
            ) : (
              <>
                Validated empirical emissions for <strong>{cleanName} State</strong> (1990&ndash;2024 solid line) with dedicated state machine learning forecast (2025&ndash;2034 dashed line).
              </>
            )}
            {hasScenario && (
              <span style={{ color: "#f97316", fontWeight: 500 }}>
                {" "}— Scenario simulation active (orange line)
              </span>
            )}
          </p>
        </div>

        {/* Region Switcher directly on chart */}
        {onRegionChange && (
          <div className="chart-controls">
            <label htmlFor="chart-region-select" className="chart-control-label">
              Target Level:
            </label>
            <select
              id="chart-region-select"
              className="chart-region-select"
              value={region}
              onChange={(e) => onRegionChange(e.target.value)}
              disabled={loading}
            >
              <option value="Nigeria (National)">🇳🇬 Nigeria (National)</option>
              <optgroup label="Trained Empirical States (Climate TRACE &amp; EDGAR)">
                {availableRegions
                  .filter((r) => !r.includes("National"))
                  .map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
              </optgroup>
            </select>
          </div>
        )}
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={380}>
          <ComposedChart
            data={chartData}
            margin={{ top: 12, right: 30, left: 10, bottom: 10 }}
          >
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
                borderRadius: "8px",
                color: "var(--text-primary)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
              }}
              formatter={(value, name) => {
                if (value === null || value === undefined) return ["-", name];
                // Fix for NaN in confidence interval band:
                if (Array.isArray(value)) {
                  const [lo, hi] = value;
                  const loNum = Number(lo);
                  const hiNum = Number(hi);
                  if (!isNaN(loNum) && !isNaN(hiNum)) {
                    return [`${loNum.toFixed(2)} – ${hiNum.toFixed(2)} Mt`, "95% CI Range"];
                  }
                  return ["-", name];
                }
                const num = Number(value);
                if (isNaN(num)) return ["-", name];
                return [`${num.toFixed(2)} Mt`, name];
              }}
            />
            <Legend
              wrapperStyle={{ color: "var(--text-secondary)", fontSize: 12, paddingTop: "8px" }}
            />
            {/* Confidence interval band */}
            <Area
              dataKey="band"
              fill="var(--accent)"
              fillOpacity={0.12}
              stroke="none"
              name="Confidence Interval"
              connectNulls={false}
            />
            {/* Historical line */}
            <Line
              type="monotone"
              dataKey="historical"
              stroke="var(--primary)"
              strokeWidth={2.5}
              dot={{ r: 3, fill: "var(--primary)" }}
              activeDot={{ r: 5 }}
              name={isNational ? "Historical CO2 (National)" : `Historical CO2 (${cleanName})`}
              connectNulls={false}
            />
            {/* Baseline forecast line */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="var(--accent)"
              strokeWidth={2.5}
              strokeDasharray="6 3"
              dot={{ r: 3, fill: "var(--accent)" }}
              activeDot={{ r: 5 }}
              name={isNational ? "Baseline Forecast (National)" : `Baseline Forecast (${cleanName})`}
              connectNulls={false}
            />
            {/* Scenario forecast line */}
            {hasScenario && (
              <Line
                type="monotone"
                dataKey="scenario"
                stroke="#f97316"
                strokeWidth={2.5}
                strokeDasharray="4 2"
                dot={{ r: 3, fill: "#f97316" }}
                activeDot={{ r: 5 }}
                name={`Scenario Forecast (${cleanName})`}
                connectNulls={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
