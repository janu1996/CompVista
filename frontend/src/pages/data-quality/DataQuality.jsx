
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Database,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
  Download,
  FileWarning,
} from "lucide-react";

import api from "../../services/api.js";

const formatNumber = (value) =>
  Number(value || 0).toLocaleString("en-IN");

const formatIssueName = (key) => {
  const labels = {
    missing_salary: "Missing Salary",
    multiple_active_salary_records: "Multiple Active Salary Records",
    missing_or_inactive_band: "Missing or Inactive Band",
    employee_band_mismatch: "Employee Band Mismatch",
    currency_mismatch: "Currency Mismatch",
    invalid_salary_or_fte: "Invalid Salary or FTE",
    invalid_band: "Invalid Band",
    missing_fx_rate: "Missing FX Rate",
  };

  return labels[key] ||
    String(key).replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
};

export default function DataQuality() {
  const [search, setSearch] = useState("");
  const [issueType, setIssueType] = useState("all");

  const [summary, setSummary] = useState(null);
  const [issues, setIssues] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchQualityData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/api/analysis/summary");

      const responseData =
        response?.data?.data ?? response?.data ?? {};

      const summaryData =
        responseData.summary ?? responseData;

      setSummary(summaryData);

      const rawIssues =
        summaryData.data_quality_issues ??
        responseData.data_quality_issues ??
        {};

      const issueRecords = Object.entries(rawIssues)
        .map(([key, value]) => {
          const count =
            typeof value === "number"
              ? value
              : Number(value?.count ?? value?.total ?? 0);

          return {
            id: key,
            issue_type: key,
            issue_name: formatIssueName(key),
            count: Number.isFinite(count) ? count : 0,
            description:
              key === "missing_fx_rate"
                ? "Employees excluded from compensation analysis because an applicable foreign exchange rate was unavailable."
                : `${formatIssueName(key)} detected in the data quality summary.`,
            severity: "Not Classified",
            status: "Requires Review",
          };
        })
        .filter((item) => item.count > 0);

      setIssues(issueRecords);
    } catch (err) {
      console.error("Data quality loading error:", err);

      setError(
        err.response?.data?.message ||
          "Unable to load data quality information. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQualityData();
  }, [fetchQualityData]);

  const analyzed = Number(summary?.employees_analyzed || 0);
  const excluded = Number(summary?.employees_excluded || 0);
  const total = analyzed + excluded;

  const totalIssues = issues.reduce(
    (sum, item) => sum + item.count,
    0
  );

  const filteredIssues = useMemo(() => {
    return issues.filter((item) => {
      const text = search.trim().toLowerCase();

      const matchesSearch =
        !text ||
        `${item.issue_name} ${item.description} ${item.issue_type}`
          .toLowerCase()
          .includes(text);

      const matchesType =
        issueType === "all" ||
        item.issue_type === issueType;

      return matchesSearch && matchesType;
    });
  }, [issues, search, issueType]);

  const analysisPercentage =
    total > 0 ? (analyzed / total) * 100 : 0;

  const exportCSV = () => {
    if (filteredIssues.length === 0) return;

    const headers = [
      "Issue Type",
      "Affected Records",
      "Description",
      "Severity",
      "Status",
    ];

    const rows = filteredIssues.map((item) => [
      item.issue_name,
      item.count,
      item.description,
      item.severity,
      item.status,
    ]);

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
    link.download = "compvista-data-quality.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  };

  const clearFilters = () => {
    setSearch("");
    setIssueType("all");
  };

  return (
    <div className="data-quality-page">

      {/* PAGE HEADER */}
      <section className="data-quality-header">
        <div className="data-quality-heading">
          <div className="data-quality-heading-icon">
            <Database size={27} />
          </div>

          <div>
            <h1>Data Quality Monitoring</h1>
            <p>
              Validate employee compensation data and identify
              data integrity issues.
            </p>
          </div>
        </div>

        <div className="quality-header-actions">
          <button
            type="button"
            className="quality-refresh-btn"
            onClick={fetchQualityData}
            disabled={loading}
          >
            <RefreshCw size={17} />
            Run Validation
          </button>

          <button
            type="button"
            className="quality-export-btn"
            onClick={exportCSV}
            disabled={loading || filteredIssues.length === 0}
          >
            <Download size={17} />
            Export CSV
          </button>
        </div>
      </section>

      {/* ERROR */}
      {error && (
        <div className="quality-error">
          <AlertCircle size={19} />
          <span>{error}</span>
          <button onClick={fetchQualityData}>Retry</button>
        </div>
      )}

      {/* STATISTICS */}
      <section className="quality-stats">

        <div className="quality-stat-card">
          <div className="quality-stat-icon blue">
            <Database size={23} />
          </div>
          <div>
            <span>Analysis Records</span>
            <h2>{loading ? "—" : formatNumber(total)}</h2>
            <p>Analyzed and excluded records</p>
          </div>
        </div>

        <div className="quality-stat-card">
          <div className="quality-stat-icon green">
            <CheckCircle2 size={23} />
          </div>
          <div>
            <span>Analyzed Records</span>
            <h2>{loading ? "—" : formatNumber(analyzed)}</h2>
            <p>Successfully analyzed</p>
          </div>
        </div>

        <div className="quality-stat-card">
          <div className="quality-stat-icon amber">
            <AlertTriangle size={23} />
          </div>
          <div>
            <span>Excluded Records</span>
            <h2>{loading ? "—" : formatNumber(excluded)}</h2>
            <p>Excluded from analysis</p>
          </div>
        </div>

        <div className="quality-stat-card">
          <div className="quality-stat-icon red">
            <FileWarning size={23} />
          </div>
          <div>
            <span>Quality Issues</span>
            <h2>{loading ? "—" : formatNumber(totalIssues)}</h2>
            <p>Reported data quality issues</p>
          </div>
        </div>

      </section>

      {/* QUALITY OVERVIEW */}
      <section className="quality-overview">

        <div className="quality-overview-heading">
          <div>
            <h3>Data Quality Overview</h3>
            <p>
              Monitor the analysis coverage and reported data issues.
            </p>
          </div>

          <span className="quality-status-label">
            <ShieldCheck size={15} />
            {loading ? "Loading..." : "Backend Summary"}
          </span>
        </div>

        {loading ? (
          <div className="quality-empty-overview">
            <RefreshCw size={28} />
            <h3>Loading quality metrics...</h3>
            <p>Retrieving actual validation summary.</p>
          </div>
        ) : error ? (
          <div className="quality-empty-overview">
            <AlertCircle size={30} />
            <h3>Quality metrics unavailable</h3>
            <p>Refresh to try loading the backend summary again.</p>
          </div>
        ) : (
          <div className="quality-metrics-content">

            <div className="quality-progress-heading">
              <div>
                <span>Analysis Coverage</span>
                <strong>{analysisPercentage.toFixed(1)}%</strong>
              </div>
              <span>
                {formatNumber(analyzed)} of {formatNumber(total)} records
              </span>
            </div>

            <div className="quality-progress-track">
              <div
                className="quality-progress-fill"
                style={{ width: `${analysisPercentage}%` }}
              />
            </div>

            <div className="quality-overview-cards">
              <div>
                <CheckCircle2 size={20} />
                <span>Analyzed</span>
                <strong>{formatNumber(analyzed)}</strong>
              </div>

              <div>
                <AlertTriangle size={20} />
                <span>Excluded</span>
                <strong>{formatNumber(excluded)}</strong>
              </div>

              <div>
                <ShieldCheck size={20} />
                <span>Reported Issues</span>
                <strong>{formatNumber(totalIssues)}</strong>
              </div>
            </div>

            <p className="quality-overview-note">
              Analysis coverage represents the proportion of records
              analyzed out of analyzed plus excluded records. It is
              not a complete data validation pass rate.
            </p>

          </div>
        )}
      </section>

      {/* QUALITY ISSUES */}
      <section className="quality-issues-panel">

        <div className="quality-section-heading">
          <div>
            <h3>Data Quality Issues</h3>
            <p>
              Review issue categories and their affected record counts.
            </p>
          </div>

          <span className="quality-record-count">
            {loading
              ? "Loading..."
              : `${formatNumber(filteredIssues.length)} Categories`}
          </span>
        </div>

        {/* FILTERS */}
        <div className="quality-filters">

          <div className="quality-search">
            <Search size={18} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search issue type or description..."
            />
          </div>

          <div className="quality-filter-control">
            <Filter size={17} />

            <select
              value={issueType}
              onChange={(e) => setIssueType(e.target.value)}
            >
              <option value="all">All Issue Types</option>

              {issues.map((item) => (
                <option key={item.id} value={item.issue_type}>
                  {item.issue_name}
                </option>
              ))}
            </select>
          </div>

          {(search || issueType !== "all") && (
            <button
              type="button"
              className="quality-clear-btn"
              onClick={clearFilters}
            >
              Clear Filters
            </button>
          )}

        </div>

        {/* TABLE */}
        <div className="quality-table-wrapper">
          <table className="quality-table">
            <thead>
              <tr>
                <th>ISSUE CATEGORY</th>
                <th>AFFECTED RECORDS</th>
                <th>DESCRIPTION</th>
                <th>SEVERITY</th>
                <th>STATUS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5">
                    <div className="quality-empty-state">
                      <RefreshCw size={28} />
                      <h3>Loading data quality records...</h3>
                      <p>Connecting to backend validation summary.</p>
                    </div>
                  </td>
                </tr>
              ) : filteredIssues.length === 0 ? (
                <tr>
                  <td colSpan="5">
                    <div className="quality-empty-state">
                      <div className="quality-empty-icon">
                        <ShieldCheck size={30} />
                      </div>
                      <h3>No reported issues found</h3>
                      <p>
                        There are no issue categories matching
                        your current search or filters.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredIssues.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.issue_name}</strong>
                      <small className="quality-issue-code">
                        {item.issue_type}
                      </small>
                    </td>

                    <td>
                      <span className="quality-count-badge">
                        {formatNumber(item.count)}
                      </span>
                    </td>

                    <td>{item.description}</td>

                    <td>
                      <span className="quality-severity-badge">
                        {item.severity}
                      </span>
                    </td>

                    <td>
                      <span className="quality-issue-status">
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

      </section>

      {/* INFORMATION PANEL */}
      <section className="quality-info-panel">
        <div className="quality-info-icon">
          <ShieldCheck size={23} />
        </div>

        <div>
          <h4>Data Integrity & Reliability</h4>
          <p>
            Reliable compensation analysis depends on accurate employee
            records, salary information, compensation bands and currency
            conversion rates. Review excluded records before making
            compensation decisions.
          </p>
        </div>
      </section>

    </div>
  );
}
