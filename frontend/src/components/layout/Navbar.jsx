
import { useEffect, useRef, useState } from "react";
import {
  Search,
  Bell,
  Menu,
  ChevronDown,
  UserRound,
  Settings,
  LogOut,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

export default function Navbar({ onMenuClick }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);

  useEffect(() => {
    let mounted = true;

    const fetchUser = async () => {
      try {
        const response = await api.get("/api/auth/me");

        if (mounted && response.data?.success) {
          setUser(response.data.data);
        }
      } catch (error) {
        if (error.response?.status === 401) {
          localStorage.removeItem("compvista_token");
          navigate("/login", { replace: true });
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchUser();

    return () => {
      mounted = false;
    };
  }, [navigate]);

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target)
      ) {
        setProfileOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  const displayName = user?.email || "User";
  const displayRole = user?.role || "Loading...";
  const avatar = displayName.charAt(0).toUpperCase();

  const handleLogout = () => {
    localStorage.removeItem("compvista_token");
    setProfileOpen(false);
    navigate("/login", { replace: true });
  };

  return (
    <header className="navbar">
      <div className="navbar-left">
        <button
          className="mobile-menu-btn"
          onClick={onMenuClick}
          aria-label="Open menu"
        >
          <Menu size={21} />
        </button>

        <div className="navbar-heading">
          <h2>Welcome to CompVista</h2>
          <p>Analyze · Detect · Propose · Ensure Pay Equity</p>
        </div>
      </div>

      <div className="navbar-right">
        <div className="navbar-search">
          <Search size={19} />
          <input
            type="text"
            placeholder="Search employee, role, or ID..."
            aria-label="Search employee, role, or ID"
          />
        </div>

        <button
          className="navbar-icon-btn notification-btn"
          title="Notifications"
          aria-label="Notifications"
        >
          <Bell size={22} />
          <span className="notification-dot" />
        </button>

        <div className="navbar-profile-wrapper" ref={profileRef}>
          <button
            type="button"
            className="navbar-profile"
            onClick={() => setProfileOpen((previous) => !previous)}
            aria-expanded={profileOpen}
            aria-label="Open profile menu"
          >
            <div className="profile-avatar">
              {loading ? "..." : avatar}
            </div>

            <div className="profile-info">
              <strong>{loading ? "Loading..." : displayName}</strong>
              <span>{displayRole}</span>
            </div>

            <ChevronDown
              size={16}
              className={`profile-chevron ${profileOpen ? "profile-chevron-open" : ""}`}
            />
          </button>

          {profileOpen && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-header">
                <strong>{displayName}</strong>
                <span>{displayRole} Account</span>
              </div>

              <button
                type="button"
                className="profile-dropdown-item"
                onClick={() => {
                  setProfileOpen(false);
                  navigate("/settings");
                }}
              >
                <UserRound size={17} />
                My Profile
              </button>

              <button
                type="button"
                className="profile-dropdown-item"
                onClick={() => {
                  setProfileOpen(false);
                  navigate("/settings");
                }}
              >
                <Settings size={17} />
                Account Settings
              </button>

              <div className="profile-dropdown-divider" />

              <button
                type="button"
                className="profile-dropdown-item logout-dropdown-item"
                onClick={handleLogout}
              >
                <LogOut size={17} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
