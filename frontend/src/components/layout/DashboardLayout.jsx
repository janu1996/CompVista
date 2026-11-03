import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="dashboard-layout">
      <div className={`sidebar-wrapper ${mobileOpen ? "mobile-open" : ""}`}>
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
        />
      </div>

      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <main className={`main-content ${collapsed ? "main-expanded" : ""}`}>
        <Navbar onMenuClick={() => setMobileOpen(!mobileOpen)} />

        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}