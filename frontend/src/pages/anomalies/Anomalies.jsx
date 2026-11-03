
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Search,
  Filter,
  ShieldAlert,
  AlertCircle,
  AlertOctagon,
  Eye,
  RefreshCw,
  Download,
  X,
  Users,
  IndianRupee,
  Target,
  CircleAlert,
} from "lucide-react";

import api from "../../services/api.js";

const getResponseData = (response) =>
  response?.data?.data ?? response?.data ?? {};

const formatINR = (value) =>
  `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;

const formatNumber = (value) =>
  Number(value || 0).toLocaleString("en-IN");

const formatIssue = (type) => {
  const labels = {
    BELOW_BAND_MINIMUM: "Below Band Minimum",
    LOW_COMPA_RATIO: "Low Compa-Ratio",
    PEER_PAY_GAP: "Peer Pay Gap",
  };

  return labels[type] || type?.replaceAll("_", " ") || "Review Required";
};

const normalizeSeverity = (severity) => {
  const value = String(severity || "").toUpperCase();

  if (value === "HIGH") return "High";
  if (value === "MEDIUM") return "Medium";
  if (value === "LOW") return "Low";

  return "Not Specified";
};

const buildAnomalies = (employees) => {
  const records = [];

  employees.forEach((employee) => {
    if (!employee.requires_hr_review) return;

    const issues = Array.isArray(employee.potential_issues)
      ? employee.potential_issues
      : [];

    issues.forEach((issue, index) => {
      records.push({
        id: `${employee.employee_id}-${issue.type}-${index}`,
        employee_id: employee.employee_id,
        employee_name: employee.employee_name || "Employee",
        level_id: employee.level_id,
        role_id: employee.role_id,
        alert_type: issue.type,
        severity: normalizeSeverity(issue.severity),
        description:
          issue.message || formatIssue(issue.type),
        compa_ratio: Number(employee.compa_ratio),
        salary: Number(employee.normalized_salary_inr),
        band_minimum: Number(employee.band_minimum_inr),
        band_midpoint: Number(employee.band_midpoint_inr),
        band_maximum: Number(employee.band_maximum_inr),
        band_position: Number(employee.band_position),
        performance_rating: employee.performance_rating,
        peer_group_size: employee.peer_group_size,
        peer_median_salary: Number(employee.peer_median_salary_inr),
        status: "Needs HR Review",
      });
    });
  });

  return records;
};

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [type, setType] = useState("all");
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAnomalies = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/api/analysis/results");
      const responseData = getResponseData(response);

      const employees = Array.isArray(responseData.results)
        ? responseData.results
        : [];

      setAnomalies(buildAnomalies(employees));
    } catch (err) {
      console.error("Anomaly loading error:", err);

      setError(
        err.response?.data?.message ||
          "Unable to load anomaly records. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnomalies();
  }, [fetchAnomalies]);

  const filteredAnomalies = useMemo(() => {
    return anomalies.filter((item) => {
      const searchText = search.trim().toLowerCase();

      const matchesSearch =
        !searchText ||
        `${item.employee_name} ${item.employee_id}`
          .toLowerCase()
          .includes(searchText);

      const matchesSeverity =
        severity === "all" ||
        item.severity === severity;

      const matchesType =
        type === "all" ||
        item.alert_type === type;

      return matchesSearch && matchesSeverity && matchesType;
    });
  }, [anomalies, search, severity, type]);

  const stats = useMemo(() => {
    const high = anomalies.filter(
      (item) => item.severity === "High"
    ).length;

    const medium = anomalies.filter(
      (item) => item.severity === "Medium"
    ).length;

    const affectedEmployees = new Set(
      anomalies.map((item) => item.employee_id)
    ).size;

    return {
      total: anomalies.length,
      high,
      medium,
      affectedEmployees,
    };
  }, [anomalies]);

  const resetFilters = () => {
    setSearch("");
    setSeverity("all");
    setType("all");
  };

  const exportAnomalies = () => {
    if (filteredAnomalies.length === 0) return;

    const headers = [
      "Employee ID",
      "Employee Name",
      "Level",
      "Anomaly Type",
      "Severity",
      "Description",
      "Annual Compensation INR",
      "Band Minimum INR",
      "Band Midpoint INR",
      "Band Maximum INR",
      "Compa Ratio",
      "Band Position",
      "Status",
    ];

    const rows = filteredAnomalies.map((item) => [
      item.employee_id,
      item.employee_name,
      item.level_id,
      formatIssue(item.alert_type),
      item.severity,
      item.description,
      item.salary,
      item.band_minimum,
      item.band_midpoint,
      item.band_maximum,
      item.compa_ratio,
      item.band_position,
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
    link.download = "compvista-anomalies.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  };

  const severityClass = (value) =>
    value === "High"
      ? "high"
      : value === "Medium"
        ? "medium"
        : value === "Low"
          ? "low"
          : "unspecified";

  return (
    <div className="anomalies-page">

      {/* PAGE HEADER */}
      <section className="anomalies-header">
        <div className="anomalies-heading">
          <div className="anomalies-heading-icon">
            <AlertTriangle size={27} />
          </div>

          <div>
            <h1>Anomaly Detection</h1>
            <p>
              Identify compensation disparities and investigate
              unusual salary patterns.
            </p>
          </div>
        </div>

        <div className="anomalies-header-actions">
          <button
            type="button"
            className="anomalies-refresh-btn"
            onClick={fetchAnomalies}
            disabled={loading}
          >
            <RefreshCw size={17} />
            Refresh Analysis
          </button>

          <button
            type="button"
            className="employees-export-btn"
            onClick={exportAnomalies}
            disabled={loading || filteredAnomalies.length === 0}
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
          <button onClick={fetchAnomalies}>Retry</button>
        </div>
      )}

      {/* STATISTICS */}
      <section className="anomalies-stats">

        <div className="anomaly-stat-card">
          <div className="anomaly-stat-icon blue">
            <AlertTriangle size={23} />
          </div>
          <div>
            <span>Total Anomalies</span>
            <h2>{loading ? "—" : formatNumber(stats.total)}</h2>
            <p>Detected compensation issues</p>
          </div>
        </div>

        <div className="anomaly-stat-card">
          <div className="anomaly-stat-icon red">
            <AlertOctagon size={23} />
          </div>
          <div>
            <span>High Severity</span>
            <h2>{loading ? "—" : formatNumber(stats.high)}</h2>
            <p>Backend-classified high severity</p>
          </div>
        </div>

        <div className="anomaly-stat-card">
          <div className="anomaly-stat-icon amber">
            <AlertCircle size={23} />
          </div>
          <div>
            <span>Medium Severity</span>
            <h2>{loading ? "—" : formatNumber(stats.medium)}</h2>
            <p>Backend-classified medium severity</p>
          </div>
        </div>

        <div className="anomaly-stat-card">
          <div className="anomaly-stat-icon green">
            <Users size={23} />
          </div>
          <div>
            <span>Affected Employees</span>
            <h2>
              {loading ? "—" : formatNumber(stats.affectedEmployees)}
            </h2>
            <p>Unique employees requiring review</p>
          </div>
        </div>

      </section>

      {/* ANOMALY DIRECTORY */}
      <section className="anomalies-directory">

        <div className="anomalies-section-heading">
          <div>
            <h3>Detected Anomalies</h3>
            <p>
              Review employee-level compensation irregularities.
            </p>
          </div>

          <span className="anomaly-record-count">
            {loading
              ? "Loading..."
              : `${formatNumber(filteredAnomalies.length)} Records`}
          </span>
        </div>

        {/* FILTERS */}
        <div className="anomalies-filters">

          <div className="anomalies-search">
            <Search size={18} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search employee name or ID..."
            />
          </div>

          <div className="anomaly-filter-control">
            <Filter size={17} />
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option value="all">All Severities</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
              <option value="Not Specified">Not Specified</option>
            </select>
          </div>

          <div className="anomaly-filter-control">
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
            >
              <option value="all">All Anomaly Types</option>
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

          {(search || severity !== "all" || type !== "all") && (
            <button
              type="button"
              className="analysis-outline-btn"
              onClick={resetFilters}
            >
              <X size={15} />
              Clear
            </button>
          )}
        </div>

        {/* TABLE */}
        <div className="anomalies-table-wrapper">
          <table className="anomalies-table">
            <thead>
              <tr>
                <th>EMPLOYEE</th>
                <th>JOB LEVEL</th>
                <th>ANOMALY TYPE</th>
                <th>COMPA-RATIO</th>
                <th>SEVERITY</th>
                <th>STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7">
                    <div className="anomalies-empty-state">
                      <RefreshCw size={27} />
                      <h3>Loading anomaly records...</h3>
                      <p>Fetching live compensation analysis.</p>
                    </div>
                  </td>
                </tr>
              ) : filteredAnomalies.length === 0 ? (
                <tr>
                  <td colSpan="7">
                    <div className="anomalies-empty-state">
                      <div className="anomalies-empty-icon">
                        <ShieldAlert size={30} />
                      </div>
                      <h3>No anomaly records found</h3>
                      <p>
                        Try changing your search or filters.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredAnomalies.slice(0, 100).map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.employee_name}</strong>
                      <small className="employee-id-label">
                        ID: {item.employee_id}
                      </small>
                    </td>

                    <td>
                      {item.level_id != null
                        ? `Level ${item.level_id}`
                        : "—"}
                    </td>

                    <td>{formatIssue(item.alert_type)}</td>

                    <td>
                      {Number.isFinite(item.compa_ratio)
                        ? `${item.compa_ratio.toFixed(1)}%`
                        : "—"}
                    </td>

                    <td>
                      <span
                        className={`anomaly-severity-badge ${severityClass(item.severity)}`}
                      >
                        {item.severity}
                      </span>
                    </td>

                    <td>
                      <span className="alert-status">
                        {item.status}
                      </span>
                    </td>

                    <td>
                      <button
                        type="button"
                        className="anomaly-view-btn"
                        title="View anomaly details"
                        onClick={() => setSelectedAnomaly(item)}
                      >
                        <Eye size={17} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {!loading && filteredAnomalies.length > 100 && (
          <p className="analysis-table-note">
            Showing first 100 records. Export CSV downloads all{" "}
            {formatNumber(filteredAnomalies.length)} filtered records.
          </p>
        )}
      </section>

      {/* RISK MONITORING INFORMATION */}
      <section className="anomaly-info-panel">
        <div className="anomaly-info-icon">
          <ShieldAlert size={23} />
        </div>
        <div>
          <h4>Compensation Risk Monitoring</h4>
          <p>
            Monitor below-band salaries, low compa-ratios and peer pay
            gaps to support fair and consistent compensation decisions.
          </p>
        </div>
      </section>

      {/* ANOMALY DETAILS MODAL */}
      {selectedAnomaly && (
        <div
          className="employee-modal-overlay"
          onClick={() => setSelectedAnomaly(null)}
        >
          <div
            className="employee-details-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="anomaly-modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="employee-modal-header">
              <div>
                <div className="anomalies-heading-icon">
                  <AlertTriangle size={24} />
                </div>
                <h2 id="anomaly-modal-title">Anomaly Details</h2>
                <p>Compensation issue and employee information</p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedAnomaly(null)}
                aria-label="Close anomaly details"
              >
                <X size={21} />
              </button>
            </div>

            <div className="employee-modal-identity">
              <h3>{selectedAnomaly.employee_name}</h3>
              <span>Employee ID: {selectedAnomaly.employee_id}</span>
              <span>
                {selectedAnomaly.level_id != null
                  ? `Level ${selectedAnomaly.level_id}`
                  : "Level unavailable"}
              </span>
            </div>

            <div className="employee-details-grid">
              <div>
                <span>Anomaly Type</span>
                <strong>{formatIssue(selectedAnomaly.alert_type)}</strong>
              </div>

              <div>
                <span>Severity</span>
                <strong>{selectedAnomaly.severity}</strong>
              </div>

              <div>
                <span>Annual Compensation</span>
                <strong>{formatINR(selectedAnomaly.salary)}</strong>
              </div>

              <div>
                <span>Compa-Ratio</span>
                <strong>
                  {Number.isFinite(selectedAnomaly.compa_ratio)
                    ? `${selectedAnomaly.compa_ratio.toFixed(2)}%`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Band Minimum</span>
                <strong>{formatINR(selectedAnomaly.band_minimum)}</strong>
              </div>

              <div>
                <span>Band Midpoint</span>
                <strong>{formatINR(selectedAnomaly.band_midpoint)}</strong>
              </div>

              <div>
                <span>Band Maximum</span>
                <strong>{formatINR(selectedAnomaly.band_maximum)}</strong>
              </div>

              <div>
                <span>Peer Median Salary</span>
                <strong>{formatINR(selectedAnomaly.peer_median_salary)}</strong>
              </div>

              <div>
                <span>Performance Rating</span>
                <strong>{selectedAnomaly.performance_rating ?? "—"}</strong>
              </div>

              <div>
                <span>Peer Group Size</span>
                <strong>{selectedAnomaly.peer_group_size ?? "—"}</strong>
              </div>
            </div>

            <div className="employee-modal-issues">
              <h4>
                <AlertCircle size={18} />
                Issue Description
              </h4>
              <div className="employee-issue-item">
                <strong>{formatIssue(selectedAnomaly.alert_type)}</strong>
                <span>{selectedAnomaly.description}</span>
              </div>
            </div>

            <div className="employee-modal-footer">
              <span className="alert-status">
                {selectedAnomaly.status}
              </span>

              <button
                type="button"
                className="analysis-outline-btn"
                onClick={() => setSelectedAnomaly(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
