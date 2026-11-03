
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from "recharts";

const COLORS = ["#08d9ed", "#ffd84d", "#ff78a9", "#ad68f5", "#328bff"];

const formatNumber = (value) =>
  Number(value).toLocaleString("en-IN");

export default function DistributionChart({ data = [], loading = false }) {
  const totalEmployees = data.reduce(
    (total, item) => total + (Number(item.employee_count) || 0),
    0
  );

  return (
    <div className="chart-card glass-card distribution-chart-card">
      <div className="chart-header">
        <div>
          <h3>Compensation Distribution</h3>
          <p>Employee distribution across compensation ranges</p>
        </div>
      </div>

      <div className="distribution-content">
        {loading ? (
          <div className="chart-loading">Loading distribution...</div>
        ) : data.length === 0 ? (
          <div className="chart-empty">
            <div className="chart-empty-icon">◉</div>
            <p>No distribution data available</p>
            <span>Distribution will appear after compensation analysis.</span>
          </div>
        ) : (
          <>
            <div className="distribution-donut">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="employee_count"
                    nameKey="range"
                    cx="50%"
                    cy="50%"
                    innerRadius="65%"
                    outerRadius="91%"
                    paddingAngle={3}
                    stroke="none"
                    animationDuration={900}
                  >
                    {data.map((entry, index) => (
                      <Cell
                        key={`${entry.range}-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "#071b38",
                      border: "1px solid #21cfff",
                      borderRadius: "10px",
                      color: "#ffffff",
                    }}
                    itemStyle={{ color: "#dff7ff" }}
                    formatter={(value) => [
                      `${formatNumber(value)} employees`,
                      "Count",
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>

              <div className="donut-center">
                <strong>{formatNumber(totalEmployees)}</strong>
                <span>Employees</span>
              </div>
            </div>

            <div
              className="distribution-legend"
              style={{
                minWidth: 0,
                width: "100%",
                display: "flex",
                flexDirection: "column",
                gap: "17px",
              }}
            >
              {data.map((item, index) => {
                const count = Number(item.employee_count) || 0;
                const percentage = totalEmployees
                  ? (count / totalEmployees) * 100
                  : 0;

                return (
                  <div
                    className="distribution-legend-item"
                    key={`${item.range}-${index}`}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "10px minmax(0, 1fr) auto",
                      alignItems: "center",
                      gap: "9px",
                      width: "100%",
                    }}
                  >
                    <span
                      className="legend-color"
                      style={{
                        backgroundColor: COLORS[index % COLORS.length],
                        flexShrink: 0,
                      }}
                    />

                    <span
                      className="legend-name"
                      title={item.range}
                      style={{
                        minWidth: 0,
                        whiteSpace: "normal",
                        overflow: "visible",
                        textOverflow: "clip",
                        fontSize: "12px",
                      }}
                    >
                      {item.range}
                    </span>

                    <strong style={{ whiteSpace: "nowrap", fontSize: "12px" }}>
                      {percentage.toFixed(1)}%
                    </strong>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
