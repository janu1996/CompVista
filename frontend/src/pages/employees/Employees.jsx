
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Users,
  Search,
  SlidersHorizontal,
  Download,
  UserRound,
  RefreshCw,
  Eye,
  X,
  IndianRupee,
  AlertTriangle,
  ShieldCheck,
  CircleAlert,
} from "lucide-react";

import api from "../../services/api.js";

const formatNumber = (value) =>
  Number(value || 0).toLocaleString("en-IN");

const formatINR = (value) =>
  `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;

const getResponseData = (response) =>
  response?.data?.data ?? response?.data ?? {};

const formatIssue = (type) => {
  const labels = {
    BELOW_BAND_MINIMUM: "Below Band Minimum",
    LOW_COMPA_RATIO: "Low Compa-Ratio",
    PEER_PAY_GAP: "Peer Pay Gap",
  };

  return labels[type] || type?.replaceAll("_", " ") || "Review Required";
};

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("all");
  const [reviewStatus, setReviewStatus] = useState("all");
  const [selectedEmployee, setSelectedEmployee] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/api/analysis/results");
      const responseData = getResponseData(response);

      const records = Array.isArray(responseData.results)
        ? responseData.results
        : [];

      setEmployees(records);
    } catch (err) {
      console.error("Employee loading error:", err);
      setError(
        err.response?.data?.message ||
          "Unable to load employee records. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const filteredEmployees = useMemo(() => {
    return employees.filter((employee) => {
      const searchText = search.trim().toLowerCase();

      const matchesSearch =
        !searchText ||
        String(employee.employee_name || "")
          .toLowerCase()
          .includes(searchText) ||
        String(employee.employee_id || "")
          .toLowerCase()
          .includes(searchText);

      const matchesLevel =
        level === "all" || String(employee.level_id) === level;

      const matchesReview =
        reviewStatus === "all" ||
        (reviewStatus === "review" && employee.requires_hr_review) ||
        (reviewStatus === "clear" && !employee.requires_hr_review);

      return matchesSearch && matchesLevel && matchesReview;
    });
  }, [employees, search, level, reviewStatus]);

  const stats = useMemo(() => {
    const total = employees.length;

    const flagged = employees.filter(
      (employee) => employee.requires_hr_review
    ).length;

    const activeLevels = new Set(
      employees
        .map((employee) => employee.level_id)
        .filter((value) => value !== null && value !== undefined)
    );

    const validSalaries = employees
      .map((employee) => Number(employee.normalized_salary_inr))
      .filter((salary) => Number.isFinite(salary) && salary > 0);

    const averageSalary = validSalaries.length
      ? validSalaries.reduce((sum, salary) => sum + salary, 0) /
        validSalaries.length
      : 0;

    return {
      total,
      flagged,
      clear: total - flagged,
      levels: activeLevels.size,
      averageSalary,
    };
  }, [employees]);

  const resetFilters = () => {
    setSearch("");
    setLevel("all");
    setReviewStatus("all");
  };

  const exportEmployees = () => {
    if (filteredEmployees.length === 0) return;

    const headers = [
      "Employee ID",
      "Employee Name",
      "Role ID",
      "Level",
      "Currency",
      "Annual Compensation INR",
      "Band Minimum INR",
      "Band Midpoint INR",
      "Band Maximum INR",
      "Compa Ratio",
      "Band Position",
      "Requires HR Review",
      "Potential Issues",
    ];

    const rows = filteredEmployees.map((employee) => [
      employee.employee_id,
      employee.employee_name,
      employee.role_id,
      employee.level_id,
      "INR",
      employee.normalized_salary_inr,
      employee.band_minimum_inr,
      employee.band_midpoint_inr,
      employee.band_maximum_inr,
      employee.compa_ratio,
      employee.band_position,
      employee.requires_hr_review ? "Yes" : "No",
      (employee.potential_issues || [])
        .map((issue) => formatIssue(issue.type))
        .join("; "),
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
    link.download = "compvista-employees.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  };

  const modalOverlayStyle = {
    position: "fixed",
    inset: 0,
    zIndex: 9999,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "20px",
    background: "rgba(2, 10, 27, 0.84)",
    backdropFilter: "blur(8px)",
  };

  const modalStyle = {
    width: "100%",
    maxWidth: "680px",
    maxHeight: "85vh",
    overflowY: "auto",
    padding: "26px",
    border: "1px solid #168bd0",
    borderRadius: "18px",
    background: "linear-gradient(145deg, #12345e, #071a35)",
    color: "#eef7ff",
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
  };

  return (
    <div className="employees-page">
      {/* PAGE HEADER */}
      <section className="employees-header">
        <div className="employees-heading">
          <div className="employees-heading-icon">
            <Users size={27} />
          </div>

          <div>
            <h1>Employee Management</h1>
            <p>
              View and review employee compensation records across
              your organization.
            </p>
          </div>
        </div>

        <div className="employees-header-actions">
          <button
            type="button"
            className="analysis-outline-btn"
            onClick={fetchEmployees}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Refresh
          </button>

          <button
            type="button"
            className="employees-export-btn"
            onClick={exportEmployees}
            disabled={loading || filteredEmployees.length === 0}
            style={{
              opacity:
                loading || filteredEmployees.length === 0 ? 0.5 : 1,
              cursor:
                loading || filteredEmployees.length === 0
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            <Download size={17} />
            Export Employees
          </button>
        </div>
      </section>

      {/* ERROR */}
      {error && (
        <div className="analysis-error">
          <CircleAlert size={19} />
          <span>{error}</span>
          <button type="button" onClick={fetchEmployees}>
            Retry
          </button>
        </div>
      )}

      {/* STATISTICS */}
      <section className="employees-stats">
        <div className="employee-stat-card">
          <div className="employee-stat-icon blue">
            <Users size={23} />
          </div>
          <div>
            <span>Analyzed Employees</span>
            <h2>{loading ? "—" : formatNumber(stats.total)}</h2>
            <p>Records in current analysis</p>
          </div>
        </div>

        <div className="employee-stat-card">
          <div className="employee-stat-icon cyan">
            <ShieldCheck size={23} />
          </div>
          <div>
            <span>Without Review Flags</span>
            <h2>{loading ? "—" : formatNumber(stats.clear)}</h2>
            <p>No current HR review flag</p>
          </div>
        </div>

        <div className="employee-stat-card">
          <div className="employee-stat-icon purple">
            <SlidersHorizontal size={23} />
          </div>
          <div>
            <span>Job Levels</span>
            <h2>{loading ? "—" : formatNumber(stats.levels)}</h2>
            <p>Levels represented in analysis</p>
          </div>
        </div>

        <div className="employee-stat-card">
          <div className="employee-stat-icon amber">
            <IndianRupee size={23} />
          </div>
          <div>
            <span>Average Compensation</span>
            <h2>{loading ? "—" : formatINR(stats.averageSalary)}</h2>
            <p>Average annual INR-normalized salary</p>
          </div>
        </div>
      </section>

      {/* EMPLOYEE DIRECTORY */}
      <section className="employees-directory">
        <div className="employees-section-heading">
          <div>
            <h3>Employee Directory</h3>
            <p>Search and review employee compensation information.</p>
          </div>

          <span className="employee-record-count">
            {loading
              ? "Loading..."
              : `${formatNumber(filteredEmployees.length)} Records`}
          </span>
        </div>

        {/* FILTERS */}
        <div className="employees-filters">
          <div className="employees-search">
            <Search size={18} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by employee name or ID..."
            />
          </div>

          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          >
            <option value="all">All Job Levels</option>
            {[1, 2, 3, 4, 5].map((item) => (
              <option key={item} value={String(item)}>
                Level {item}
              </option>
            ))}
          </select>

          <select
            value={reviewStatus}
            onChange={(e) => setReviewStatus(e.target.value)}
          >
            <option value="all">All Review Statuses</option>
            <option value="review">Needs HR Review</option>
            <option value="clear">No Review Flag</option>
          </select>

          {(search || level !== "all" || reviewStatus !== "all") && (
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

        {/* EMPLOYEE TABLE */}
        <div className="employees-table-wrapper">
          <table className="employees-table">
            <thead>
              <tr>
                <th>EMPLOYEE</th>
                <th>JOB LEVEL</th>
                <th>ANNUAL COMPENSATION</th>
                <th>BAND MIDPOINT</th>
                <th>COMPA-RATIO</th>
                <th>REVIEW STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7">
                    <div className="employees-empty-state">
                      <RefreshCw size={27} />
                      <h3>Loading employee records...</h3>
                      <p>Fetching live compensation analysis data.</p>
                    </div>
                  </td>
                </tr>
              ) : filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan="7">
                    <div className="employees-empty-state">
                      <div className="employees-empty-icon">
                        <Users size={30} />
                      </div>
                      <h3>No employee records found</h3>
                      <p>Try changing your search or filters.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredEmployees.slice(0, 100).map((employee) => (
                  <tr key={employee.employee_id}>
                    <td>
                      <strong>
                        {employee.employee_name || "Employee"}
                      </strong>
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
                        {Number.isFinite(Number(employee.compa_ratio))
                          ? `${Number(employee.compa_ratio).toFixed(1)}%`
                          : "—"}
                      </strong>
                    </td>

                    <td>
                      {employee.requires_hr_review ? (
                        <span className="severity-badge medium">
                          Needs Review
                        </span>
                      ) : (
                        <span className="alert-status">
                          No Review Flag
                        </span>
                      )}
                    </td>

                    <td>
                      <button
                        type="button"
                        className="employee-view-btn"
                        title="View employee details"
                        aria-label={`View ${employee.employee_name || "employee"} details`}
                        onClick={() => setSelectedEmployee(employee)}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          padding: "9px",
                          border: "1px solid #245b8a",
                          borderRadius: "9px",
                          background: "#102e52",
                          color: "#55dfff",
                          cursor: "pointer",
                        }}
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

        {!loading && filteredEmployees.length > 100 && (
          <p className="analysis-table-note">
            Showing first 100 records. Export Employees downloads all{" "}
            {formatNumber(filteredEmployees.length)} filtered records.
          </p>
        )}
      </section>

      {/* EMPLOYEE DETAILS MODAL */}
      {selectedEmployee && (
        <div
          style={modalOverlayStyle}
          onClick={() => setSelectedEmployee(null)}
        >
          <div
            style={modalStyle}
            role="dialog"
            aria-modal="true"
            aria-labelledby="employee-modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="employee-modal-header">
              <div>
                <div className="employees-heading-icon">
                  <UserRound size={24} />
                </div>
                <h2 id="employee-modal-title">Employee Details</h2>
                <p>Compensation analysis information</p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedEmployee(null)}
                aria-label="Close employee details"
                style={{
                  border: "1px solid #245b8a",
                  borderRadius: "9px",
                  padding: "9px",
                  background: "#102e52",
                  color: "#55dfff",
                  cursor: "pointer",
                }}
              >
                <X size={21} />
              </button>
            </div>

            <div className="employee-modal-identity">
              <h3>
                {selectedEmployee.employee_name || "Employee"}
              </h3>
              <span>Employee ID: {selectedEmployee.employee_id}</span>
              <span>
                {selectedEmployee.level_id != null
                  ? `Level ${selectedEmployee.level_id}`
                  : "Level unavailable"}
              </span>
            </div>

            <div className="employee-details-grid">
              <div>
                <span>Annual Compensation</span>
                <strong>
                  {formatINR(selectedEmployee.normalized_salary_inr)}
                </strong>
              </div>

              <div>
                <span>Band Minimum</span>
                <strong>
                  {formatINR(selectedEmployee.band_minimum_inr)}
                </strong>
              </div>

              <div>
                <span>Band Midpoint</span>
                <strong>
                  {formatINR(selectedEmployee.band_midpoint_inr)}
                </strong>
              </div>

              <div>
                <span>Band Maximum</span>
                <strong>
                  {formatINR(selectedEmployee.band_maximum_inr)}
                </strong>
              </div>

              <div>
                <span>Compa-Ratio</span>
                <strong>
                  {Number.isFinite(Number(selectedEmployee.compa_ratio))
                    ? `${Number(selectedEmployee.compa_ratio).toFixed(2)}%`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Band Position</span>
                <strong>
                  {Number.isFinite(Number(selectedEmployee.band_position))
                    ? `${Number(selectedEmployee.band_position).toFixed(2)}%`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Performance Rating</span>
                <strong>
                  {selectedEmployee.performance_rating ?? "—"}
                </strong>
              </div>

              <div>
                <span>Peer Group Size</span>
                <strong>
                  {selectedEmployee.peer_group_size ?? "—"}
                </strong>
              </div>
            </div>

            <div className="employee-modal-issues">
              <h4>
                <AlertTriangle size={18} />
                Potential Issues
              </h4>

              {selectedEmployee.potential_issues?.length ? (
                selectedEmployee.potential_issues.map((issue, index) => (
                  <div
                    className="employee-issue-item"
                    key={`${issue.type}-${index}`}
                  >
                    <strong>{formatIssue(issue.type)}</strong>
                    <span>
                      {issue.message || "HR review recommended."}
                    </span>
                  </div>
                ))
              ) : (
                <p>No potential issues reported for this employee.</p>
              )}
            </div>

            <div className="employee-modal-footer">
              {selectedEmployee.requires_hr_review ? (
                <span className="severity-badge medium">
                  Requires HR Review
                </span>
              ) : (
                <span className="alert-status">No Review Flag</span>
              )}

              <button
                type="button"
                className="analysis-outline-btn"
                onClick={() => setSelectedEmployee(null)}
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
