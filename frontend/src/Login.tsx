import React, { useState } from 'react';
import './Login.css';
import queryGuardHero from './assets/queryguard-hero.jpg';
import { api } from './lib/api';
import type { User } from './types/queryguard';
import { Shield, ShieldAlert, Eye, EyeOff, Lock, UserCheck } from 'lucide-react';

interface LoginProps {
  onLogin?: (user: User) => void;
  onBackToDashboard?: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [identifier, setIdentifier] = useState('EMP-DBA-01');
  const [password, setPassword] = useState('Dba@Guard2026!');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sign up form state
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupRole, setSignupRole] = useState<'ENGINEER' | 'VIEWER'>('ENGINEER');
  const [signupPassword, setSignupPassword] = useState('');

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.loginUser(identifier.trim(), password);
      if (res.success && res.user) {
        if (onLogin) {
          onLogin(res.user);
        }
      } else {
        setErrorMessage(res.message || 'Invalid credentials. Please verify your Employee ID and password.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Authentication failed. Please check database connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      alert(`Access requested for ${signupName} (${signupRole}). Enterprise compliance requires Lead DBA (EMP-DBA-01) approval before provisioning.`);
      setIsSignUp(false);
    }, 600);
  };

  return (
    <div className="login-wrapper">
      <div className={`auth-card ${isSignUp ? 'right-panel-active' : ''}`} id="authCard">
        {/* Sign In Form Container (Left half in default state) */}
        <div className="form-container sign-in-container">
          <form onSubmit={handleSignIn}>
            <div className="form-header-badge">
              <Shield size={20} className="brand-icon" />
              <span className="brand-badge-text">QUERYGUARD AI</span>
            </div>

            <h2>Employee Sign In</h2>
            <p className="form-subtitle">
              Enter your organizational credentials to access your authorized database telemetry & tuning tools
            </p>

            {/* Error Banner */}
            {errorMessage && (
              <div className="login-error-banner">
                <ShieldAlert size={14} style={{ flexShrink: 0 }} />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="form-fields-group">
              <div className="input-group">
                <label>Employee ID or Email</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. EMP-DBA-01 or priya.sharma@queryguard.io"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>

              <div className="input-group">
                <div className="password-header-row">
                  <label>Password</label>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="password-toggle-btn"
                  >
                    {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                    <span>{showPassword ? 'Hide' : 'Show'}</span>
                  </button>
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-field"
                  placeholder="Enter your account password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            <div className="form-options-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember me</span>
              </label>

              <button
                type="button"
                className="forgot-link"
                onClick={() => {
                  alert(
                    "Employee Default Credentials:\n\n" +
                    "• Level 3 Lead DBA: EMP-DBA-01 | Dba@Guard2026!\n" +
                    "• Level 2 Senior Engineer: EMP-ENG-02 | Eng@Guard2026!\n" +
                    "• Level 1 Compliance Auditor: EMP-AUD-03 | Auditor@Guard2026!"
                  );
                }}
              >
                Forgot password?
              </button>
            </div>

            <button type="submit" className="dark-pill-btn" disabled={isLoading}>
              {isLoading ? 'AUTHENTICATING...' : 'SIGN IN'}
            </button>
          </form>
        </div>

        {/* Sign Up Form Container (Slides into right half) */}
        <div className="form-container sign-up-container">
          <form onSubmit={handleSignUp}>
            <div className="form-header-badge">
              <Lock size={18} className="brand-icon" />
              <span className="brand-badge-text">ACCESS REQUEST</span>
            </div>

            <h2>Register Employee</h2>
            <p className="form-subtitle">
              Submit employee profile for Lead DBA role provisioning
            </p>

            <div className="form-fields-group">
              <div className="input-group">
                <label>Full Employee Name</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. Jordan Smith"
                  value={signupName}
                  onChange={(e) => setSignupName(e.target.value)}
                  required
                />
              </div>

              <div className="input-group">
                <label>Corporate Work Email</label>
                <input
                  type="email"
                  className="input-field"
                  placeholder="e.g. jordan.smith@queryguard.io"
                  value={signupEmail}
                  onChange={(e) => setSignupEmail(e.target.value)}
                  required
                />
              </div>

              <div className="input-group">
                <label>Requested Role Hierarchy</label>
                <select
                  value={signupRole}
                  onChange={(e) => setSignupRole(e.target.value as any)}
                  className="input-field"
                  style={{ cursor: 'pointer' }}
                >
                  <option value="ENGINEER">Level 2: Platform Engineer (Operational)</option>
                  <option value="VIEWER">Level 1: Compliance Auditor (Read-Only)</option>
                </select>
              </div>

              <div className="input-group">
                <label>Proposed Password</label>
                <input
                  type="password"
                  className="input-field"
                  placeholder="Create secure enterprise password"
                  value={signupPassword}
                  onChange={(e) => setSignupPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="dark-pill-btn" disabled={isLoading} style={{ marginTop: 12 }}>
              {isLoading ? 'SUBMITTING...' : 'REQUEST ACCESS'}
            </button>
          </form>
        </div>

        {/* Sliding Overlay Container */}
        <div className="overlay-container">
          <div className="overlay" style={{ backgroundImage: `linear-gradient(rgba(11, 25, 44, 0.62), rgba(11, 25, 44, 0.78)), url(${queryGuardHero})` }}>
            {/* Left Overlay (shown when viewing Sign Up) */}
            <div className="overlay-panel overlay-left">
              <h2>Existing Employee?</h2>
              <p>
                Sign in with your verified organizational ID or email to access your role-gated workspace.
              </p>
              <button
                type="button"
                className="outline-pill-btn"
                onClick={() => {
                  setIsSignUp(false);
                  setErrorMessage(null);
                }}
              >
                SIGN IN
              </button>
            </div>

            {/* Right Overlay (shown when viewing Sign In) */}
            <div className="overlay-panel overlay-right">
              <h2>QueryGuard AI</h2>
              <p>
                Self-Driving PostgreSQL Tuning & Autonomous GNN Optimization Copilot.
              </p>
              <button
                type="button"
                className="outline-pill-btn"
                onClick={() => {
                  setIsSignUp(true);
                  setErrorMessage(null);
                }}
              >
                REQUEST ACCESS
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

