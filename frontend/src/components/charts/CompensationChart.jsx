
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

const formatINR = (value) =>
  `₹${Number(value).toLocaleString("en-IN")}`;

export default function CompensationChart({
  data = [],
  loading = false,
}) {
  return (
    <div className="chart-card glass-card compensation-chart-card">
      <div className="chart-header">
        <div>
          <h3>Compensation by Level</h3>
          <p>Average compensation across job levels</p>
        </div>
        <span className="chart-unit">INR (₹)</span>
      </div>

      <div className="chart-container compensation-chart">
        {loading ? (
          <div className="chart-loading">
            <div className="chart-spinner" />
            Loading compensation data...
          </div>
        ) : data.length === 0 ? (
          <div className="chart-empty">
            <div className="chart-empty-icon">▥</div>
            <p>No compensation data available</p>
            <span>
              Data will appear here once the analysis is available.
            </span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 18, right: 12, left: 8, bottom: 5 }}
              barCategoryGap="28%"
            >
              <defs>
                <linearGradient id="compVistaBar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#55eaff" />
                  <stop offset="48%" stopColor="#168cff" />
                  <stop offset="100%" stopColor="#0750b8" />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="3 5"
                stroke="rgba(145, 190, 235, 0.13)"
                vertical={false}
              />

              <XAxis
                dataKey="level"
                tick={{ fill: "#b8d1ed", fontSize: 11 }}
                axisLine={{ stroke: "rgba(90, 160, 225, 0.25)" }}
                tickLine={false}
                dy={9}
              />

              <YAxis
                tick={{ fill: "#91accb", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) =>
                  `₹${Number(value).toLocaleString("en-IN")}`
                }
                width={75}
              />

              <Tooltip
                cursor={{ fill: "rgba(0, 195, 255, 0.07)" }}
                contentStyle={{
                  background: "rgba(5, 22, 48, 0.97)",
                  border: "1px solid rgba(45, 195, 255, 0.65)",
                  borderRadius: "12px",
                  color: "#ffffff",
                  boxShadow: "0 8px 25px rgba(0, 140, 255, 0.2)",
                }}
                labelStyle={{
                  color: "#61dcff",
                  fontWeight: 700,
                  marginBottom: 6,
                }}
                formatter={(value) => [
                  formatINR(value),
                  "Average Compensation",
                ]}
              />

              <Bar
                dataKey="average_compensation"
                fill="url(#compVistaBar)"
                radius={[7, 7, 0, 0]}
                maxBarSize={48}
                animationDuration={1000}
              >
                {data.map((entry, index) => (
                  <Cell key={`bar-${index}`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
