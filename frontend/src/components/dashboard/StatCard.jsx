import {
  Users,
  AlertTriangle,
  TrendingUp,
  FileText,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

const icons = {
  employees: Users,
  alerts: AlertTriangle,
  ratio: TrendingUp,
  proposals: FileText,
};

export default function StatCard({
  title,
  value,
  change,
  trend = "up",
  icon = "employees",
  accent = "blue",
  subtitle,
  loading = false,
}) {
  const Icon = icons[icon] || Users;

  return (
    <div className={`stat-card accent-${accent}`}>
      <div className="stat-card-icon">
        <Icon size={27} strokeWidth={2.2} />
      </div>

      <div className="stat-card-content">
        <p className="stat-card-title">{title}</p>

        <div className="stat-value-row">
          {loading ? (
            <div className="stat-skeleton" />
          ) : (
            <h2 className="stat-card-value">{value ?? "—"}</h2>
          )}

          {change && (
            <span className={`stat-change ${trend === "up" ? "positive" : "negative"}`}>
              {trend === "up" ? (
                <ArrowUpRight size={15} />
              ) : (
                <ArrowDownRight size={15} />
              )}
              {change}
            </span>
          )}
        </div>

        {subtitle && (
          <p className="stat-card-subtitle">{subtitle}</p>
        )}
      </div>
    </div>
  );
}