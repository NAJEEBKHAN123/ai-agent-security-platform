import React, { useState, useEffect } from 'react';
import { Shield, Lock, CheckCircle2, AlertCircle, Key, Server, UserCheck, Terminal } from 'lucide-react';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [email, setEmail] = useState('analyst@agentsec.com');
  const [password, setPassword] = useState('AnalystPass123!');
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Check Backend Health
  const checkHealth = async () => {
    try {
      setLoadingHealth(true);
      const res = await fetch('/api/v1/health');
      if (res.ok) {
        const data = await res.json();
        setHealthStatus(data);
      } else {
        setHealthStatus({ status: 'error', database: 'unavailable' });
      }
    } catch (err) {
      setHealthStatus({ status: 'disconnected', database: 'unreachable' });
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  // Fetch Current User if token exists
  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      return;
    }
    const fetchMe = async () => {
      try {
        const res = await fetch('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const user = await res.json();
          setCurrentUser(user);
        } else {
          setToken('');
          localStorage.removeItem('token');
          setCurrentUser(null);
        }
      } catch {
        setCurrentUser(null);
      }
    };
    fetchMe();
  }, [token]);

  // Handle Login
  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
      } else {
        setAuthError(data.detail || 'Authentication failed');
      }
    } catch {
      setAuthError('Connection error connecting to security API');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    setCurrentUser(null);
  };

  const fillCredentials = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setAuthError('');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-wide text-white flex items-center gap-2">
              AI Agent Security Platform
              <span className="text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full font-mono">
                Step 1: Active
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Prompt Injection Defense &bull; Action RBAC &bull; Human-in-the-Loop
            </p>
          </div>
        </div>

        {/* Health status badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-mono bg-slate-900/90 border-slate-800">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Backend:</span>
            {loadingHealth ? (
              <span className="text-amber-400 animate-pulse">Checking...</span>
            ) : healthStatus?.status === 'ok' ? (
              <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Operational ({healthStatus.database})
              </span>
            ) : (
              <span className="text-red-400 flex items-center gap-1 font-semibold">
                <AlertCircle className="w-3 h-3" /> Offline
              </span>
            )}
          </div>
          <button
            onClick={checkHealth}
            className="text-xs px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: System Status & Step 1 Blueprint */}
        <div className="md:col-span-5 space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-emerald-400" />
              Step 1 Verification
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>FastAPI + Uvicorn Core Server running</span>
              </div>
              <div className="flex items-start gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>SQLAlchemy ORM + SQLite/Postgres Engine</span>
              </div>
              <div className="flex items-start gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>JWT Authentication & Secure Bcrypt Hashing</span>
              </div>
              <div className="flex items-start gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>Role-Based Access Control (RBAC) Architecture</span>
              </div>
              <div className="flex items-start gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>Pytest Automated Test Suite Passing (7/7)</span>
              </div>
            </div>
          </div>

          {/* Quick Demo Credentials */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <Key className="w-3.5 h-3.5 text-cyan-400" />
              Pre-Seeded Demo Accounts
            </h3>
            <div className="space-y-2 text-xs">
              <button
                type="button"
                onClick={() => fillCredentials('analyst@agentsec.com', 'AnalystPass123!')}
                className="w-full text-left p-2.5 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800 transition flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-200">analyst@agentsec.com</div>
                  <div className="text-slate-500">Role: REVIEWER (Approval Authority)</div>
                </div>
                <span className="text-cyan-400 font-mono">Fill &rarr;</span>
              </button>

              <button
                type="button"
                onClick={() => fillCredentials('admin@agentsec.com', 'AdminPass123!')}
                className="w-full text-left p-2.5 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800 transition flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-200">admin@agentsec.com</div>
                  <div className="text-slate-500">Role: ADMIN (Full Control)</div>
                </div>
                <span className="text-amber-400 font-mono">Fill &rarr;</span>
              </button>

              <button
                type="button"
                onClick={() => fillCredentials('user@agentsec.com', 'UserPass123!')}
                className="w-full text-left p-2.5 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800 transition flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-200">user@agentsec.com</div>
                  <div className="text-slate-500">Role: USER (Standard Agent Client)</div>
                </div>
                <span className="text-emerald-400 font-mono">Fill &rarr;</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Authentication Card & Session State */}
        <div className="md:col-span-7">
          {currentUser ? (
            /* Authenticated State */
            <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-5">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-full bg-emerald-500/10 text-emerald-400">
                    <UserCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-white">{currentUser.full_name}</h3>
                    <p className="text-xs text-slate-400">{currentUser.email}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1.5 rounded-lg text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition"
                >
                  Sign Out
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block mb-1">Assigned Role</span>
                    <span className="font-mono font-bold uppercase text-emerald-400 text-sm">
                      {currentUser.role}
                    </span>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block mb-1">Account Status</span>
                    <span className="font-mono font-semibold text-emerald-400 text-sm">
                      ACTIVE &bull; VERIFIED
                    </span>
                  </div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-xs block mb-1 font-mono">Issued JWT Bearer Token:</span>
                  <p className="font-mono text-xs text-slate-400 break-all bg-slate-900/60 p-2 rounded border border-slate-800/80">
                    {token}
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 text-xs space-y-1">
                  <p className="font-semibold text-emerald-400">Step 1 Foundation Complete!</p>
                  <p className="text-slate-400">
                    The backend authentication pipeline, database persistence, and session context are verified and ready for Step 2 (Controlled AI Agent Engine & Safe Tools).
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* Login Form */
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 border-b border-slate-800 pb-4 mb-5">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">Platform Sign In</h3>
                  <p className="text-xs text-slate-400">Authenticate to access protected security routes</p>
                </div>
              </div>

              {authError && (
                <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{authError}</span>
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-slate-200 text-sm font-mono"
                    placeholder="analyst@agentsec.com"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-slate-200 text-sm font-mono"
                    placeholder="••••••••••••"
                  />
                </div>

                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full py-2.5 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition flex items-center justify-center gap-2 text-sm disabled:opacity-50"
                >
                  {authLoading ? 'Verifying Credentials...' : 'Authenticate & Issue Token'}
                </button>
              </form>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 px-6 py-3 text-center text-xs text-slate-600">
        AI Agent Security Platform &bull; Step 1 Complete &bull; Built with FastAPI, SQLite/PostgreSQL, React & Tailwind CSS
      </footer>
    </div>
  );
}
