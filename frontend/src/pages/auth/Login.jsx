
import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { ShieldCheck, Lock, Mail, Eye, EyeOff } from "lucide-react";
import api from "../../services/api";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (localStorage.getItem("compvista_token")) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const response = await api.post("/api/auth/login", {
        email: email.trim(),
        password,
      });

      const token = response.data?.data?.access_token;

      if (!response.data?.success || !token) {
        throw new Error(
          response.data?.message || "Invalid login response."
        );
      }

      localStorage.setItem("compvista_token", token);
      navigate("/dashboard", { replace: true });

    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.response?.data?.msg ||
        err.message ||
        "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-glow login-glow-one" />
      <div className="login-glow login-glow-two" />

      <div className="login-card">
        <div className="login-brand">
          <div className="login-brand-icon">
            <ShieldCheck size={32} />
          </div>
          <h1>CompVista</h1>
          <p>Equity Intelligence</p>
        </div>

        <div className="login-heading">
          <h2>Welcome Back</h2>
          <p>Sign in to access your compensation dashboard.</p>
        </div>

        <form onSubmit={handleLogin}>
          <label htmlFor="email">Email / Username</label>

          <div className="login-input-wrap">
            <Mail size={19} />
            <input
              id="email"
              type="text"
              placeholder="Enter your email or username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </div>

          <label htmlFor="password">Password</label>

          <div className="login-input-wrap">
            <Lock size={19} />
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />

            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
            </button>
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="login-submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="login-footer">
          <ShieldCheck size={16} />
          <span>Secure HR & Administrator Access</span>
        </div>
      </div>
    </div>
  );
}
