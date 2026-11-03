
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChartNoAxesCombined,
  Users,
  IndianRupee,
  Target,
  AlertTriangle,
  RefreshCw,
  Download,
  Search,
  SlidersHorizontal,
  TrendingUp,
  ShieldCheck,
  CircleAlert,
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";

import api from "../../services/api.js";

const initialFilters = {
  level: "all",
  issue: "all",
};

const COLORS = ["#08d9ed", "#ffd84d", "#ff78a9", "#ad68f5"];

const formatINR = (value) =>
  `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;

const formatNumber = (value) =>
  Number(value || 0).toLocaleString("en-IN");

const getResponseData = (response) =>
  response?.data?.data ?? response?.data ?? {};

const formatIssue = (type) => {
  const labels = {
    BELOW_BAND_MINIMUM: "Below Band Minimum",
    LOW_COMPA_RATIO: "Low Compa-Ratio",
    PEER_PAY_GAP: "Peer Pay Gap",
  };

  return labels[type] || type?.replaceAll("_", " ") || "No Issue";
};

function MetricCard({ item }) {
  const Icon = item.icon;

  return (
    <div className={`analysis-metric-card metric-${item.color}`}>
      <div className="analysis-metric-icon">
        <Icon size={23} />
      </div>

      <div className="analysis-metric-content">
        <span>{item.title}</span>
        <h2>{item.value}</h2>
        <p>{item.subtitle}</p>
      </div>
    </div>
  );
}

function EmptyAnalysis({ icon: Icon, title, description }) {
  return (
    <div className="analysis-empty-state">
      <div className="analysis-empty-icon">
        <Icon size={30} />
      </div>
      <h4>{title}</h4>
      <p>{description}</p>
    </div>
  );
}

export default function CompensationAnalysis() {
  const [employees, setEmployees] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [searchTerm, setSearchTerm] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analysisDate, setAnalysisDate] = useState(null);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/api/analysis/results");
      const responseData = getResponseData(response);

      const results = Array.isArray(responseData.results)
        ? responseData.results
        : [];

      setEmployees(results);
      setAnalysisDate(responseData.summary?.analysis_date || null);
    } catch (err) {
      console.error("Compensation analysis error:", err);

      setError(
        err.response?.data?.message ||
          "Unable to load compensation analysis. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const updateFilter = (name, value) => {
    setFilters((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const resetFilters = () => {
    setFilters(initialFilters);
    setSearchTerm("");
  };

  const filteredEmployees = useMemo(() => {
    return employees.filter((employee) => {
      const search = searchTerm.trim().toLowerCase();

      const matchesSearch =
        !search ||
        String(employee.employee_name || "")
          .toLowerCase()
          .includes(search) ||
        String(employee.employee_id || "")
          .toLowerCase()
          .includes(search);

      const matchesLevel =
        filters.level === "all" ||
        String(employee.level_id) === filters.level;

      const issues = Array.isArray(employee.potential_issues)
        ? employee.potential_issues
        : [];

      const matchesIssue =
        filters.issue === "all" ||
        issues.some((issue) => issue.type === filters.issue);

      return matchesSearch && matchesLevel && matchesIssue;
    });
  }, [employees, filters, searchTerm]);

  const metrics = useMemo(() => {
    const total = filteredEmployees.length;

    const averageSalary = total
      ? filteredEmployees.reduce(
          (sum, employee) =>
            sum + (Number(employee.normalized_salary_inr) || 0),
          0
        ) / total
      : 0;

    const validRatios = filteredEmployees
      .map((employee) => Number(employee.compa_ratio))
      .filter((ratio) => Number.isFinite(ratio) && ratio > 0);

    const averageRatio = validRatios.length
      ? validRatios.reduce((sum, ratio) => sum + ratio, 0) /
        validRatios.length
      : 0;

    const flagged = filteredEmployees.filter(
      (employee) => employee.requires_hr_review
    ).length;

    return [
      {
        title: "Total Employees",
        value: formatNumber(total),
        subtitle: "Employees included in current view",
        icon: Users,
        color: "cyan",
      },
      {
        title: "Average Compensation",
        value: formatINR(averageSalary),
        subtitle: "Average annual INR-normalized salary",
        icon: IndianRupee,
        color: "blue",
      },
      {
        title: "Average Compa-Ratio",
        value: validRatios.length
          ? `${averageRatio.toFixed(1)}%`
          : "—",
        subtitle: "Against salary band midpoint",
        icon: Target,
        color: "purple",
      },
      {
        title: "Employees Flagged",
        value: formatNumber(flagged),
        subtitle: "Employees requiring HR review",
        icon: AlertTriangle,
        color: "red",
      },
    ];
  }, [filteredEmployees]);

  const levelChartData = useMemo(() => {
    const groups = {};

    filteredEmployees.forEach((employee) => {
      const level = employee.level_id;
      const salary = Number(employee.normalized_salary_inr);

      if (
        level === null ||
        level === undefined ||
        !Number.isFinite(salary)
      ) return;

      if (!groups[level]) {
        groups[level] = { total: 0, count: 0 };
      }

      groups[level].total += salary;
      groups[level].count += 1;
    });

    return Object.entries(groups)
      .map(([level, values]) => ({
        level: `Level ${level}`,
        average: Math.round(values.total / values.count),
      }))
      .sort(
        (a, b) =>
          Number(a.level.replace("Level ", "")) -
          Number(b.level.replace("Level ", ""))
      );
  }, [filteredEmployees]);

  const ratioChartData = useMemo(() => {
    const ranges = [
      { range: "Below 80%", min: -Infinity, max: 80 },
      { range: "80% - 100%", min: 80, max: 100 },
      { range: "100% - 120%", min: 100, max: 120 },
      { range: "Above 120%", min: 120, max: Infinity },
    ];

    const counts = ranges.map((range) => ({
      name: range.range,
      value: 0,
    }));

    filteredEmployees.forEach((employee) => {
      const ratio = Number(employee.compa_ratio);

      if (!Number.isFinite(ratio) || ratio <= 0) return;

      const index = ranges.findIndex(
        (range) => ratio >= range.min && ratio < range.max
      );

      if (index !== -1) counts[index].value += 1;
    });

    return counts;
  }, [filteredEmployees]);

  const flaggedCount = filteredEmployees.filter(
    (employee) => employee.requires_hr_review
  ).length;

  const targetRangeCount = ratioChartData
    .filter((item) =>
      ["80% - 100%", "100% - 120%"].includes(item.name)
    )
    .reduce((sum, item) => sum + item.value, 0);

  const targetRangePercentage = filteredEmployees.length
    ? (targetRangeCount / filteredEmployees.length) * 100
    : 0;

  const exportAnalysis = () => {
    const headers = [
      "Employee ID",
      "Employee Name",
      "Level",
      "Currency",
      "Annual Salary INR",
      "Band Minimum INR",
      "Band Midpoint INR",
      "Band Maximum INR",
      "Compa Ratio",
      "Band Position",
      "Requires HR Review",
      "Issues",
    ];

    const rows = filteredEmployees.map((employee) => {
      const issues = (employee.potential_issues || [])
        .map((issue) => formatIssue(issue.type))
        .join("; ");

      return [
        employee.employee_id,
        employee.employee_name,
        employee.level_id,
        "INR",
        employee.normalized_salary_inr,
        employee.band_minimum_inr,
        employee.band_midpoint_inr,
        employee.band_maximum_inr,
        employee.compa_ratio,
        employee.band_position,
        employee.requires_hr_review ? "Yes" : "No",
        issues,
      ];
    });

    const escapeCSV = (value) =>
      `"${String(value ?? "").replaceAll('"', '""')}"`;

    const csv = [headers, ...rows]
      .map((row) => row.map(escapeCSV).join(","))
      .join("\n");

    const blob = new Blob(["\uFEFF" + csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "compvista-compensation-analysis.csv";
    link.click();

    URL.revokeObjectURL(url);
  };

  const hasFilters =
    filters.level !== "all" ||
    filters.issue !== "all" ||
    searchTerm !== "";

  return (
    <div className="compensation-page">

      {/* PAGE HEADER */}
      <section className="compensation-page-header">
        <div>
          <div className="compensation-heading-icon">
            <ChartNoAxesCombined size={25} />
          </div>

          <h1>Compensation Analysis</h1>

          <p>
            Analyze salary structures, identify pay gaps and monitor
            compensation equity across your organization.
          </p>

          <span className="analysis-date-label">
            Analysis date: {analysisDate || "Loading..."}
          </span>
        </div>

        <div className="compensation-header-actions">
          <button
            className="analysis-outline-btn"
            onClick={fetchAnalysis}
            disabled={loading}
          >
            <RefreshCw
              size={16}
              className={loading ? "spin" : ""}
            />
            Refresh
          </button>

          <button
            className="btn-primary"
            onClick={exportAnalysis}
            disabled={loading || filteredEmployees.length === 0}
          >
            <Download size={17} />
            Export CSV
          </button>
        </div>
      </section>

      {/* ERROR */}
      {error && (
        <div className="analysis-error">
          <CircleAlert size={19} />
          <span>{error}</span>
          <button onClick={fetchAnalysis}>Retry</button>
        </div>
      )}

      {/* OVERVIEW METRICS */}
      <section className="analysis-metrics-grid">
        {metrics.map((item) => (
          <MetricCard key={item.title} item={item} />
        ))}
      </section>

      {/* FILTER PANEL */}
      <section className="analysis-filter-panel">
        <div className="analysis-filter-heading">
          <div>
            <SlidersHorizontal size={19} />
            <h3>Analysis Filters</h3>
          </div>

          {hasFilters && (
            <button onClick={resetFilters}>Clear all</button>
          )}
        </div>

        <div className="analysis-filter-grid">

          <div className="analysis-filter-field">
            <label htmlFor="level">Job Level</label>

            <select
              id="level"
              value={filters.level}
              onChange={(e) =>
                updateFilter("level", e.target.value)
              }
            >
              <option value="all">All Levels</option>
              {[1, 2, 3, 4, 5].map((level) => (
                <option key={level} value={String(level)}>
                  Level {level}
                </option>
              ))}
            </select>
          </div>

          <div className="analysis-filter-field">
            <label htmlFor="issue">Issue Type</label>

            <select
              id="issue"
              value={filters.issue}
              onChange={(e) =>
                updateFilter("issue", e.target.value)
              }
            >
              <option value="all">All Issues</option>
              <option value="BELOW_BAND_MINIMUM">
                Below Band Minimum
              </option>
              <option value="LOW_COMPA_RATIO">
                Low Compa-Ratio
              </option>
              <option value="PEER_PAY_GAP">
                Peer Pay Gap
              </option>
            </select>
          </div>

          <div className="analysis-filter-field search-filter-field">
            <label htmlFor="employee-search">Employee Search</label>

            <div className="analysis-search-input">
              <Search size={17} />

              <input
                id="employee-search"
                type="text"
                placeholder="Search employee name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

        </div>
      </section>

      {/* ANALYSIS CHARTS */}
      <section className="compensation-analysis-grid">

        {/* COMPENSATION BY LEVEL */}
        <div className="analysis-panel">
          <div className="analysis-panel-heading">
            <div>
              <h3>Compensation by Level</h3>
              <p>Average annual compensation in INR</p>
            </div>
            <ChartNoAxesCombined size={20} />
          </div>

          {loading ? (
            <EmptyAnalysis
              icon={IndianRupee}
              title="Loading compensation data"
              description="Fetching employee compensation records."
            />
          ) : levelChartData.length === 0 ? (
            <EmptyAnalysis
              icon={IndianRupee}
              title="No compensation data"
              description="No matching employee records found."
            />
          ) : (
            <div className="analysis-chart-container">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={levelChartData}
                  margin={{ top: 15, right: 12, left: 12, bottom: 5 }}
                >
                  <CartesianGrid
                    stroke="#29476b"
                    strokeDasharray="3 3"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="level"
                    stroke="#a8c1dc"
                    tick={{ fontSize: 11 }}
                  />

                  <YAxis
                    stroke="#a8c1dc"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(value) =>
                      `₹${(value / 100000).toFixed(0)}L`
                    }
                  />

                  <Tooltip
                    formatter={(value) => [
                      formatINR(value),
                      "Average Compensation",
                    ]}
                    contentStyle={{
                      background: "#071b38",
                      border: "1px solid #168bd0",
                      borderRadius: 10,
                      color: "#fff",
                    }}
                  />

                  <Bar
                    dataKey="average"
                    fill="#08bce9"
                    radius={[7, 7, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* COMPA RATIO DISTRIBUTION */}
        <div className="analysis-panel">
          <div className="analysis-panel-heading">
            <div>
              <h3>Compa-Ratio Analysis</h3>
              <p>Employee distribution across ratio ranges</p>
            </div>
            <Target size={20} />
          </div>

          {loading ? (
            <EmptyAnalysis
              icon={Target}
              title="Loading ratio data"
              description="Calculating compa-ratio distribution."
            />
          ) : filteredEmployees.length === 0 ? (
            <EmptyAnalysis
              icon={Target}
              title="No ratio data available"
              description="No matching employee records found."
            />
          ) : (
            <div className="analysis-ratio-content">
              <div className="analysis-ratio-donut">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={ratioChartData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius="62%"
                      outerRadius="90%"
                      paddingAngle={3}
                      stroke="none"
                    >
                      {ratioChartData.map((item, index) => (
                        <Cell
                          key={item.name}
                          fill={COLORS[index]}
                        />
                      ))}
                    </Pie>

                    <Tooltip
                      contentStyle={{
                        background: "#071b38",
                        border: "1px solid #168bd0",
                        borderRadius: 10,
                        color: "#fff",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>

                <div className="analysis-donut-center">
                  <strong>{formatNumber(filteredEmployees.length)}</strong>
                  <span>Employees</span>
                </div>
              </div>

              <div className="analysis-ratio-legend">
                {ratioChartData.map((item, index) => {
                  const percentage = filteredEmployees.length
                    ? (item.value / filteredEmployees.length) * 100
                    : 0;

                  return (
                    <div className="analysis-legend-item" key={item.name}>
                      <span
                        className="analysis-legend-dot"
                        style={{ background: COLORS[index] }}
                      />
                      <span>{item.name}</span>
                      <strong>{percentage.toFixed(1)}%</strong>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* PAY EQUITY INSIGHTS */}
        <div className="analysis-panel">
          <div className="analysis-panel-heading">
            <div>
              <h3>Pay Equity Insights</h3>
              <p>Compensation disparity indicators</p>
            </div>
            <ShieldCheck size={20} />
          </div>

          {loading ? (
            <EmptyAnalysis
              icon={TrendingUp}
              title="Loading insights"
              description="Analyzing compensation records."
            />
          ) : (
            <div className="analysis-insights-content">
              <div className="analysis-insight-item">
                <div className="analysis-insight-icon green-insight">
                  <Target size={20} />
                </div>
                <div>
                  <span>Within 80%–120% range</span>
                  <strong>{targetRangePercentage.toFixed(1)}%</strong>
                </div>
              </div>

              <div className="analysis-insight-item">
                <div className="analysis-insight-icon red-insight">
                  <AlertTriangle size={20} />
                </div>
                <div>
                  <span>Employees requiring review</span>
                  <strong>{formatNumber(flaggedCount)}</strong>
                </div>
              </div>

              <div className="analysis-insight-item">
                <div className="analysis-insight-icon blue-insight">
                  <Users size={20} />
                </div>
                <div>
                  <span>Employees without flags</span>
                  <strong>
                    {formatNumber(
                      filteredEmployees.length - flaggedCount
                    )}
                  </strong>
                </div>
              </div>

              <p className="analysis-insight-note">
                These indicators identify potential compensation
                concerns and are not a standalone fairness determination.
              </p>
            </div>
          )}
        </div>

      </section>

      {/* EMPLOYEE COMPENSATION TABLE */}
      <section className="analysis-panel employee-analysis-panel">
        <div className="analysis-panel-heading">
          <div>
            <h3>Employee Compensation Details</h3>
            <p>
              Showing {formatNumber(filteredEmployees.length)} of{" "}
              {formatNumber(employees.length)} analyzed employees
            </p>
          </div>

          <Users size={20} />
        </div>

        <div className="table-responsive">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Level</th>
                <th>Annual Salary</th>
                <th>Band Midpoint</th>
                <th>Compa-Ratio</th>
                <th>Band Position</th>
                <th>Review Status</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="empty-table">
                    Loading employee compensation records...
                  </td>
                </tr>
              ) : filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-table">
                    <EmptyAnalysis
                      icon={Search}
                      title="No employees found"
                      description="Try changing your search or filters."
                    />
                  </td>
                </tr>
              ) : (
                filteredEmployees.slice(0, 100).map((employee) => (
                  <tr key={employee.employee_id}>
                    <td>
                      <strong>{employee.employee_name || "Employee"}</strong>
                      <small className="employee-id-label">
                        ID: {employee.employee_id}
                      </small>
                    </td>

                    <td>
                      {employee.level_id != null
                        ? `Level ${employee.level_id}`
                        : "—"}
                    </td>

                    <td>
                      {formatINR(employee.normalized_salary_inr)}
                    </td>

                    <td>
                      {formatINR(employee.band_midpoint_inr)}
                    </td>

                    <td>
                      <strong>
                        {Number(employee.compa_ratio).toFixed(1)}%
                      </strong>
                    </td>

                    <td>
                      {Number.isFinite(Number(employee.band_position))
                        ? `${Number(employee.band_position).toFixed(1)}%`
                        : "—"}
                    </td>

                    <td>
                      {employee.requires_hr_review ? (
                        <span className="severity-badge medium">
                          Needs Review
                        </span>
                      ) : (
                        <span className="alert-status">
                          Within Checks
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {!loading && filteredEmployees.length > 100 && (
          <p className="analysis-table-note">
            Showing first 100 records. Export CSV to download all{" "}
            {formatNumber(filteredEmployees.length)} filtered records.
          </p>
        )}
      </section>

      {/* ANALYSIS STATUS */}
      <section className="analysis-status-panel">
        <div className="analysis-status-icon">
          <ShieldCheck size={23} />
        </div>

        <div className="analysis-status-content">
          <h3>Analysis Workspace</h3>
          <p>
            Data is loaded from the live compensation analysis API.
            Use filters to explore employee salary, band position
            and potential disparities.
          </p>
        </div>

        <button
          className="analysis-run-btn"
          onClick={fetchAnalysis}
          disabled={loading}
        >
          Refresh Analysis
          <RefreshCw size={17} />
        </button>
      </section>

    </div>
  );
}
