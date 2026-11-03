
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import DashboardLayout from "./components/layout/DashboardLayout";
import Dashboard from "./pages/dashboard/Dashboard";
import Login from "./pages/auth/Login";

import CompensationAnalysis from "./pages/compensation/CompensationAnalysis";
import Employees from "./pages/employees/Employees";
import Proposals from "./pages/proposals/Proposals";
import Approvals from "./pages/approvals/Approvals";
import Anomalies from "./pages/anomalies/Anomalies";
import DataQuality from "./pages/data-quality/DataQuality";
import Reports from "./pages/reports/Reports";
import Settings from "./pages/settings/Settings";

import "./index.css";
import "./styles/dashboard.css";
import "./styles/layout.css";
import "./styles/auth.css";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("compvista_token");

  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="compensation" element={<CompensationAnalysis />} />
          <Route path="employees" element={<Employees />} />
          <Route path="proposals" element={<Proposals />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="anomalies" element={<Anomalies />} />
          <Route path="data-quality" element={<DataQuality />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
