
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  FileText, Search, Plus, Clock, CheckCircle2, XCircle,
  IndianRupee, Eye, Filter, RefreshCw, Send, Check,
  Ban, Play, X, AlertCircle, History, Users, TrendingUp,
  LoaderCircle, CalendarDays, ArrowUpRight,
} from "lucide-react";
import api from "../../services/api";

const STATUSES = ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "APPLIED"];

const formatINR = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `₹${number.toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;
};

const formatDate = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
};

const statusLabel = (status) =>
  status?.charAt(0) + status?.slice(1).toLowerCase();

export default function Proposals() {
  const [proposals, setProposals] = useState([]);
  const [analysisRows, setAnalysisRows] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedProposal, setSelectedProposal] = useState(null);
  const [actionModal, setActionModal] = useState(null);
  const [remarks, setRemarks] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const employeeMap = useMemo(() => {
    const map = new Map();
    analysisRows.forEach((row) => {
      map.set(row.employee_id, row);
    });
    return map;
  }, [analysisRows]);

  const loadData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);

    setError("");

    try {
      const [proposalResponse, analysisResponse] = await Promise.all([
        api.get("/api/proposals/", {
          params: { page: 1, per_page: 100 },
        }),
        api.get("/api/analysis/results"),
      ]);

      const proposalData = proposalResponse.data?.data || [];
      const analysisData = analysisResponse.data?.data;

      setProposals(Array.isArray(proposalData) ? proposalData : []);
      setAnalysisRows(
        Array.isArray(analysisData?.results) ? analysisData.results : []
      );
    } catch (err) {
      setError(
        err.response?.data?.message ||
        "Unable to load proposals. Please check your login and backend connection."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const getEmployee = (proposal) =>
    employeeMap.get(proposal.employee_id);

  const getCurrentSalaryINR = (proposal) => {
    const employee = getEmployee(proposal);
    if (!employee) return null;
    return Number(employee.normalized_salary_inr);
  };

  const getProposedSalaryINR = (proposal) => {
    const employee = getEmployee(proposal);
    if (!employee) return null;

    const normalizedSalary = Number(employee.normalized_salary);
    const normalizedINR = Number(employee.normalized_salary_inr);
    const proposedSalary = Number(proposal.proposed_salary);

    if (
      !Number.isFinite(normalizedSalary) ||
      normalizedSalary <= 0 ||
      !Number.isFinite(normalizedINR) ||
      !Number.isFinite(proposedSalary)
    ) return null;

    return proposedSalary * (normalizedINR / normalizedSalary);
  };

  const counts = useMemo(() => ({
    total: proposals.length,
    draft: proposals.filter((p) => p.status === "DRAFT").length,
    submitted: proposals.filter((p) => p.status === "SUBMITTED").length,
    approved: proposals.filter((p) => p.status === "APPROVED").length,
    rejected: proposals.filter((p) => p.status === "REJECTED").length,
    applied: proposals.filter((p) => p.status === "APPLIED").length,
  }), [proposals]);

  const filteredProposals = useMemo(() => {
    const query = search.trim().toLowerCase();

    return proposals.filter((proposal) => {
      const employee = getEmployee(proposal);
      const matchesSearch =
        !query ||
        String(proposal.proposal_id || "").toLowerCase().includes(query) ||
        String(proposal.employee_id || "").toLowerCase().includes(query) ||
        String(employee?.employee_name || "").toLowerCase().includes(query);

      const matchesStatus =
        status === "all" || proposal.status === status;

      return matchesSearch && matchesStatus;
    });
  }, [proposals, search, status, employeeMap]);

  const generateProposals = async () => {
    const confirmed = window.confirm(
      "Generate adjustment proposals for eligible flagged employees? Existing proposals will not be duplicated. New proposals will be created as DRAFT and will require HR review."
    );

    if (!confirmed) return;

    setGenerating(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.post("/api/proposals/generate", {});
      const result = response.data?.data || {};

      setSuccess(
        `Generation completed: ${result.proposals_created ?? 0} created, ${result.proposals_skipped ?? 0} skipped.`
      );

      await loadData(true);
    } catch (err) {
      setError(
        err.response?.data?.message || "Proposal generation failed."
      );
    } finally {
      setGenerating(false);
    }
  };

  const openDetails = async (proposal) => {
    setError("");
    setSelectedProposal({ ...proposal, loadingDetails: true });

    try {
      const response = await api.get(
        `/api/proposals/${encodeURIComponent(proposal.proposal_id)}`
      );
      setSelectedProposal(response.data?.data || proposal);
    } catch (err) {
      setSelectedProposal(proposal);
      setError(
        err.response?.data?.message || "Unable to load proposal details."
      );
    }
  };

  const openAction = (proposal, action) => {
    setSelectedProposal(null);
    setRemarks("");
    setActionModal({ proposal, action });
  };

  const performAction = async () => {
    if (!actionModal) return;

    const { proposal, action } = actionModal;
    const needsRemarks = ["submit", "approve", "reject"].includes(action);

    if (needsRemarks && !remarks.trim()) {
      setError(
        action === "reject"
          ? "Please provide a rejection reason."
          : action === "approve"
          ? "Approval remarks are required."
          : "Submission remarks are required."
      );
      return;
    }

    setActionLoading(true);
    setError("");
    setSuccess("");

    try {
      const payload = needsRemarks ? { remarks: remarks.trim() } : {};

      const response = await api.post(
        `/api/proposals/${encodeURIComponent(proposal.proposal_id)}/${action}`,
        payload
      );

      setSuccess(
        response.data?.message ||
        `Proposal ${action} action completed successfully.`
      );

      setActionModal(null);
      setRemarks("");
      await loadData(true);
    } catch (err) {
      setError(
        err.response?.data?.message ||
        `Unable to ${action} this proposal.`
      );
    } finally {
      setActionLoading(false);
    }
  };

  const actionTitle = {
    submit: "Submit Proposal",
    approve: "Approve Proposal",
    reject: "Reject Proposal",
    apply: "Apply Approved Proposal",
  };

  const actionDescription = {
    submit: "Submit this draft for HR review. Submission remarks are required.",
    approve: "Confirm your approval decision. Approval remarks are required.",
    reject: "Reject this proposal with a clear reason. This decision will be recorded in the audit history.",
    apply: "This will close the current salary record and create a new salary record using the approved adjustment.",
  };

  const employeeName = (proposal) =>
    getEmployee(proposal)?.employee_name || "Employee name unavailable";

  return (
    <div className="proposals-page">
      <style>{`
        .proposals-page {
          color: #eaf2ff;
          width: 100%;
          animation: proposalFade .35s ease;
        }
        @keyframes proposalFade {
          from { opacity: 0; transform: translateY(7px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .proposals-header {
          display:flex; align-items:center; justify-content:space-between;
          gap:18px; margin-bottom:25px; flex-wrap:wrap;
        }
        .proposals-heading { display:flex; align-items:center; gap:15px; }
        .proposals-heading-icon {
          width:54px; height:54px; display:grid; place-items:center;
          border-radius:16px; color:#70d8ff;
          background:linear-gradient(135deg,#123d75,#087eae);
          box-shadow:0 8px 25px #078bd533;
        }
        .proposals-heading h1 { margin:0; font-size:25px; font-weight:750; color:#f4f8ff; }
        .proposals-heading p { margin:6px 0 0; color:#91a9c8; font-size:13px; }
        .proposal-refresh-btn {
          border:1px solid #42bdf477; border-radius:11px;
          padding:11px 17px; display:inline-flex; align-items:center;
          justify-content:center; gap:9px; color:white; cursor:pointer;
          font-weight:650; background:linear-gradient(120deg,#1264bc,#087fae);
          box-shadow:0 7px 22px #087fc333; transition:.2s;
        }
        .proposal-refresh-btn:hover:not(:disabled) {
          transform:translateY(-2px); filter:brightness(1.12);
        }
        .proposal-refresh-btn:disabled {
          opacity:.6; cursor:not-allowed; transform:none;
        }
        .proposal-create-btn {
          position:relative; overflow:hidden;
          border:1px solid #39c8ff; border-radius:12px;
          padding:12px 20px; display:inline-flex; align-items:center;
          justify-content:center; gap:10px; color:#fff; cursor:pointer;
          font-size:13px; font-weight:750; letter-spacing:.2px;
          background:linear-gradient(120deg,#087fd5 0%,#079fc5 55%,#08b6c9 100%);
          box-shadow:0 6px 20px #079bd655,inset 0 1px 0 #ffffff35;
          transition:all .25s ease;
        }
        .proposal-create-btn:hover:not(:disabled) {
          transform:translateY(-2px); filter:brightness(1.15);
          box-shadow:0 9px 28px #08b9e477,0 0 14px #08b9e433;
        }
        .proposal-create-btn:active:not(:disabled) { transform:translateY(0); }
        .proposal-create-btn:disabled {
          opacity:.65; cursor:not-allowed; filter:none; transform:none;
        }
        .proposals-header-actions { display:flex; gap:10px; flex-wrap:wrap; }
        .proposals-stats {
          display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
          gap:15px; margin-bottom:23px;
        }
        .proposal-stat-card {
          min-width:0; padding:19px; display:flex; align-items:center; gap:14px;
          border:1px solid #8bbce51c; border-radius:16px;
          background:linear-gradient(135deg,#102d50ed,#102541ed);
          box-shadow:0 9px 28px #020b1c30;
        }
        .proposal-stat-icon {
          flex-shrink:0; width:45px; height:45px; display:grid;
          place-items:center; border-radius:14px;
        }
        .proposal-stat-icon.blue { color:#65c9ff; background:#258de326; }
        .proposal-stat-icon.amber { color:#ffd078; background:#eaa52a24; }
        .proposal-stat-icon.green { color:#65e4bd; background:#2ac49a24; }
        .proposal-stat-icon.red { color:#ff899c; background:#ef536b24; }
        .proposal-stat-card span { color:#9bb1cc; font-size:12px; }
        .proposal-stat-card h2 { margin:5px 0 3px; color:#f5f9ff; font-size:25px; }
        .proposal-stat-card p { margin:0; color:#718baa; font-size:11px; }
        .proposals-directory, .proposal-info-panel {
          border:1px solid #8bbce51c; border-radius:17px;
          background:linear-gradient(145deg,#102b4bed,#0c2039ed);
          box-shadow:0 10px 30px #020b1c25;
        }
        .proposals-directory { padding:21px; }
        .proposals-section-heading {
          display:flex; justify-content:space-between; align-items:center;
          gap:12px; margin-bottom:19px;
        }
        .proposals-section-heading h3 { margin:0; font-size:17px; color:#f1f6ff; }
        .proposals-section-heading p { margin:5px 0 0; font-size:12px; color:#8da6c5; }
        .proposal-record-count {
          border:1px solid #369edc45; border-radius:30px; padding:7px 12px;
          color:#79d4ff; background:#087fba18; font-size:11px; white-space:nowrap;
        }
        .proposals-filters {
          display:flex; align-items:center; gap:12px; margin-bottom:17px;
          flex-wrap:wrap;
        }
        .proposals-search, .proposal-status-filter {
          display:flex; align-items:center; gap:9px; height:42px;
          border:1px solid #759bc52d; border-radius:10px;
          background:#091c32; color:#81a9d0; padding:0 12px;
        }
        .proposals-search { flex:1; min-width:220px; }
        .proposals-search input, .proposal-status-filter select {
          width:100%; border:0; outline:0; background:transparent;
          color:#e7f1ff; font-size:12px;
        }
        .proposals-search input::placeholder { color:#6f89a8; }
        .proposal-status-filter { min-width:205px; }
        .proposal-status-filter select option { background:#102b48; color:white; }
        .proposals-table-wrapper { width:100%; overflow-x:auto; }
        .proposals-table { width:100%; border-collapse:collapse; min-width:850px; }
        .proposals-table th {
          padding:13px 12px; text-align:left; color:#7895b8;
          font-size:10px; letter-spacing:.7px; font-weight:700;
          border-bottom:1px solid #7797ba24; white-space:nowrap;
        }
        .proposals-table td {
          padding:15px 12px; border-bottom:1px solid #7797ba16;
          color:#dce9fa; font-size:12px; white-space:nowrap;
        }
        .proposals-table tbody tr:hover { background:#258bd10b; }
        .proposal-employee-name { color:#f1f6ff; font-weight:650; }
        .proposal-employee-id { color:#7896b7; font-size:10px; margin-top:4px; }
        .proposal-money { color:#bde9ff; font-weight:650; }
        .proposal-change { color:#62dfb7; font-weight:700; }
        .proposal-status-badge {
          display:inline-flex; padding:6px 10px; border-radius:20px;
          font-size:10px; font-weight:700; letter-spacing:.3px;
        }
        .proposal-status-badge.draft { color:#9dcaff; background:#368ee323; }
        .proposal-status-badge.submitted { color:#ffd27f; background:#e8a62b22; }
        .proposal-status-badge.approved { color:#69e3bb; background:#29c39722; }
        .proposal-status-badge.rejected { color:#ff91a2; background:#ed536b22; }
        .proposal-status-badge.applied { color:#85e6f1; background:#2aafc422; }
        .proposal-view-btn {
          width:32px; height:32px; border:1px solid #399edc55;
          border-radius:9px; display:grid; place-items:center;
          background:#087fba1c; color:#72d0ff; cursor:pointer;
        }
        .proposal-view-btn:hover { background:#087fba45; }
        .proposal-actions-cell { display:flex; align-items:center; gap:6px; }
        .proposal-mini-action {
          border:1px solid #479edc45; border-radius:8px; padding:7px 9px;
          background:#0e4772; color:#d9f3ff; font-size:10px;
          font-weight:650; cursor:pointer; display:inline-flex;
          align-items:center; gap:5px;
        }
        .proposal-mini-action:hover { filter:brightness(1.25); }
        .proposal-mini-action.danger { background:#6d2940; border-color:#d45b7955; }
        .proposal-mini-action.success { background:#145747; border-color:#3bbd9455; }
        .proposals-empty-state {
          text-align:center; padding:42px 15px; white-space:normal;
        }
        .proposals-empty-icon {
          margin:0 auto 13px; width:54px; height:54px;
          display:grid; place-items:center; border-radius:17px;
          color:#64caff; background:#1686c326;
        }
        .proposals-empty-state h3 { margin:0 0 7px; color:#e8f2ff; font-size:15px; }
        .proposals-empty-state p { margin:0; color:#829cbb; font-size:12px; }
        .proposal-info-panel {
          margin-top:18px; padding:17px 20px; display:flex;
          align-items:center; gap:14px;
        }
        .proposal-info-icon {
          flex-shrink:0; width:43px; height:43px; border-radius:13px;
          display:grid; place-items:center; color:#74d7ff; background:#148bc32a;
        }
        .proposal-info-panel h4 { margin:0 0 5px; color:#eaf4ff; font-size:13px; }
        .proposal-info-panel p { margin:0; color:#8ba6c6; font-size:11px; line-height:1.6; }
        .proposal-alert {
          padding:11px 14px; border-radius:10px; margin-bottom:14px;
          display:flex; align-items:center; gap:9px; font-size:12px;
        }
        .proposal-alert.error { color:#ffabb7; background:#a52e461c; border:1px solid #df61722e; }
        .proposal-alert.success { color:#83e7c7; background:#15936c1b; border:1px solid #39c59a30; }
        .proposal-modal-overlay {
          position:fixed; inset:0; z-index:1000; padding:20px;
          display:flex; align-items:center; justify-content:center;
          background:#020a16c9; backdrop-filter:blur(7px);
        }
        .proposal-modal {
          width:min(680px,100%); max-height:88vh; overflow-y:auto;
          border:1px solid #66b9e64a; border-radius:18px;
          background:linear-gradient(145deg,#122f50,#0b1e35);
          box-shadow:0 25px 90px #0009;
        }
        .proposal-modal-header {
          padding:19px 21px; display:flex; justify-content:space-between;
          align-items:center; border-bottom:1px solid #91b6d522;
          position:sticky; top:0; background:#112d4c; z-index:2;
        }
        .proposal-modal-header h3 { margin:0; font-size:16px; color:#f2f7ff; }
        .proposal-modal-header p { margin:5px 0 0; color:#8da8c8; font-size:11px; }
        .proposal-modal-close {
          width:33px; height:33px; border:1px solid #7598bb44;
          border-radius:9px; display:grid; place-items:center;
          background:#173a5c; color:#c5def8; cursor:pointer;
        }
        .proposal-modal-body { padding:21px; }
        .proposal-detail-grid {
          display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:11px;
        }
        .proposal-detail-item {
          padding:13px; border:1px solid #86acd01d;
          border-radius:11px; background:#091e35a8; min-width:0;
        }
        .proposal-detail-item span { display:block; color:#809cbd; font-size:10px; margin-bottom:7px; }
        .proposal-detail-item strong { color:#eaf4ff; font-size:13px; overflow-wrap:anywhere; }
        .proposal-detail-section { margin-top:20px; }
        .proposal-detail-section h4 { display:flex; gap:8px; align-items:center; color:#cfe5ff; font-size:12px; margin:0 0 11px; }
        .proposal-reason {
          padding:13px; border-radius:10px; background:#091e35a8;
          color:#b2c7df; font-size:11px; line-height:1.7;
          border:1px solid #86acd01d; white-space:pre-wrap;
        }
        .proposal-history-item {
          border-left:2px solid #278fc5; padding:2px 0 13px 13px;
          margin-left:5px; position:relative;
        }
        .proposal-history-item:before {
          content:""; position:absolute; left:-5px; top:1px;
          width:8px; height:8px; border-radius:50%; background:#5dc8f3;
        }
        .proposal-history-item strong { color:#dceeff; font-size:11px; }
        .proposal-history-item p { margin:5px 0; color:#9bb2cd; font-size:11px; }
        .proposal-history-item small { color:#718baa; font-size:10px; }
        .proposal-action-footer {
          display:flex; justify-content:flex-end; gap:9px; margin-top:20px;
          flex-wrap:wrap;
        }
        .proposal-action-btn {
          border:1px solid #399edc55; border-radius:9px; padding:10px 15px;
          background:linear-gradient(120deg,#1264bc,#087fae);
          color:white; font-size:11px; font-weight:700; cursor:pointer;
          display:inline-flex; align-items:center; gap:7px;
        }
        .proposal-action-btn.secondary { background:#183753; border-color:#7598bb44; }
        .proposal-action-btn.danger { background:#8a3047; border-color:#d45b7955; }
        .proposal-action-btn:disabled { opacity:.55; cursor:not-allowed; }
        .proposal-remarks-label { display:block; color:#bdd3ec; font-size:11px; margin:15px 0 7px; }
        .proposal-remarks {
          width:100%; min-height:105px; resize:vertical; box-sizing:border-box;
          border:1px solid #6e9ac044; border-radius:10px;
          background:#081c32; color:#edf6ff; padding:12px;
          outline:none; font:inherit; font-size:12px;
        }
        .proposal-remarks:focus { border-color:#42b8ed; }
        .proposal-remarks::placeholder { color:#718baa; }
        .proposal-loading {
          display:flex; justify-content:center; align-items:center;
          gap:10px; padding:45px; color:#9ab7d8; font-size:12px;
        }
        .proposal-spin { animation:proposalSpin 1s linear infinite; }
        @keyframes proposalSpin { to { transform:rotate(360deg); } }
        @media(max-width:1050px) {
          .proposals-stats { grid-template-columns:repeat(2,minmax(0,1fr)); }
        }
        @media(max-width:600px) {
          .proposals-stats { grid-template-columns:1fr; }
          .proposals-directory { padding:14px; }
          .proposals-section-heading { align-items:flex-start; }
          .proposal-detail-grid { grid-template-columns:1fr; }
          .proposals-heading h1 { font-size:20px; }
          .proposal-modal-overlay { padding:10px; }
        }
      `}</style>

      <section className="proposals-header">
        <div className="proposals-heading">
          <div className="proposals-heading-icon">
            <FileText size={27} />
          </div>
          <div>
            <h1>Compensation Proposals</h1>
            <p>Create, review, and track employee compensation adjustment proposals.</p>
          </div>
        </div>

        <div className="proposals-header-actions">
          <button
            className="proposal-refresh-btn"
            onClick={() => loadData(true)}
            disabled={loading || refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "proposal-spin" : ""} />
            Refresh
          </button>
          <button
            className="proposal-create-btn"
            onClick={generateProposals}
            disabled={generating || loading}
          >
            {generating
              ? <LoaderCircle size={17} className="proposal-spin" />
              : <Plus size={18} />}
            {generating ? "Generating..." : "Generate Proposals"}
          </button>
        </div>
      </section>

      {error && (
        <div className="proposal-alert error">
          <AlertCircle size={17} /> {error}
          <button
            onClick={() => setError("")}
            style={{ marginLeft: "auto", border: 0, background: "transparent", color: "inherit", cursor: "pointer" }}
          >
            <X size={15} />
          </button>
        </div>
      )}

      {success && (
        <div className="proposal-alert success">
          <CheckCircle2 size={17} /> {success}
          <button
            onClick={() => setSuccess("")}
            style={{ marginLeft: "auto", border: 0, background: "transparent", color: "inherit", cursor: "pointer" }}
          >
            <X size={15} />
          </button>
        </div>
      )}

      <section className="proposals-stats">
        <div className="proposal-stat-card">
          <div className="proposal-stat-icon blue"><FileText size={22} /></div>
          <div><span>Total Proposals</span><h2>{loading ? "—" : counts.total}</h2><p>All generated proposals</p></div>
        </div>
        <div className="proposal-stat-card">
          <div className="proposal-stat-icon amber"><Clock size={22} /></div>
          <div><span>Pending Review</span><h2>{loading ? "—" : counts.submitted}</h2><p>Awaiting HR decision</p></div>
        </div>
        <div className="proposal-stat-card">
          <div className="proposal-stat-icon green"><CheckCircle2 size={22} /></div>
          <div><span>Approved</span><h2>{loading ? "—" : counts.approved}</h2><p>Approved adjustments</p></div>
        </div>
        <div className="proposal-stat-card">
          <div className="proposal-stat-icon red"><XCircle size={22} /></div>
          <div><span>Rejected</span><h2>{loading ? "—" : counts.rejected}</h2><p>Rejected proposals</p></div>
        </div>
      </section>

      <section className="proposals-directory">
        <div className="proposals-section-heading">
          <div>
            <h3>Proposal Records</h3>
            <p>Monitor compensation changes and their approval progress.</p>
          </div>
          <span className="proposal-record-count">
            {filteredProposals.length} Records
          </span>
        </div>

        <div className="proposals-filters">
          <div className="proposals-search">
            <Search size={17} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search employee name, ID or proposal..."
            />
          </div>
          <div className="proposal-status-filter">
            <Filter size={16} />
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All Proposal Statuses</option>
              {STATUSES.map((item) => (
                <option key={item} value={item}>{statusLabel(item)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="proposals-table-wrapper">
          <table className="proposals-table">
            <thead>
              <tr>
                <th>EMPLOYEE</th>
                <th>PROPOSAL ID</th>
                <th>CURRENT SALARY</th>
                <th>PROPOSED SALARY</th>
                <th>CHANGE</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7">
                    <div className="proposal-loading">
                      <LoaderCircle size={20} className="proposal-spin" />
                      Loading proposal records...
                    </div>
                  </td>
                </tr>
              ) : filteredProposals.length === 0 ? (
                <tr>
                  <td colSpan="7">
                    <div className="proposals-empty-state">
                      <div className="proposals-empty-icon"><FileText size={29} /></div>
                      <h3>{proposals.length ? "No matching proposals" : "No proposal records available"}</h3>
                      <p>
                        {proposals.length
                          ? "Try changing your search or status filter."
                          : "Generate proposals to create draft compensation recommendations for HR review."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredProposals.map((proposal) => {
                  const currentINR = getCurrentSalaryINR(proposal);
                  const proposedINR = getProposedSalaryINR(proposal);
                  const change = currentINR > 0 && proposedINR !== null
                    ? ((proposedINR - currentINR) / currentINR) * 100
                    : null;

                  return (
                    <tr key={proposal.proposal_id}>
                      <td>
                        <div className="proposal-employee-name">{employeeName(proposal)}</div>
                        <div className="proposal-employee-id">{proposal.employee_id}</div>
                      </td>
                      <td>{proposal.proposal_id}</td>
                      <td className="proposal-money">
                        {currentINR === null ? "—" : formatINR(currentINR)}
                      </td>
                      <td className="proposal-money">
                        {proposedINR === null ? "—" : formatINR(proposedINR)}
                      </td>
                      <td className="proposal-change">
                        {change === null ? "—" : `+${change.toFixed(1)}%`}
                      </td>
                      <td>
                        <span className={`proposal-status-badge ${proposal.status?.toLowerCase()}`}>
                          {statusLabel(proposal.status)}
                        </span>
                      </td>
                      <td>
                        <div className="proposal-actions-cell">
                          <button
                            className="proposal-view-btn"
                            title="View details and history"
                            onClick={() => openDetails(proposal)}
                          >
                            <Eye size={16} />
                          </button>
                          {proposal.status === "DRAFT" && (
                            <button
                              className="proposal-mini-action"
                              onClick={() => openAction(proposal, "submit")}
                            >
                              <Send size={12} /> Submit
                            </button>
                          )}
                          {proposal.status === "SUBMITTED" && (
                            <>
                              <button
                                className="proposal-mini-action success"
                                onClick={() => openAction(proposal, "approve")}
                              >
                                <Check size={12} /> Approve
                              </button>
                              <button
                                className="proposal-mini-action danger"
                                onClick={() => openAction(proposal, "reject")}
                              >
                                <Ban size={12} /> Reject
                              </button>
                            </>
                          )}
                          {proposal.status === "APPROVED" && (
                            <button
                              className="proposal-mini-action success"
                              onClick={() => openAction(proposal, "apply")}
                            >
                              <Play size={12} /> Apply
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="proposal-info-panel">
        <div className="proposal-info-icon"><IndianRupee size={22} /></div>
        <div>
          <h4>Compensation Governance</h4>
          <p>
            System-generated proposals are recommendations only. Each adjustment
            requires independent HR review, recorded remarks, approval history,
            and validation against the employee's active compensation band.
          </p>
        </div>
      </section>

      {selectedProposal && (
        <div className="proposal-modal-overlay" onClick={() => setSelectedProposal(null)}>
          <div className="proposal-modal" onClick={(e) => e.stopPropagation()}>
            <div className="proposal-modal-header">
              <div>
                <h3>Proposal Details</h3>
                <p>{selectedProposal.proposal_id}</p>
              </div>
              <button className="proposal-modal-close" onClick={() => setSelectedProposal(null)}>
                <X size={17} />
              </button>
            </div>
            <div className="proposal-modal-body">
              {selectedProposal.loadingDetails ? (
                <div className="proposal-loading">
                  <LoaderCircle size={20} className="proposal-spin" />
                  Loading proposal history...
                </div>
              ) : (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
                    <div>
                      <strong style={{ color: "#f1f7ff", fontSize: 15 }}>{employeeName(selectedProposal)}</strong>
                      <div style={{ color: "#809cbd", fontSize: 11, marginTop: 5 }}>{selectedProposal.employee_id}</div>
                    </div>
                    <span className={`proposal-status-badge ${selectedProposal.status?.toLowerCase()}`}>
                      {statusLabel(selectedProposal.status)}
                    </span>
                  </div>

                  <div className="proposal-detail-grid">
                    <div className="proposal-detail-item">
                      <span>Proposed Salary</span>
                      <strong>{selectedProposal.proposed_salary} {selectedProposal.currency_code}</strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Current Salary (INR normalized)</span>
                      <strong>
                        {getCurrentSalaryINR(selectedProposal) === null
                          ? "Unavailable"
                          : formatINR(getCurrentSalaryINR(selectedProposal))}
                      </strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Proposed Salary (INR normalized)</span>
                      <strong>
                        {getProposedSalaryINR(selectedProposal) === null
                          ? "Unavailable"
                          : formatINR(getProposedSalaryINR(selectedProposal))}
                      </strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Issue Type</span>
                      <strong>{selectedProposal.issue_type || "—"}</strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Created By</span>
                      <strong>{selectedProposal.proposed_by || "—"}</strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Created Date</span>
                      <strong>{formatDate(selectedProposal.created_at)}</strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Approved By</span>
                      <strong>{selectedProposal.approved_by || "—"}</strong>
                    </div>
                    <div className="proposal-detail-item">
                      <span>Applied Date</span>
                      <strong>{formatDate(selectedProposal.applied_at)}</strong>
                    </div>
                  </div>

                  <div className="proposal-detail-section">
                    <h4><FileText size={15} /> Recommendation Reason</h4>
                    <div className="proposal-reason">{selectedProposal.reason || "No reason provided."}</div>
                  </div>

                  <div className="proposal-detail-section">
                    <h4><History size={15} /> Approval History</h4>
                    {selectedProposal.history?.length ? (
                      selectedProposal.history.map((item, index) => (
                        <div className="proposal-history-item" key={`${item.new_status}-${index}`}>
                          <strong>
                            {item.previous_status
                              ? `${statusLabel(item.previous_status)} → ${statusLabel(item.new_status)}`
                              : statusLabel(item.new_status)}
                          </strong>
                          <p>{item.remarks || "No remarks recorded."}</p>
                          <small>
                            {item.changed_by || "System"} · {formatDate(item.changed_at)}
                          </small>
                        </div>
                      ))
                    ) : (
                      <p style={{ color: "#819bb9", fontSize: 11 }}>No history records available.</p>
                    )}
                  </div>

                  <div className="proposal-action-footer">
                    {selectedProposal.status === "DRAFT" && (
                      <button className="proposal-action-btn" onClick={() => openAction(selectedProposal, "submit")}>
                        <Send size={14} /> Submit for Review
                      </button>
                    )}
                    {selectedProposal.status === "SUBMITTED" && (
                      <>
                        <button className="proposal-action-btn" onClick={() => openAction(selectedProposal, "approve")}>
                          <Check size={14} /> Approve
                        </button>
                        <button className="proposal-action-btn danger" onClick={() => openAction(selectedProposal, "reject")}>
                          <Ban size={14} /> Reject
                        </button>
                      </>
                    )}
                    {selectedProposal.status === "APPROVED" && (
                      <button className="proposal-action-btn" onClick={() => openAction(selectedProposal, "apply")}>
                        <Play size={14} /> Apply Adjustment
                      </button>
                    )}
                    <button className="proposal-action-btn secondary" onClick={() => setSelectedProposal(null)}>
                      Close
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {actionModal && (
        <div className="proposal-modal-overlay" onClick={() => !actionLoading && setActionModal(null)}>
          <div className="proposal-modal" onClick={(e) => e.stopPropagation()}>
            <div className="proposal-modal-header">
              <div>
                <h3>{actionTitle[actionModal.action]}</h3>
                <p>{actionModal.proposal.proposal_id}</p>
              </div>
              <button
                className="proposal-modal-close"
                disabled={actionLoading}
                onClick={() => setActionModal(null)}
              >
                <X size={17} />
              </button>
            </div>
            <div className="proposal-modal-body">
              <div className="proposal-alert" style={{ color: "#a9dfff", background: "#1689c31a", border: "1px solid #4bb9e52c" }}>
                <AlertCircle size={17} />
                {actionDescription[actionModal.action]}
              </div>

              <div className="proposal-detail-item">
                <span>Employee / Proposal</span>
                <strong>{actionModal.proposal.employee_id} · {actionModal.proposal.proposal_id}</strong>
              </div>

              {["submit", "approve", "reject"].includes(actionModal.action) && (
                <>
                  <label className="proposal-remarks-label">
                    {actionModal.action === "reject" ? "Rejection reason *" : "Remarks *"}
                  </label>
                  <textarea
                    className="proposal-remarks"
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    placeholder={
                      actionModal.action === "submit"
                        ? "Add submission remarks for HR review..."
                        : actionModal.action === "approve"
                        ? "Explain the reason for approving this adjustment..."
                        : "Explain why this proposal is being rejected..."
                    }
                  />
                </>
              )}

              <div className="proposal-action-footer">
                <button
                  className="proposal-action-btn secondary"
                  disabled={actionLoading}
                  onClick={() => setActionModal(null)}
                >
                  Cancel
                </button>
                <button
                  className={`proposal-action-btn ${actionModal.action === "reject" ? "danger" : ""}`}
                  disabled={actionLoading}
                  onClick={performAction}
                >
                  {actionLoading
                    ? <LoaderCircle size={14} className="proposal-spin" />
                    : actionModal.action === "submit"
                    ? <Send size={14} />
                    : actionModal.action === "approve"
                    ? <Check size={14} />
                    : actionModal.action === "reject"
                    ? <Ban size={14} />
                    : <Play size={14} />}
                  {actionLoading ? "Processing..." : actionTitle[actionModal.action]}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
