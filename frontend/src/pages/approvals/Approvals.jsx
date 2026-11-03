import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ClipboardCheck, Search, Clock, CheckCircle2, XCircle,
  Eye, ShieldCheck, Filter, RefreshCw, IndianRupee,
  Check, Ban, X, AlertCircle, History, LoaderCircle,
} from "lucide-react";
import api from "../../services/api";

const formatINR = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `₹${number.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
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
  status ? status.charAt(0) + status.slice(1).toLowerCase() : "—";

export default function Approvals() {
  const [proposals, setProposals] = useState([]);
  const [analysisRows, setAnalysisRows] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selected, setSelected] = useState(null);
  const [decision, setDecision] = useState(null);
  const [remarks, setRemarks] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);
    setError("");

    try {
      const [proposalResponse, analysisResponse] = await Promise.all([
        api.get("/api/proposals/", { params: { page: 1, per_page: 100 } }),
        api.get("/api/analysis/results"),
      ]);

      const proposalList = proposalResponse.data?.data;
      const analysisList = analysisResponse.data?.data?.results;

      setProposals(Array.isArray(proposalList) ? proposalList : []);
      setAnalysisRows(Array.isArray(analysisList) ? analysisList : []);
    } catch (err) {
      setError(
        err.response?.data?.message ||
        "Unable to load approval requests. Please check your login and backend connection."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const employeeMap = useMemo(() => {
    const map = new Map();
    analysisRows.forEach((row) => map.set(row.employee_id, row));
    return map;
  }, [analysisRows]);

  const counts = useMemo(() => ({
    total: proposals.length,
    pending: proposals.filter((item) => item.status === "SUBMITTED").length,
    approved: proposals.filter((item) => item.status === "APPROVED").length,
    rejected: proposals.filter((item) => item.status === "REJECTED").length,
  }), [proposals]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return proposals.filter((item) => {
      const employee = employeeMap.get(item.employee_id);
      const matchesSearch =
        !query ||
        String(employee?.employee_name || "").toLowerCase().includes(query) ||
        String(item.employee_id || "").toLowerCase().includes(query) ||
        String(item.proposal_id || "").toLowerCase().includes(query);
      const matchesStatus = status === "all" || item.status === status;
      return matchesSearch && matchesStatus;
    });
  }, [proposals, employeeMap, search, status]);

  const employeeName = (item) =>
    employeeMap.get(item.employee_id)?.employee_name || "Employee name unavailable";

  const currentSalaryINR = (item) => {
    const row = employeeMap.get(item.employee_id);
    const value = Number(row?.normalized_salary_inr);
    return Number.isFinite(value) ? value : null;
  };

  const proposedSalaryINR = (item) => {
    const row = employeeMap.get(item.employee_id);
    if (!row) return null;
    const current = Number(row.normalized_salary);
    const currentINR = Number(row.normalized_salary_inr);
    const proposed = Number(item.proposed_salary);
    if (!Number.isFinite(current) || current <= 0 ||
        !Number.isFinite(currentINR) || !Number.isFinite(proposed)) return null;
    return proposed * (currentINR / current);
  };

  const openDetails = async (item) => {
    setError("");
    setSelected({ ...item, loadingDetails: true });
    try {
      const response = await api.get(
        `/api/proposals/${encodeURIComponent(item.proposal_id)}`
      );
      setSelected(response.data?.data || item);
    } catch (err) {
      setSelected(item);
      setError(err.response?.data?.message || "Unable to load proposal details.");
    }
  };

  const openDecision = (item, action) => {
    setSelected(null);
    setRemarks("");
    setDecision({ item, action });
  };

  const submitDecision = async () => {
    if (!decision) return;
    if (!remarks.trim()) {
      setError(decision.action === "reject"
        ? "Please provide a rejection reason."
        : "Approval remarks are required.");
      return;
    }

    setActionLoading(true);
    setError("");
    setSuccess("");
    try {
      const { item, action } = decision;
      const response = await api.post(
        `/api/proposals/${encodeURIComponent(item.proposal_id)}/${action}`,
        { remarks: remarks.trim() }
      );
      setSuccess(response.data?.message || `Proposal ${action}d successfully.`);
      setDecision(null);
      setRemarks("");
      await loadData(true);
    } catch (err) {
      setError(err.response?.data?.message || `Unable to ${decision.action} this proposal.`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="approvals-page">
      <style>{`
        .approvals-page { color:#eaf2ff; width:100%; animation:approvalFade .3s ease; }
        @keyframes approvalFade { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }
        .approvals-header { display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:25px;flex-wrap:wrap;padding:25px 28px;border:1px solid #168ac0;border-radius:20px;background:linear-gradient(115deg,#123e70,#0b2443); }
        .approvals-heading { display:flex;align-items:center;gap:16px; }
        .approvals-heading-icon { width:56px;height:56px;display:grid;place-items:center;border-radius:16px;color:#65ddff;background:linear-gradient(135deg,#12568a,#087eae);border:1px solid #28b8e866; }
        .approvals-heading h1 { margin:0;color:#f4f8ff;font-size:25px;font-weight:750; }
        .approvals-heading p { margin:7px 0 0;color:#9fc3e9;font-size:13px; }
        .approval-header-badge { display:inline-flex;align-items:center;gap:9px;padding:12px 17px;border:1px solid #16b99b55;border-radius:11px;background:#087f7130;color:#69e8c7;font-size:12px;font-weight:700; }
        .approvals-stats { display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:23px; }
        .approval-stat-card { min-width:0;padding:20px;display:flex;align-items:center;gap:14px;border:1px solid #8bbce51c;border-radius:17px;background:linear-gradient(135deg,#12365b,#0c2340);box-shadow:0 9px 28px #020b1c30; }
        .approval-stat-icon { flex-shrink:0;width:47px;height:47px;display:grid;place-items:center;border-radius:14px; }
        .approval-stat-icon.blue{color:#65d5ff;background:#258de326}.approval-stat-icon.amber{color:#ffd078;background:#eaa52a24}.approval-stat-icon.green{color:#65e4bd;background:#2ac49a24}.approval-stat-icon.red{color:#ff899c;background:#ef536b24}
        .approval-stat-card span{color:#a9bfd9;font-size:12px}.approval-stat-card h2{margin:5px 0 3px;color:#f5f9ff;font-size:26px}.approval-stat-card p{margin:0;color:#7898bb;font-size:11px}
        .approvals-directory,.approval-info-panel{border:1px solid #278bc04d;border-radius:18px;background:linear-gradient(145deg,#102b4bed,#0b203bed);box-shadow:0 10px 30px #020b1c25}
        .approvals-directory{padding:22px}
        .approvals-section-heading{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}
        .approvals-section-heading h3{margin:0;color:#f1f6ff;font-size:18px}.approvals-section-heading p{margin:6px 0 0;color:#8daed2;font-size:12px}
        .approval-record-count{border:1px solid #369edc45;border-radius:30px;padding:8px 13px;color:#79d4ff;background:#087fba18;font-size:11px;white-space:nowrap}
        .approvals-filters{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}
        .approvals-search,.approval-status-filter{height:44px;display:flex;align-items:center;gap:10px;padding:0 13px;border:1px solid #2675a966;border-radius:11px;background:#091e36;color:#37c9f5}
        .approvals-search{flex:1;min-width:220px}.approvals-search input,.approval-status-filter select{width:100%;border:0;outline:0;background:transparent;color:#e7f1ff;font-size:12px}.approvals-search input::placeholder{color:#7894b4}.approval-status-filter{min-width:220px}.approval-status-filter select option{background:#102b48;color:white}
        .approvals-table-wrapper{width:100%;overflow-x:auto}.approvals-table{width:100%;border-collapse:collapse;min-width:900px}
        .approvals-table th{padding:14px 12px;text-align:left;color:#85acd3;background:#12395f;font-size:10px;letter-spacing:.65px;font-weight:750;white-space:nowrap}
        .approvals-table th:first-child{border-radius:10px 0 0 0}.approvals-table th:last-child{border-radius:0 10px 0 0}
        .approvals-table td{padding:15px 12px;border-bottom:1px solid #7797ba1c;color:#dce9fa;font-size:12px;white-space:nowrap}
        .approvals-table tbody tr:hover{background:#258bd10b}.approval-employee-name{color:#f1f6ff;font-weight:700}.approval-employee-id{margin-top:4px;color:#7896b7;font-size:10px}
        .approval-status-badge{display:inline-flex;padding:6px 10px;border-radius:20px;font-size:10px;font-weight:750}
        .approval-status-badge.submitted{color:#ffd27f;background:#e8a62b22}.approval-status-badge.approved{color:#69e3bb;background:#29c39722}.approval-status-badge.rejected{color:#ff91a2;background:#ed536b22}.approval-status-badge.applied{color:#85e6f1;background:#2aafc422}.approval-status-badge.draft{color:#9dcaff;background:#368ee323}
        .approval-action-group{display:flex;align-items:center;gap:6px}.approval-view-btn,.approval-decision-btn{height:32px;padding:0 10px;border:1px solid #399edc55;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;gap:6px;background:#087fba1c;color:#72d0ff;cursor:pointer;font-size:10px;font-weight:700}.approval-decision-btn.approve{background:#145747;border-color:#3bbd9455;color:#8af0cf}.approval-decision-btn.reject{background:#6d2940;border-color:#d45b7955;color:#ffb0bd}
        .approval-view-btn:hover,.approval-decision-btn:hover{filter:brightness(1.25)}
        .approvals-empty-state{text-align:center;padding:54px 15px;white-space:normal}.approvals-empty-icon{margin:0 auto 15px;width:60px;height:60px;display:grid;place-items:center;border-radius:18px;color:#64d9ff;background:#1686c326;border:1px solid #22b9e655}.approvals-empty-state h3{margin:0 0 8px;color:#e8f2ff;font-size:16px}.approvals-empty-state p{max-width:430px;margin:0 auto;color:#829fbe;font-size:12px;line-height:1.7}
        .approval-info-panel{margin-top:19px;padding:19px 22px;display:flex;align-items:center;gap:14px}.approval-info-icon{width:45px;height:45px;flex-shrink:0;border-radius:14px;display:grid;place-items:center;color:#74d7ff;background:#148bc32a}.approval-info-panel h4{margin:0 0 6px;color:#eaf4ff;font-size:13px}.approval-info-panel p{margin:0;color:#8ba6c6;font-size:11px;line-height:1.6}
        .approval-alert{padding:12px 15px;border-radius:10px;margin-bottom:15px;display:flex;align-items:center;gap:9px;font-size:12px}.approval-alert.error{color:#ffabb7;background:#a52e461c;border:1px solid #df61722e}.approval-alert.success{color:#83e7c7;background:#15936c1b;border:1px solid #39c59a30}
        .approval-modal-overlay{position:fixed;inset:0;z-index:1000;padding:18px;display:flex;align-items:center;justify-content:center;background:#020a16c9;backdrop-filter:blur(7px)}.approval-modal{width:min(650px,100%);max-height:88vh;overflow-y:auto;border:1px solid #66b9e64a;border-radius:18px;background:linear-gradient(145deg,#122f50,#0b1e35);box-shadow:0 25px 90px #0009}.approval-modal-header{padding:18px 21px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #91b6d522;background:#112d4c;position:sticky;top:0}.approval-modal-header h3{margin:0;color:#f2f7ff;font-size:16px}.approval-modal-header p{margin:5px 0 0;color:#8da8c8;font-size:11px}.approval-modal-close{width:34px;height:34px;border:1px solid #7598bb44;border-radius:9px;background:#173a5c;color:#c5def8;display:grid;place-items:center;cursor:pointer}.approval-modal-body{padding:21px}.approval-detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.approval-detail-item{padding:13px;border:1px solid #86acd01d;border-radius:11px;background:#091e35a8;min-width:0}.approval-detail-item span{display:block;margin-bottom:7px;color:#809cbd;font-size:10px}.approval-detail-item strong{color:#eaf4ff;font-size:13px;overflow-wrap:anywhere}.approval-detail-section{margin-top:19px}.approval-detail-section h4{display:flex;align-items:center;gap:8px;margin:0 0 11px;color:#cfe5ff;font-size:12px}.approval-reason{padding:13px;border-radius:10px;background:#091e35a8;color:#b2c7df;font-size:11px;line-height:1.7;border:1px solid #86acd01d;white-space:pre-wrap}.approval-history-item{border-left:2px solid #278fc5;padding:2px 0 13px 13px;margin-left:5px;position:relative}.approval-history-item:before{content:"";position:absolute;left:-5px;top:1px;width:8px;height:8px;border-radius:50%;background:#5dc8f3}.approval-history-item strong{color:#dceeff;font-size:11px}.approval-history-item p{margin:5px 0;color:#9bb2cd;font-size:11px}.approval-history-item small{color:#718baa;font-size:10px}
        .approval-remarks-label{display:block;margin:15px 0 7px;color:#bdd3ec;font-size:11px}.approval-remarks{width:100%;min-height:105px;box-sizing:border-box;resize:vertical;border:1px solid #6e9ac044;border-radius:10px;background:#081c32;color:#edf6ff;padding:12px;outline:none;font:inherit;font-size:12px}.approval-remarks:focus{border-color:#42b8ed}.approval-modal-footer{display:flex;justify-content:flex-end;gap:9px;margin-top:19px;flex-wrap:wrap}.approval-modal-btn{border:1px solid #399edc55;border-radius:9px;padding:10px 15px;background:linear-gradient(120deg,#1264bc,#087fae);color:white;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:7px}.approval-modal-btn.secondary{background:#183753;border-color:#7598bb44}.approval-modal-btn.danger{background:#8a3047;border-color:#d45b7955}.approval-modal-btn:disabled{opacity:.55;cursor:not-allowed}.approval-spin{animation:approvalSpin 1s linear infinite}@keyframes approvalSpin{to{transform:rotate(360deg)}}
        @media(max-width:1050px){.approvals-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.approvals-stats{grid-template-columns:1fr}.approvals-directory{padding:14px}.approvals-heading h1{font-size:20px}.approval-detail-grid{grid-template-columns:1fr}.approval-modal-overlay{padding:10px}}
      `}</style>

      <section className="approvals-header">
        <div className="approvals-heading">
          <div className="approvals-heading-icon"><ClipboardCheck size={27} /></div>
          <div>
            <h1>Approval Management</h1>
            <p>Review compensation proposals and monitor approval decisions.</p>
          </div>
        </div>
        <div className="approval-header-badge"><ShieldCheck size={17} /> Approval Workflow</div>
      </section>

      {error && <div className="approval-alert error"><AlertCircle size={17} />{error}<button onClick={() => setError("")} style={{ marginLeft:"auto",border:0,background:"transparent",color:"inherit",cursor:"pointer" }}><X size={15}/></button></div>}
      {success && <div className="approval-alert success"><CheckCircle2 size={17}/>{success}<button onClick={() => setSuccess("")} style={{ marginLeft:"auto",border:0,background:"transparent",color:"inherit",cursor:"pointer" }}><X size={15}/></button></div>}

      <section className="approvals-stats">
        <div className="approval-stat-card"><div className="approval-stat-icon blue"><ClipboardCheck size={23}/></div><div><span>Total Requests</span><h2>{loading ? "—" : counts.total}</h2><p>All proposal requests</p></div></div>
        <div className="approval-stat-card"><div className="approval-stat-icon amber"><Clock size={23}/></div><div><span>Awaiting Review</span><h2>{loading ? "—" : counts.pending}</h2><p>Pending HR decisions</p></div></div>
        <div className="approval-stat-card"><div className="approval-stat-icon green"><CheckCircle2 size={23}/></div><div><span>Approved Requests</span><h2>{loading ? "—" : counts.approved}</h2><p>Approved adjustments</p></div></div>
        <div className="approval-stat-card"><div className="approval-stat-icon red"><XCircle size={23}/></div><div><span>Rejected Requests</span><h2>{loading ? "—" : counts.rejected}</h2><p>Declined requests</p></div></div>
      </section>

      <section className="approvals-directory">
        <div className="approvals-section-heading">
          <div><h3>Approval Requests</h3><p>Track and review submitted compensation proposals.</p></div>
          <div style={{display:"flex",gap:10,alignItems:"center"}}>
            <span className="approval-record-count">{filtered.length} Records</span>
            <button className="approval-view-btn" onClick={() => loadData(true)} disabled={loading || refreshing} title="Refresh requests">
              <RefreshCw size={15} className={refreshing ? "approval-spin" : ""}/> Refresh
            </button>
          </div>
        </div>

        <div className="approvals-filters">
          <div className="approvals-search"><Search size={18}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search employee name, ID or proposal..."/></div>
          <div className="approval-status-filter"><Filter size={17}/><select value={status} onChange={(e) => setStatus(e.target.value)}><option value="all">All Proposal Statuses</option><option value="SUBMITTED">Awaiting Review</option><option value="APPROVED">Approved</option><option value="REJECTED">Rejected</option><option value="APPLIED">Applied</option><option value="DRAFT">Draft</option></select></div>
        </div>

        <div className="approvals-table-wrapper">
          <table className="approvals-table">
            <thead><tr><th>EMPLOYEE</th><th>DEPARTMENT</th><th>REQUEST TYPE</th><th>REQUESTED BY</th><th>SUBMITTED DATE</th><th>STATUS</th><th>ACTION</th></tr></thead>
            <tbody>
              {loading ? <tr><td colSpan="7"><div className="approvals-empty-state"><LoaderCircle className="approval-spin" size={24}/><p>Loading approval requests...</p></div></td></tr>
              : filtered.length === 0 ? <tr><td colSpan="7"><div className="approvals-empty-state"><div className="approvals-empty-icon"><ClipboardCheck size={30}/></div><h3>{proposals.length ? "No matching requests" : "No approval requests available"}</h3><p>{proposals.length ? "Try changing your search or status filter." : "Submit a draft proposal from the Proposals page. It will appear here for HR review."}</p></div></td></tr>
              : filtered.map((item) => (
                <tr key={item.proposal_id}>
                  <td><div className="approval-employee-name">{employeeName(item)}</div><div className="approval-employee-id">{item.employee_id}</div></td>
                  <td>—</td>
                  <td>{item.issue_type || "Compensation Adjustment"}</td>
                  <td>{item.proposed_by || "—"}</td>
                  <td>{formatDate(item.created_at)}</td>
                  <td><span className={`approval-status-badge ${item.status?.toLowerCase()}`}>{statusLabel(item.status)}</span></td>
                  <td><div className="approval-action-group">
                    <button className="approval-view-btn" title="View details and history" onClick={() => openDetails(item)}><Eye size={15}/></button>
                    {item.status === "SUBMITTED" && <>
                      <button className="approval-decision-btn approve" onClick={() => openDecision(item,"approve")}><Check size={13}/> Approve</button>
                      <button className="approval-decision-btn reject" onClick={() => openDecision(item,"reject")}><Ban size={13}/> Reject</button>
                    </>}
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="approval-info-panel">
        <div className="approval-info-icon"><ShieldCheck size={23}/></div>
        <div><h4>Controlled Approval Process</h4><p>Only submitted proposals can be approved or rejected. Every decision requires remarks and is recorded in the proposal history.</p></div>
      </section>

      {selected && <div className="approval-modal-overlay" onClick={() => setSelected(null)}>
        <div className="approval-modal" onClick={(e) => e.stopPropagation()}>
          <div className="approval-modal-header"><div><h3>Approval Request Details</h3><p>{selected.proposal_id}</p></div><button className="approval-modal-close" onClick={() => setSelected(null)}><X size={17}/></button></div>
          <div className="approval-modal-body">
            {selected.loadingDetails ? <div className="approvals-empty-state"><LoaderCircle className="approval-spin" size={22}/><p>Loading proposal history...</p></div> : <>
              <div style={{display:"flex",justifyContent:"space-between",gap:12,flexWrap:"wrap",marginBottom:16}}><div><strong style={{color:"#f1f7ff",fontSize:15}}>{employeeName(selected)}</strong><div style={{color:"#809cbd",fontSize:11,marginTop:5}}>{selected.employee_id}</div></div><span className={`approval-status-badge ${selected.status?.toLowerCase()}`}>{statusLabel(selected.status)}</span></div>
              <div className="approval-detail-grid">
                <div className="approval-detail-item"><span>Current Salary (INR normalized)</span><strong>{currentSalaryINR(selected) === null ? "Unavailable" : formatINR(currentSalaryINR(selected))}</strong></div>
                <div className="approval-detail-item"><span>Proposed Salary (INR normalized)</span><strong>{proposedSalaryINR(selected) === null ? "Unavailable" : formatINR(proposedSalaryINR(selected))}</strong></div>
                <div className="approval-detail-item"><span>Proposal Amount</span><strong>{selected.proposed_salary} {selected.currency_code}</strong></div>
                <div className="approval-detail-item"><span>Issue Type</span><strong>{selected.issue_type || "—"}</strong></div>
                <div className="approval-detail-item"><span>Requested By</span><strong>{selected.proposed_by || "—"}</strong></div>
                <div className="approval-detail-item"><span>Submitted / Created</span><strong>{formatDate(selected.created_at)}</strong></div>
                <div className="approval-detail-item"><span>Approved By</span><strong>{selected.approved_by || "—"}</strong></div>
                <div className="approval-detail-item"><span>Rejected By</span><strong>{selected.rejected_by || "—"}</strong></div>
              </div>
              <div className="approval-detail-section"><h4><IndianRupee size={15}/> Recommendation Reason</h4><div className="approval-reason">{selected.reason || "No reason provided."}</div></div>
              <div className="approval-detail-section"><h4><History size={15}/> Approval History</h4>
                {selected.history?.length ? selected.history.map((entry,index)=><div className="approval-history-item" key={`${entry.new_status}-${index}`}><strong>{entry.previous_status ? `${statusLabel(entry.previous_status)} → ${statusLabel(entry.new_status)}` : statusLabel(entry.new_status)}</strong><p>{entry.remarks || "No remarks recorded."}</p><small>{entry.changed_by || "System"} · {formatDate(entry.changed_at)}</small></div>) : <p style={{color:"#819bb9",fontSize:11}}>No history records available.</p>}
              </div>
              {selected.status === "SUBMITTED" && <div className="approval-modal-footer"><button className="approval-modal-btn" onClick={() => openDecision(selected,"approve")}><Check size={14}/> Approve</button><button className="approval-modal-btn danger" onClick={() => openDecision(selected,"reject")}><Ban size={14}/> Reject</button></div>}
            </>}
          </div>
        </div>
      </div>}

      {decision && <div className="approval-modal-overlay" onClick={() => !actionLoading && setDecision(null)}>
        <div className="approval-modal" onClick={(e) => e.stopPropagation()}>
          <div className="approval-modal-header"><div><h3>{decision.action === "approve" ? "Approve Proposal" : "Reject Proposal"}</h3><p>{decision.item.proposal_id}</p></div><button className="approval-modal-close" disabled={actionLoading} onClick={() => setDecision(null)}><X size={17}/></button></div>
          <div className="approval-modal-body">
            <div className="approval-alert" style={{color:"#a9dfff",background:"#1689c31a",border:"1px solid #4bb9e52c"}}><AlertCircle size={17}/>{decision.action === "approve" ? "Confirm this compensation adjustment. Approval remarks are required." : "Reject this proposal with a clear reason. This decision will be recorded in history."}</div>
            <div className="approval-detail-item"><span>Employee / Proposal</span><strong>{decision.item.employee_id} · {decision.item.proposal_id}</strong></div>
            <label className="approval-remarks-label">{decision.action === "reject" ? "Rejection reason *" : "Approval remarks *"}</label>
            <textarea className="approval-remarks" value={remarks} onChange={(e)=>setRemarks(e.target.value)} placeholder={decision.action === "approve" ? "Explain why this adjustment is approved..." : "Explain why this proposal is rejected..."}/>
            <div className="approval-modal-footer">
              <button className="approval-modal-btn secondary" disabled={actionLoading} onClick={()=>setDecision(null)}>Cancel</button>
              <button className={`approval-modal-btn ${decision.action === "reject" ? "danger" : ""}`} disabled={actionLoading || !remarks.trim()} onClick={submitDecision}>
                {actionLoading ? <LoaderCircle size={14} className="approval-spin"/> : decision.action === "approve" ? <Check size={14}/> : <Ban size={14}/>}
                {actionLoading ? "Processing..." : decision.action === "approve" ? "Confirm Approval" : "Confirm Rejection"}
              </button>
            </div>
          </div>
        </div>
      </div>}
    </div>
  );
}
