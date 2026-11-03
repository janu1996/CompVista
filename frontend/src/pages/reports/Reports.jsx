
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  FileBarChart,
  Download,
  Search,
  FileSpreadsheet,
  FileText,
  Users,
  ShieldCheck,
  ChartNoAxesCombined,
  Clock,
  CalendarDays,
  ArrowDownToLine,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

import api from "../../services/api.js";

const reportCategories = [
  {
    title: "Compensation Analysis",
    description: "Review salary distributions and compensation benchmarks.",
    icon: ChartNoAxesCombined,
    format: "CSV",
    color: "blue",
    key: "compensation",
  },
  {
    title: "Pay Equity Report",
    description: "Analyze compa-ratios and employee pay disparities.",
    icon: ShieldCheck,
    format: "CSV",
    color: "cyan",
    key: "equity",
  },
  {
    title: "Employee Records",
    description: "Export available employee compensation records.",
    icon: Users,
    format: "CSV",
    color: "purple",
    key: "employees",
  },
  {
    title: "Data Quality Report",
    description: "Review analysis coverage and reported data quality issues.",
    icon: FileSpreadsheet,
    format: "CSV",
    color: "amber",
    key: "quality",
  },
];

const formatINR = (value) =>
  Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  });

const getResponseData = (response) =>
  response?.data?.data ?? response?.data ?? {};

const escapeCSV = (value) =>
  `"${String(value ?? "").replaceAll('"', '""')}"`;

const createCSV = (headers, rows) =>
  [headers, ...rows]
    .map((row) => row.map(escapeCSV).join(","))
    .join("\n");

const getIssueNames = (employee) => {
  const issues = Array.isArray(employee.potential_issues)
    ? employee.potential_issues
    : [];

  return issues
    .map((issue) => issue.message || issue.type || "")
    .filter(Boolean)
    .join("; ");
};

export default function Reports() {
  const [search, setSearch] = useState("");
  const [period, setPeriod] = useState("all");

  const [employees, setEmployees] = useState([]);
  const [summary, setSummary] = useState(null);
  const [reportHistory, setReportHistory] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState("");

  const fetchReportData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [summaryResponse, resultsResponse] =
        await Promise.all([
          api.get("/api/analysis/summary"),
          api.get("/api/analysis/results"),
        ]);

      const summaryData = getResponseData(summaryResponse);
      const resultsData = getResponseData(resultsResponse);

      setSummary(summaryData.summary ?? summaryData);

      setEmployees(
        Array.isArray(resultsData.results)
          ? resultsData.results
          : []
      );
    } catch (err) {
      console.error("Reports loading error:", err);

      setError(
        err.response?.data?.message ||
          "Unable to load report data. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReportData();
  }, [fetchReportData]);

  const filteredHistory = useMemo(() => {
    const now = new Date();

    return reportHistory.filter((report) => {
      const matchesSearch = report.name
        .toLowerCase()
        .includes(search.toLowerCase());

      const reportDate = new Date(report.timestamp);
      const ageInDays =
        (now.getTime() - reportDate.getTime()) /
        (1000 * 60 * 60 * 24);

      let matchesPeriod = true;

      if (period === "today") {
        matchesPeriod =
          reportDate.toDateString() === now.toDateString();
      } else if (period === "week") {
        matchesPeriod = ageInDays <= 7;
      } else if (period === "month") {
        matchesPeriod = ageInDays <= 30;
      }

      return matchesSearch && matchesPeriod;
    });
  }, [reportHistory, search, period]);

  const generateReport = (report) => {
    if (!summary || exporting) return;

    let headers = [];
    let rows = [];
    let fileName = "";

    if (report.key === "compensation") {
      headers = [
        "Employee ID",
        "Employee Name",
        "Role ID",
        "Level ID",
        "Currency",
        "Annual Compensation INR",
        "Band Minimum INR",
        "Band Midpoint INR",
        "Band Maximum INR",
        "Compa Ratio",
        "Band Position",
        "Performance Rating",
        "HR Review Required",
      ];

      rows = employees.map((item) => [
        item.employee_id,
        item.employee_name,
        item.role_id,
        item.level_id,
        item.reporting_currency || "INR",
        item.normalized_salary_inr,
        item.band_minimum_inr,
        item.band_midpoint_inr,
        item.band_maximum_inr,
        item.compa_ratio,
        item.band_position,
        item.performance_rating,
        item.requires_hr_review ? "Yes" : "No",
      ]);

      fileName = "compvista-compensation-analysis.csv";
    }

    if (report.key === "equity") {
      const flaggedEmployees = employees.filter(
        (item) => item.requires_hr_review
      );

      headers = [
        "Employee ID",
        "Employee Name",
        "Role ID",
        "Level ID",
        "Annual Compensation INR",
        "Band Midpoint INR",
        "Compa Ratio",
        "Band Position",
        "Peer Group Size",
        "Peer Median Salary INR",
        "Potential Issues",
      ];

      rows = flaggedEmployees.map((item) => [
        item.employee_id,
        item.employee_name,
        item.role_id,
        item.level_id,
        item.normalized_salary_inr,
        item.band_midpoint_inr,
        item.compa_ratio,
        item.band_position,
        item.peer_group_size,
        item.peer_median_salary_inr,
        getIssueNames(item),
      ]);

      fileName = "compvista-pay-equity-report.csv";
    }

    if (report.key === "employees") {
      headers = [
        "Employee ID",
        "Employee Name",
        "Role ID",
        "Level ID",
        "Location ID",
        "Currency",
        "Annual Compensation INR",
        "Band Minimum INR",
        "Band Midpoint INR",
        "Band Maximum INR",
        "Compa Ratio",
        "Performance Rating",
        "HR Review Required",
      ];

      rows = employees.map((item) => [
        item.employee_id,
        item.employee_name,
        item.role_id,
        item.level_id,
        item.location_id,
        item.reporting_currency || "INR",
        item.normalized_salary_inr,
        item.band_minimum_inr,
        item.band_midpoint_inr,
        item.band_maximum_inr,
        item.compa_ratio,
        item.performance_rating,
        item.requires_hr_review ? "Yes" : "No",
      ]);

      fileName = "compvista-employee-records.csv";
    }

    if (report.key === "quality") {
      const qualityIssues =
        summary.data_quality_issues || {};

      headers = [
        "Metric",
        "Count",
        "Description",
      ];

      rows = [
        [
          "Employees Analyzed",
          summary.employees_analyzed,
          "Employees included in compensation analysis",
        ],
        [
          "Employees Excluded",
          summary.employees_excluded,
          "Employees excluded from compensation analysis",
        ],
        ...Object.entries(qualityIssues).map(([key, value]) => {
          const count =
            typeof value === "number"
              ? value
              : Number(value?.count ?? value?.total ?? 0);

          return [
            key,
            count,
            key === "missing_fx_rate"
              ? "Missing foreign exchange rate"
              : key.replaceAll("_", " "),
          ];
        }),
      ];

      fileName = "compvista-data-quality-report.csv";
    }

    if (rows.length === 0) {
      setError("No records are available for this report.");
      return;
    }

    setExporting(report.key);
    setError("");

    try {
      const csv = createCSV(headers, rows);

      const blob = new Blob(["\uFEFF" + csv], {
        type: "text/csv;charset=utf-8;",
      });

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = fileName;

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(url);

      const now = new Date();

      const historyItem = {
        id: `${now.getTime()}-${report.key}`,
        name: report.title,
        type: report.title,
        generated_date: now.toLocaleString("en-IN"),
        format: "CSV",
        status: "Downloaded",
        timestamp: now.toISOString(),
      };

      setReportHistory((previous) => [
        historyItem,
        ...previous,
      ]);
    } catch (err) {
      console.error("Report export error:", err);
      setError("Unable to generate this report.");
    } finally {
      setExporting("");
    }
  };

  const lastGenerated =
    reportHistory.length > 0
      ? new Date(reportHistory[0].timestamp).toLocaleDateString("en-IN")
      : "—";

  return (
    <div className="reports-page">

      {/* PAGE HEADER */}
      <section className="reports-header">
        <div className="reports-heading">
          <div className="reports-heading-icon">
            <FileBarChart size={27} />
          </div>

          <div>
            <h1>Reports & Exports</h1>
            <p>
              Generate, organize, and export compensation insights
              and employee reports.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="reports-refresh-btn"
          onClick={fetchReportData}
          disabled={loading}
        >
          <RefreshCw size={17} />
          Refresh Data
        </button>
      </section>

      {/* ERROR */}
      {error && (
        <div className="reports-error">
          <AlertCircle size={19} />
          <span>{error}</span>
          <button onClick={() => setError("")}>Dismiss</button>
        </div>
      )}

      {/* STATISTICS */}
      <section className="reports-stats">

        <div className="report-stat-card">
          <div className="report-stat-icon blue">
            <FileText size={23} />
          </div>
          <div>
            <span>Available Reports</span>
            <h2>04</h2>
            <p>Report categories</p>
          </div>
        </div>

        <div className="report-stat-card">
          <div className="report-stat-icon cyan">
            <Download size={23} />
          </div>
          <div>
            <span>Generated Reports</span>
            <h2>{reportHistory.length.toString().padStart(2, "0")}</h2>
            <p>Current session exports</p>
          </div>
        </div>

        <div className="report-stat-card">
          <div className="report-stat-icon purple">
            <FileSpreadsheet size={23} />
          </div>
          <div>
            <span>Supported Formats</span>
            <h2>01</h2>
            <p>CSV export available</p>
          </div>
        </div>

        <div className="report-stat-card">
          <div className="report-stat-icon amber">
            <Clock size={23} />
          </div>
          <div>
            <span>Last Generated</span>
            <h2 className="report-last-generated">
              {lastGenerated}
            </h2>
            <p>Most recent export</p>
          </div>
        </div>

      </section>

      {/* REPORT CENTER */}
      <section className="report-catalog">

        <div className="reports-section-heading">
          <div>
            <h3>Report Center</h3>
            <p>
              Select a report category to generate your export.
            </p>
          </div>

          <span className="report-category-count">
            04 Categories
          </span>
        </div>

        <div className="report-cards-grid">
          {reportCategories.map((report) => {
            const Icon = report.icon;
            const isExporting = exporting === report.key;

            return (
              <div className="report-card" key={report.key}>

                <div className={`report-card-icon ${report.color}`}>
                  <Icon size={25} />
                </div>

                <div className="report-card-content">
                  <h4>{report.title}</h4>
                  <p>{report.description}</p>
                </div>

                <div className="report-card-footer">
                  <span>{report.format}</span>

                  <button
                    type="button"
                    onClick={() => generateReport(report)}
                    disabled={loading || !summary || Boolean(exporting)}
                  >
                    {isExporting ? (
                      <>
                        <RefreshCw size={16} />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Download size={16} />
                        Export
                      </>
                    )}
                  </button>
                </div>

              </div>
            );
          })}
        </div>
      </section>

      {/* EXPORT HISTORY */}
      <section className="report-history-panel">

        <div className="reports-section-heading">
          <div>
            <h3>Export History</h3>
            <p>
              Track reports generated during this browser session.
            </p>
          </div>

          <span className="report-history-count">
            {filteredHistory.length} Records
          </span>
        </div>

        <div className="report-history-filters">

          <div className="report-search">
            <Search size={18} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search report name..."
            />
          </div>

          <div className="report-period-filter">
            <CalendarDays size={17} />

            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
            </select>
          </div>

        </div>

        <div className="report-history-table-wrapper">
          <table className="report-history-table">

            <thead>
              <tr>
                <th>REPORT NAME</th>
                <th>REPORT TYPE</th>
                <th>GENERATED DATE</th>
                <th>FORMAT</th>
                <th>STATUS</th>
              </tr>
            </thead>

            <tbody>
              {filteredHistory.length === 0 ? (
                <tr>
                  <td colSpan="5">
                    <div className="report-history-empty">
                      <div className="report-history-empty-icon">
                        <ArrowDownToLine size={29} />
                      </div>

                      <h3>No export history available</h3>

                      <p>
                        Generate a report from the Report Center.
                        Your export history will appear here.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredHistory.map((report) => (
                  <tr key={report.id}>
                    <td>
                      <strong>{report.name}</strong>
                    </td>

                    <td>{report.type}</td>
                    <td>{report.generated_date}</td>
                    <td>
                      <span className="report-format-badge">
                        {report.format}
                      </span>
                    </td>
                    <td>
                      <span className="report-success-status">
                        {report.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>

          </table>
        </div>
      </section>

      <p className="reports-data-note">
        Reports are generated from the currently available compensation
        analysis results. Employee Records includes analyzed records only;
        excluded employees are represented separately in the Data Quality Report.
      </p>

    </div>
  );
}
