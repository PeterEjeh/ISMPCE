import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const SECTOR_COLORS = {
  Energy: "#3b82f6",
  "Oil & Transport": "#f97316",
  Flaring: "#ef4444",
  Industrial: "#8b5cf6",
};

export default function SectorCharts({ sectorData }) {
  if (!sectorData || sectorData.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">Sector Breakdown</h2>
        <p className="card-subtitle">Loading sector data...</p>
      </div>
    );
  }

  // Get most recent year for pie chart
  const latestYear = Math.max(...sectorData.map((d) => d.year));
  const latestSectors = sectorData.filter((d) => d.year === latestYear);
  const pieData = latestSectors.map((d) => ({
    name: d.sector,
    value: +d.co2_value.toFixed(2),
  }));

  // Group data by year for bar chart
  const years = [...new Set(sectorData.map((d) => d.year))].sort();
  const barData = years.map((year) => {
    const entry = { year };
    sectorData
      .filter((d) => d.year === year)
      .forEach((d) => {
        entry[d.sector] = +d.co2_value.toFixed(2);
      });
    return entry;
  });

  // Only show last 10 years for bar chart clarity
  const recentBarData = barData.slice(-10);
  const sectors = Object.keys(SECTOR_COLORS);

  return (
    <div className="card">
      <h2 className="card-title">CO2 Emissions by Sector</h2>
      <p className="card-subtitle">
        Breakdown across energy, transport, flaring, and industrial sectors
      </p>
      <div className="sector-charts-grid">
        <div className="sector-chart">
          <h3 className="chart-label">Trend by Sector (Last 10 Years)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={recentBarData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="year"
                tick={{ fill: "var(--text-secondary)", fontSize: 11 }}
                stroke="var(--border)"
              />
              <YAxis
                tick={{ fill: "var(--text-secondary)", fontSize: 11 }}
                stroke="var(--border)"
                label={{
                  value: "CO2 (Mt)",
                  angle: -90,
                  position: "insideLeft",
                  fill: "var(--text-secondary)",
                  fontSize: 11,
                }}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--text-primary)",
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {sectors.map((sector) => (
                <Bar
                  key={sector}
                  dataKey={sector}
                  stackId="a"
                  fill={SECTOR_COLORS[sector]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="sector-chart">
          <h3 className="chart-label">Share in {latestYear}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                labelLine={{ stroke: "var(--text-secondary)" }}
              >
                {pieData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={SECTOR_COLORS[entry.name] || "#64748b"}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--text-primary)",
                }}
                formatter={(value) => [`${value} Mt`, "CO2"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
