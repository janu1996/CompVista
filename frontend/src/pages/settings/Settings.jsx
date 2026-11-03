
import { useEffect, useState } from "react";
import {
  Settings as SettingsIcon,
  UserRound,
  Building2,
  Bell,
  ShieldCheck,
  Save,
  IndianRupee,
  Mail,
  Lock,
  Globe,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

const STORAGE_KEY = "compvista_settings";

const defaultSettings = {
  profile: {
    name: "Admin User",
    email: "",
    role: "Administrator",
  },
  organization: {
    name: "CompVista Organization",
    currency: "INR",
    timezone: "Asia/Kolkata",
  },
  notifications: {
    emailAlerts: true,
    equityAlerts: true,
    proposalUpdates: true,
    approvalUpdates: true,
  },
};

export default function Settings() {
  const [profile, setProfile] = useState(defaultSettings.profile);
  const [organization, setOrganization] = useState(
    defaultSettings.organization
  );
  const [notifications, setNotifications] = useState(
    defaultSettings.notifications
  );
  const [saveStatus, setSaveStatus] = useState("");

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);

      if (saved) {
        const parsed = JSON.parse(saved);

        setProfile({ ...defaultSettings.profile, ...parsed.profile });
        setOrganization({
          ...defaultSettings.organization,
          ...parsed.organization,
        });
        setNotifications({
          ...defaultSettings.notifications,
          ...parsed.notifications,
        });
      }
    } catch (error) {
      console.error("Unable to load settings:", error);
      setSaveStatus("error");
    }
  }, []);

  const updateProfile = (key, value) => {
    setProfile((prev) => ({ ...prev, [key]: value }));
    setSaveStatus("");
  };

  const updateOrganization = (key, value) => {
    setOrganization((prev) => ({ ...prev, [key]: value }));
    setSaveStatus("");
  };

  const updateNotification = (key) => {
    setNotifications((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaveStatus("");
  };

  const handleSave = (event) => {
    event.preventDefault();

    if (!profile.name.trim()) {
      setSaveStatus("validation");
      return;
    }

    if (
      profile.email &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)
    ) {
      setSaveStatus("validation");
      return;
    }

    try {
      const settings = {
        profile,
        organization,
        notifications,
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      setSaveStatus("success");
    } catch (error) {
      console.error("Unable to save settings:", error);
      setSaveStatus("error");
    }
  };

  return (
    <div className="settings-page">
      <section className="settings-header">
        <div className="settings-heading">
          <div className="settings-heading-icon">
            <SettingsIcon size={27} />
          </div>
          <div>
            <h1>Settings</h1>
            <p>
              Manage your account, organization, and platform preferences.
            </p>
          </div>
        </div>
      </section>

      <form onSubmit={handleSave} className="settings-form">
        <section className="settings-panel">
          <div className="settings-panel-heading">
            <div className="settings-panel-icon blue">
              <UserRound size={21} />
            </div>
            <div>
              <h3>Profile Information</h3>
              <p>Manage your administrator account details.</p>
            </div>
          </div>

          <div className="settings-fields-grid">
            <div className="settings-field">
              <label>Full Name</label>
              <input
                value={profile.name}
                onChange={(e) => updateProfile("name", e.target.value)}
                placeholder="Enter your name"
                required
              />
            </div>

            <div className="settings-field">
              <label>Email Address</label>
              <div className="settings-input-icon">
                <Mail size={17} />
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => updateProfile("email", e.target.value)}
                  placeholder="Enter email address"
                />
              </div>
            </div>

            <div className="settings-field">
              <label>Account Role</label>
              <input value={profile.role} disabled />
            </div>
          </div>
        </section>

        <section className="settings-panel">
          <div className="settings-panel-heading">
            <div className="settings-panel-icon cyan">
              <Building2 size={21} />
            </div>
            <div>
              <h3>Organization Preferences</h3>
              <p>
                Configure organization and regional display preferences.
              </p>
            </div>
          </div>

          <div className="settings-fields-grid">
            <div className="settings-field">
              <label>Organization Name</label>
              <input
                value={organization.name}
                onChange={(e) =>
                  updateOrganization("name", e.target.value)
                }
              />
            </div>

            <div className="settings-field">
              <label>Display Currency</label>
              <div className="settings-input-icon">
                <IndianRupee size={17} />
                <select
                  value="INR"
                  disabled
                  onChange={(e) =>
                    updateOrganization("currency", e.target.value)
                  }
                >
                  <option value="INR">INR — Indian Rupee (₹)</option>
                </select>
              </div>
            </div>

            <div className="settings-field">
              <label>Time Zone</label>
              <div className="settings-input-icon">
                <Globe size={17} />
                <select
                  value={organization.timezone}
                  onChange={(e) =>
                    updateOrganization("timezone", e.target.value)
                  }
                >
                  <option value="Asia/Kolkata">
                    India Standard Time (IST)
                  </option>
                </select>
              </div>
            </div>
          </div>
        </section>

        <section className="settings-panel">
          <div className="settings-panel-heading">
            <div className="settings-panel-icon purple">
              <Bell size={21} />
            </div>
            <div>
              <h3>Notification Preferences</h3>
              <p>Choose which platform updates you want to receive.</p>
            </div>
          </div>

          <div className="settings-notification-list">
            {[
              {
                key: "emailAlerts",
                title: "Email Notifications",
                description:
                  "Receive important platform updates through email.",
              },
              {
                key: "equityAlerts",
                title: "Equity Alerts",
                description:
                  "Get notified about compensation disparities.",
              },
              {
                key: "proposalUpdates",
                title: "Proposal Updates",
                description:
                  "Receive updates when proposals change status.",
              },
              {
                key: "approvalUpdates",
                title: "Approval Updates",
                description:
                  "Receive notifications about approval decisions.",
              },
            ].map((item) => (
              <label className="settings-toggle-row" key={item.key}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.description}</span>
                </div>
                <input
                  type="checkbox"
                  checked={notifications[item.key]}
                  onChange={() => updateNotification(item.key)}
                />
              </label>
            ))}
          </div>
        </section>

        <section className="settings-security-note">
          <div className="settings-security-icon">
            <ShieldCheck size={22} />
          </div>
          <div>
            <h4>Account Security</h4>
            <p>
              Your login and authentication are managed separately.
              Password management is not available from this settings page.
            </p>
          </div>
          <Lock size={19} className="settings-lock-icon" />
        </section>

        {saveStatus && (
          <div
            className={`settings-status-message ${
              saveStatus === "success" ? "success" : "error"
            }`}
            role="status"
          >
            {saveStatus === "success" ? (
              <>
                <CheckCircle2 size={18} />
                Preferences saved successfully on this browser.
              </>
            ) : saveStatus === "validation" ? (
              <>
                <AlertCircle size={18} />
                Please enter a valid name and email address.
              </>
            ) : (
              <>
                <AlertCircle size={18} />
                Unable to save preferences. Please try again.
              </>
            )}
          </div>
        )}

        <div className="settings-save-area">
          <button type="submit" className="settings-save-btn">
            <Save size={17} />
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
}
