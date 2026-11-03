
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Download,
  FileText,
  ShieldCheck,
  Zap,
  TrendingUp,
} from "lucide-react";

import api from "../../services/api";
import StatCard from "../../components/dashboard/StatCard";
import CompensationChart from "../../components/charts/CompensationChart";
import DistributionChart from "../../components/charts/DistributionChart";
import PayEquityGauge from "../../components/charts/PayEquityGauge";

const initialSummary = {
  employees_analyzed: 0,
  employees_flagged: 0,
  employees_excluded: 0,
  data_quality_issues: {},
  analysis_date: null,
  reporting_currency: "INR",
  peer_pay_gap: 0,
};

const buildLevelChart = (results) => {
  const groups = {};

  results.forEach((item) => {
    const level = item.level_id;
    const salary = Number(item.normalized_salary_inr);

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
      average_compensation: Math.round(
        values.total / values.count
      ),
    }))
    .sort(
      (a, b) =>
        Number(a.level.replace("Level ", "")) -
        Number(b.level.replace("Level ", ""))
    );
};

const buildDistributionChart = (results) => {
  const ranges = [
    { range: "Below 80%", min: -Infinity, max: 80 },
    { range: "80% - 100%", min: 80, max: 100 },
    { range: "100% - 120%", min: 100, max: 120 },
    { range: "Above 120%", min: 120, max: Infinity },
  ];

  const counts = ranges.map((range) => ({
    range: range.range,
    employee_count: 0,
  }));

  results.forEach((item) => {
    const ratio = Number(item.compa_ratio);

    if (!Number.isFinite(ratio) || ratio <= 0) return;

    const index = ranges.findIndex(
      (range) => ratio >= range.min && ratio < range.max
    );

    if (index !== -1) {
      counts[index].employee_count += 1;
    }
  });

  return counts;
};

const buildEquityScore = (results) => {
  const validResults = results.filter((item) => {
    const ratio = Number(item.compa_ratio);
    return Number.isFinite(ratio) && ratio > 0;
  });

  if (validResults.length === 0) return null;

  const withinTarget = validResults.filter((item) => {
    const ratio = Number(item.compa_ratio);
    return ratio >= 80 && ratio <= 120;
  }).length;

  return (withinTarget / validResults.length) * 100;
};

const buildRecentAlerts = (results) => {
  const alerts = [];

  results.forEach((employee) => {
    if (!employee.requires_hr_review) return;

    const issues = Array.isArray(employee.potential_issues)
      ? employee.potential_issues
      : [];

    issues.forEach((issue, index) => {
      alerts.push({
        id: `${employee.employee_id}-${issue.type}-${index}`,
        employee_name: employee.employee_name || "Employee",
        employee_id: employee.employee_id,
        level: employee.level_id,
        alert_type: issue.type,
        message: issue.message,
        severity: issue.severity || "MEDIUM",
        compa_ratio: Number(employee.compa_ratio),
      });
    });
  });

  const severityOrder = {
    HIGH: 0,
    MEDIUM: 1,
    LOW: 2,
  };

  return alerts
    .sort((a, b) => {
      const severityDifference =
        (severityOrder[a.severity] ?? 3) -
        (severityOrder[b.severity] ?? 3);

      if (severityDifference !== 0) {
        return severityDifference;
      }

      return (a.compa_ratio || 0) - (b.compa_ratio || 0);
    })
    .slice(0, 5);
};

const getResponseData = (response) =>
  response?.data?.data ?? response?.data ?? {};

const formatINR = (value) =>
  `₹${Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;

export default function Dashboard() {
  const [summary, setSummary] = useState(initialSummary);
  const [compensationData, setCompensationData] = useState([]);
  const [distributionData, setDistributionData] = useState([]);
  const [equityScore, setEquityScore] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const fetchDashboardData = async () => {
      setLoading(true);
      setError("");

      try {
        const [summaryResponse, resultsResponse] =
          await Promise.allSettled([
            api.get("/api/analysis/summary"),
            api.get("/api/analysis/results"),
          ]);

        if (!active) return;

        if (summaryResponse.status === "fulfilled") {
          const summaryData = getResponseData(
            summaryResponse.value
          );

          setSummary({
            ...initialSummary,
            ...summaryData,
          });
        } else {
          throw summaryResponse.reason;
        }

        if (resultsResponse.status === "fulfilled") {
          const resultsData = getResponseData(
            resultsResponse.value
          );

          const results = Array.isArray(resultsData.results)
            ? resultsData.results
            : [];

          setCompensationData(buildLevelChart(results));
          setDistributionData(buildDistributionChart(results));
          setEquityScore(buildEquityScore(results));
          setRecentAlerts(buildRecentAlerts(results));
        } else {
          setCompensationData([]);
          setDistributionData([]);
          setEquityScore(null);
          setRecentAlerts([]);

          setError(
            "Summary loaded, but employee analysis details could not be fetched."
          );
        }
      } catch (err) {
        if (!active) return;

        console.error("Dashboard loading error:", err);

        setError(
          err.response?.data?.message ||
          "Unable to load dashboard data. Please try again."
        );
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchDashboardData();

    return () => {
      active = false;
    };
  }, []);

  const missingFxRates =
    Number(summary.data_quality_issues?.missing_fx_rate) || 0;

  const quickActions = [
    {
      title: "Run Analysis",
      description: "Detect pay gaps and anomalies",
      icon: BarChart3,
      path: "/compensation",
      color: "blue",
    },
    {
      title: "Create Proposal",
      description: "Adjust compensation",
      icon: FileText,
      path: "/proposals",
      color: "cyan",
    },
    {
      title: "Export Data",
      description: "Download reports and records",
      icon: Download,
      path: "/reports",
      color: "purple",
    },
    {
      title: "View Approvals",
      description: "Pending compensation requests",
      icon: ShieldCheck,
      path: "/approvals",
      color: "green",
    },
  ];

  const formatDate = (date) => {
    if (!date) return "Not available";

    return new Date(`${date}T00:00:00`).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };

  const formatIssueType = (type) => {
    const labels = {
      BELOW_BAND_MINIMUM: "Below Band Minimum",
      LOW_COMPA_RATIO: "Low Compa-Ratio",
      PEER_PAY_GAP: "Peer Pay Gap",
    };

    return labels[type] || type?.replaceAll("_", " ") || "Review Required";
  };

  return (
    <div className="dashboard-page">

      {/* KPI CARDS */}
      <section className="stats-grid">
        <StatCard
          title="Employees Analyzed"
          value={summary.employees_analyzed}
          icon="employees"
          accent="blue"
          subtitle="Successfully analyzed workforce"
          loading={loading}
        />

        <StatCard
          title="Equity Alerts"
          value={summary.employees_flagged}
          icon="alerts"
          accent="red"
          subtitle="Employees flagged for review"
          loading={loading}
        />

        <StatCard
          title="Employees Excluded"
          value={summary.employees_excluded}
          icon="ratio"
          accent="green"
          subtitle="Excluded from current analysis"
          loading={loading}
        />

        <StatCard
          title="Missing FX Rates"
          value={missingFxRates}
          icon="proposals"
          accent="purple"
          subtitle="Data quality issues requiring review"
          loading={loading}
        />
      </section>

      {error && (
        <div className="dashboard-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* ANALYTICS CHARTS */}
      <section className="analytics-grid">
        <CompensationChart
          data={compensationData}
          loading={loading}
        />

        <DistributionChart
          data={distributionData}
          loading={loading}
        />

        <PayEquityGauge
          value={equityScore}
          loading={loading}
        />
      </section>

      {/* BOTTOM DASHBOARD */}
      <section className="dashboard-bottom-grid">

        {/* RECENT EQUITY ALERTS */}
        <div className="dashboard-section alerts-panel">
          <div className="section-heading">
            <div className="section-heading-title">
              <div className="section-title-icon red-icon">
                <AlertTriangle size={22} />
              </div>

              <div>
                <h3>Recent Equity Alerts</h3>
                <p>
                  Actual employees and issues requiring HR review.
                </p>
              </div>
            </div>

            <Link to="/anomalies" className="view-all-link">
              View All <ArrowRight size={16} />
            </Link>
          </div>

          <div className="table-responsive">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Level</th>
                  <th>Issue Type</th>
                  <th>Compa-Ratio</th>
                  <th>Severity</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-table">
                      Loading employee alerts...
                    </td>
                  </tr>
                ) : recentAlerts.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-table">
                      <div className="alerts-empty-state">
                        <div className="alerts-empty-icon">
                          <ShieldCheck size={27} />
                        </div>

                        <strong>No alert data available</strong>

                        <span>
                          No employees currently require HR review.
                        </span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  recentAlerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <strong>{alert.employee_name}</strong>
                      </td>

                      <td>
                        {alert.level != null
                          ? `Level ${alert.level}`
                          : "—"}
                      </td>

                      <td>
                        <span title={alert.message}>
                          {formatIssueType(alert.alert_type)}
                        </span>
                      </td>

                      <td>
                        {Number.isFinite(alert.compa_ratio)
                          ? `${alert.compa_ratio.toFixed(1)}%`
                          : "—"}
                      </td>

                      <td>
                        <span
                          className={`severity-badge ${alert.severity.toLowerCase()}`}
                        >
                          {alert.severity}
                        </span>
                      </td>

                      <td>
                        <span className="alert-status">
                          Needs HR Review
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* QUICK ACTIONS */}
        <div className="dashboard-section quick-actions-panel">
          <div className="section-heading">
            <div className="section-heading-title">
              <div className="section-title-icon amber-icon">
                <Zap size={22} />
              </div>

              <div>
                <h3>Quick Actions</h3>
                <p>Frequently used platform features.</p>
              </div>
            </div>
          </div>

          <div className="quick-actions-grid">
            {quickActions.map((action) => {
              const Icon = action.icon;

              return (
                <Link
                  key={action.title}
                  to={action.path}
                  className={`quick-action-card ${action.color}`}
                >
                  <div className="quick-action-icon">
                    <Icon size={23} />
                  </div>

                  <div className="quick-action-info">
                    <h4>{action.title}</h4>
                    <p>{action.description}</p>
                  </div>

                  <ArrowRight
                    size={19}
                    className="quick-action-arrow"
                  />
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ANALYSIS SUMMARY */}
      <section className="dashboard-section analysis-summary-panel">
        <div className="section-heading">
          <div className="section-heading-title">
            <div className="section-title-icon">
              <TrendingUp size={22} />
            </div>

            <div>
              <h3>Analysis Summary</h3>
              <p>Latest compensation analysis overview.</p>
            </div>
          </div>
        </div>

        <div className="analysis-summary-content">
          <div className="summary-detail">
            <span>Reporting Currency</span>
            <strong>{summary.reporting_currency || "INR"}</strong>
          </div>

          <div className="summary-detail">
            <span>Analysis Date</span>
            <strong>{formatDate(summary.analysis_date)}</strong>
          </div>

          <div className="summary-detail">
            <span>Peer Pay Gap Alerts</span>
            <strong>
              {Number(summary.peer_pay_gap || 0).toLocaleString("en-IN")}
            </strong>
          </div>

          <div className="summary-detail">
            <span>Missing FX Rates</span>
            <strong>{missingFxRates.toLocaleString("en-IN")}</strong>
          </div>
        </div>
      </section>
    </div>
  );
}
