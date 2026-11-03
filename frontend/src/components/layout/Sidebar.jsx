
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  ChartNoAxesCombined,
  Users,
  FileText,
  ClipboardCheck,
  AlertTriangle,
  Database,
  FileBarChart,
  Settings,
  LogOut,
  ShieldCheck,
  ChevronLeft,
} from "lucide-react";

const menuItems = [
  { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { name: "Compensation Analysis", path: "/compensation", icon: ChartNoAxesCombined },
  { name: "Employees", path: "/employees", icon: Users },
  { name: "Proposals", path: "/proposals", icon: FileText },
  { name: "Approvals", path: "/approvals", icon: ClipboardCheck },
  { name: "Anomalies", path: "/anomalies", icon: AlertTriangle },
  { name: "Data Quality", path: "/data-quality", icon: Database },
  { name: "Reports & Exports", path: "/reports", icon: FileBarChart },
];

export default function Sidebar({ collapsed = false, onToggle }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("compvista_token");
    navigate("/login", { replace: true });
  };

  return (
    <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
      <div className="sidebar-brand">
        <div className="brand-icon">
          <ShieldCheck size={25} />
        </div>

        {!collapsed && (
          <div className="brand-info">
            <h2>CompVista</h2>
            <span>Equity Intelligence</span>
          </div>
        )}

        <button
          className="sidebar-toggle"
          onClick={onToggle}
          title="Toggle sidebar"
          type="button"
        >
          <ChevronLeft size={18} />
        </button>
      </div>

      <div className="sidebar-section-label">
        {!collapsed && "WORKSPACE"}
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              title={collapsed ? item.name : ""}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "active" : ""}`
              }
            >
              <Icon size={19} strokeWidth={1.8} />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        {!collapsed && (
          <div className="sidebar-section-label">PREFERENCES</div>
        )}

        <NavLink
          to="/settings"
          title={collapsed ? "Settings" : ""}
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <Settings size={19} strokeWidth={1.8} />
          {!collapsed && <span>Settings</span>}
        </NavLink>

        <button
          type="button"
          className="sidebar-link logout-link"
          onClick={handleLogout}
          title={collapsed ? "Logout" : ""}
        >
          <LogOut size={19} strokeWidth={1.8} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

      {!collapsed && (
        <div className="sidebar-footer">
          <div className="footer-status-dot" />
          <span>System Operational</span>
        </div>
      )}
    </aside>
  );
}
