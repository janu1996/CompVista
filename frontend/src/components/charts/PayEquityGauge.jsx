
import {
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from "recharts";

export default function PayEquityGauge({ value, loading = false }) {
  const score = Number(value);

  const validScore =
    value !== null &&
    value !== undefined &&
    value !== "" &&
    Number.isFinite(score)
      ? Math.min(100, Math.max(0, score))
      : null;

  const data = [
    {
      name: "Within target range",
      value: validScore ?? 0,
      fill: "#08d9ed",
    },
  ];

  return (
    <div className="chart-card glass-card equity-gauge-card">
      <div className="chart-header">
        <div>
          <h3>Pay Equity Indicator</h3>
          <p>Employees within target compa-ratio range</p>
        </div>
      </div>

      <div className="gauge-container">
        {loading ? (
          <div className="chart-loading">Calculating equity indicator...</div>
        ) : (
          <div className="gauge-visual">
            <div className="gauge-chart">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  data={data}
                  startAngle={180}
                  endAngle={0}
                  innerRadius="78%"
                  outerRadius="100%"
                  barSize={17}
                >
                  <PolarAngleAxis
                    type="number"
                    domain={[0, 100]}
                    tick={false}
                  />
                  <RadialBar
                    dataKey="value"
                    cornerRadius={12}
                    background={{ fill: "#193b65" }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>

            <div className="gauge-value">
              {validScore === null ? (
                <>
                  <h2>—</h2>
                  <span>Score unavailable</span>
                </>
              ) : (
                <>
                  <h2>{validScore.toFixed(1)}%</h2>
                  <span>Within target range</span>
                </>
              )}
            </div>

            <div className="gauge-footer">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
