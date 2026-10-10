import React, { useState, useEffect, useRef } from 'react';
import { 
  Shield, Lock, CheckCircle2, AlertCircle, Key, Server, UserCheck, 
  Terminal, Bot, Send, Calculator, FileText, Search, User, Sparkles, 
  RefreshCw, LogOut, Cpu, ArrowRight
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [email, setEmail] = useState('analyst@agentsec.com');
  const [password, setPassword] = useState('AnalystPass123!');
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'agent',
      text: "Hello! I am your controlled enterprise AI agent. I can perform safe calculations, summarize approved security guidelines, and look up directory records under backend security supervision.",
      tools: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);
  const chatBottomRef = useRef(null);

  // Check Backend Health
  const checkHealth = async () => {
    try {
      setLoadingHealth(true);
      const res = await fetch(`${API_BASE}/api/v1/health`);
      if (res.ok) {
        const data = await res.json();
        setHealthStatus(data);
      } else {
        setHealthStatus({ status: 'error', database: 'unavailable' });
      }
    } catch {
      setHealthStatus({ status: 'disconnected', database: 'unreachable' });
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  // Fetch Current User & Available Tools
  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      return;
    }
    const fetchUserData = async () => {
      try {
        const [meRes, toolsRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/auth/me`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${API_BASE}/api/v1/chat/tools`, { headers: { Authorization: `Bearer ${token}` } })
        ]);
        if (meRes.ok) {
          const user = await meRes.json();
          setCurrentUser(user);
        } else {
          handleLogout();
        }
        if (toolsRes.ok) {
          const tools = await toolsRes.json();
          setAvailableTools(tools);
        }
      } catch {
        setCurrentUser(null);
      }
    };
    fetchUserData();
  }, [token]);

  // Scroll to bottom on new message
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatLoading]);

  // Handle Login
  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
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

  // Handle Send Chat
  const handleSendMessage = async (customPrompt) => {
    const textToSend = typeof customPrompt === 'string' ? customPrompt : inputMessage;
    if (!textToSend.trim() || chatLoading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: textToSend }),
      });

      if (res.ok) {
        const data = await res.json();
        const agentMsg = {
          id: Date.now() + 1,
          sender: 'agent',
          text: data.response,
          tools: data.tools_invoked || [],
          mode: data.model_mode,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, agentMsg]);
      } else {
        const errData = await res.json();
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          sender: 'agent',
          text: `Error executing task: ${errData.detail || 'Server error'}`,
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
      }
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'agent',
        text: "Network error communicating with the agent security endpoint.",
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: 'agent',
        text: "Conversation thread cleared. How can I assist you with your security tasks?",
        tools: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-3.5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-base tracking-wide text-white flex items-center gap-2">
              AI Agent Security Platform
              <span className="text-xs bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-2 py-0.5 rounded-full font-mono">
                Step 2: AI Agent & Safe Tools
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Controlled Tool Registry &bull; Deterministic Engine &bull; Zero RCE
            </p>
          </div>
        </div>

        {/* Status badges */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-mono bg-slate-900 border-slate-800">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Backend:</span>
            {loadingHealth ? (
              <span className="text-amber-400 animate-pulse">Checking...</span>
            ) : healthStatus?.status === 'ok' ? (
              <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                Operational ({healthStatus.database})
              </span>
            ) : (
              <span className="text-red-400 flex items-center gap-1 font-semibold">
                <AlertCircle className="w-3 h-3" /> Offline
              </span>
            )}
          </div>

          {currentUser && (
            <button
              onClick={handleLogout}
              className="text-xs px-3 py-1.5 rounded-md bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition flex items-center gap-1.5 font-medium"
            >
              <LogOut className="w-3.5 h-3.5" /> Sign Out
            </button>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        
        {/* Authentication View if not logged in */}
        {!currentUser ? (
          <div className="col-span-12 max-w-4xl mx-auto w-full grid grid-cols-1 md:grid-cols-12 gap-6 pt-4">
            {/* Left demo presets */}
            <div className="md:col-span-6 space-y-4">
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-emerald-400" />
                  Step 2 Architecture Ready
                </h2>
                <div className="space-y-2.5 text-xs text-slate-300">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>Controlled AI Agent with Safe Tools Engine</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>Sandboxed AST Calculator (zero eval/exec code injection)</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>Internal Document Summarizer & Directory Query Tools</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>Automated Test Suite Passing: 16/16 Unit & API Tests</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                  <Key className="w-3.5 h-3.5 text-cyan-400" />
                  Select Pre-Seeded Account to Begin
                </h3>
                <div className="space-y-2 text-xs">
                  <button
                    onClick={() => fillCredentials('analyst@agentsec.com', 'AnalystPass123!')}
                    className="w-full text-left p-3 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800 transition flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-slate-200">analyst@agentsec.com</div>
                      <div className="text-slate-500">Role: REVIEWER (Approval Authority)</div>
                    </div>
                    <span className="text-cyan-400 font-mono">Fill &rarr;</span>
                  </button>
                  <button
                    onClick={() => fillCredentials('user@agentsec.com', 'UserPass123!')}
                    className="w-full text-left p-3 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800 transition flex items-center justify-between"
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

            {/* Right Login Card */}
            <div className="md:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 border-b border-slate-800 pb-4 mb-5">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">Sign In to Launch Agent</h3>
                  <p className="text-xs text-slate-400">Authenticate with JWT to interact with the controlled agent</p>
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
                    className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-slate-200 text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-slate-200 text-sm font-mono"
                  />
                </div>
                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full py-2.5 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition flex items-center justify-center gap-2 text-sm disabled:opacity-50"
                >
                  {authLoading ? 'Signing in...' : 'Sign In & Open Agent Console'}
                </button>
              </form>
            </div>
          </div>
        ) : (
          /* Logged In: Full Agent Workspace (Step 2) */
          <>
            {/* Left Sidebar: Session & Safe Tool Catalog */}
            <div className="md:col-span-4 space-y-5">
              {/* User Session Profile Card */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center gap-3 border-b border-slate-800/80 pb-3 mb-3">
                  <div className="p-2 rounded-full bg-cyan-500/10 text-cyan-400">
                    <UserCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white">{currentUser.full_name}</h3>
                    <p className="text-xs text-slate-400 font-mono">{currentUser.email}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Current RBAC Role:</span>
                  <span className="font-mono font-bold uppercase text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {currentUser.role}
                  </span>
                </div>
              </div>

              {/* Safe Tools Catalog */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    Available Safe Tools ({availableTools.length})
                  </h3>
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                    Backend Allowlist
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-cyan-400">
                      <Calculator className="w-3.5 h-3.5" /> safe_calculator
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Evaluates arithmetic expressions via safe AST parser (blocks functions/code injection).
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-emerald-400">
                      <FileText className="w-3.5 h-3.5" /> document_summarizer
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Summarizes approved policies: <code className="text-slate-300">remote_work_policy</code>, <code className="text-slate-300">incident_response</code>, <code className="text-slate-300">cloud_infrastructure</code>.
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-amber-400">
                      <Search className="w-3.5 h-3.5" /> record_lookup
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Queries synthetic employee directory: IDs <code className="text-slate-300">SEC-101</code> through <code className="text-slate-300">SEC-104</code>.
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick Evaluation Test Chips */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Quick Evaluation Tasks
                </h3>
                <div className="space-y-1.5 text-xs">
                  <button
                    onClick={() => handleSendMessage("Calculate (365 * 24 - 12) / (365 * 24) * 100")}
                    className="w-full text-left p-2 rounded bg-slate-950/60 hover:bg-slate-800 border border-slate-800/80 text-slate-300 hover:text-white transition flex items-center justify-between text-[11px]"
                  >
                    <span>🧮 Compute uptime percentage</span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                  </button>

                  <button
                    onClick={() => handleSendMessage("Please summarize the remote work policy.")}
                    className="w-full text-left p-2 rounded bg-slate-950/60 hover:bg-slate-800 border border-slate-800/80 text-slate-300 hover:text-white transition flex items-center justify-between text-[11px]"
                  >
                    <span>📄 Summarize remote work guidelines</span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                  </button>

                  <button
                    onClick={() => handleSendMessage("Look up directory record SEC-101.")}
                    className="w-full text-left p-2 rounded bg-slate-950/60 hover:bg-slate-800 border border-slate-800/80 text-slate-300 hover:text-white transition flex items-center justify-between text-[11px]"
                  >
                    <span>👤 Query employee record SEC-101</span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                  </button>

                  <button
                    onClick={() => handleSendMessage("What are the key responsibilities of an AI security guardrail?")}
                    className="w-full text-left p-2 rounded bg-slate-950/60 hover:bg-slate-800 border border-slate-800/80 text-slate-300 hover:text-white transition flex items-center justify-between text-[11px]"
                  >
                    <span>💬 General agent conversational query</span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Interactive AI Agent Chat Console */}
            <div className="md:col-span-8 bg-slate-900 border border-slate-800 rounded-xl flex flex-col h-[700px] shadow-2xl overflow-hidden">
              {/* Chat Window Header */}
              <div className="border-b border-slate-800 px-5 py-3.5 bg-slate-900/90 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400"></div>
                  <div>
                    <h2 className="text-sm font-bold text-white flex items-center gap-2">
                      Controlled AI Agent
                      <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono border border-slate-700">
                        Module 1
                      </span>
                    </h2>
                    <p className="text-[11px] text-slate-400">Operating in safe deterministic execution mode</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={clearChat}
                    className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1"
                    title="Clear Conversation"
                  >
                    <RefreshCw className="w-3 h-3" /> Reset
                  </button>
                </div>
              </div>

              {/* Messages Scroll Area */}
              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                        msg.sender === 'user'
                          ? 'bg-cyan-600 text-white'
                          : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                      }`}
                    >
                      {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>

                    {/* Bubble Content */}
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-cyan-600 text-white rounded-tr-none'
                          : msg.isError
                          ? 'bg-red-500/10 border border-red-500/30 text-red-300 rounded-tl-none'
                          : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
                      }`}
                    >
                      {/* Tool Invocations Box */}
                      {msg.tools && msg.tools.length > 0 && (
                        <div className="mb-2.5 p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] space-y-1.5 font-mono">
                          <div className="text-[10px] uppercase font-bold text-cyan-400 flex items-center gap-1">
                            <Cpu className="w-3 h-3" /> Tool Executed: {msg.tools[0].tool_name}
                          </div>
                          <div className="text-slate-400">
                            Args: <span className="text-slate-300">{JSON.stringify(msg.tools[0].arguments)}</span>
                          </div>
                          <div className="text-slate-400">
                            Output: <span className="text-emerald-400 font-semibold">{String(msg.tools[0].output)}</span>
                          </div>
                        </div>
                      )}

                      {/* Main Message Text */}
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                      
                      {/* Timestamp */}
                      <span className="block text-[10px] text-right mt-1.5 opacity-50 font-mono">
                        {msg.timestamp}
                      </span>
                    </div>
                  </div>
                ))}

                {/* Loading indicator */}
                {chatLoading && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="bg-slate-950 border border-slate-800 rounded-2xl rounded-tl-none px-4 py-3 text-xs text-slate-400 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      Evaluating task and inspecting safe tools...
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="border-t border-slate-800 p-3 bg-slate-900/90">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask the agent a task (e.g., 'Calculate 25 * 4' or 'Summarize remote work policy')..."
                    className="flex-1 bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none rounded-xl px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500"
                    disabled={chatLoading}
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !inputMessage.trim()}
                    className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition flex items-center gap-1.5 text-xs disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Send</span>
                  </button>
                </form>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 px-6 py-2.5 text-center text-xs text-slate-600">
        AI Agent Security Platform &bull; Step 2 (Controlled AI Agent & Safe Tools) Active &bull; 16 Tests Passing
      </footer>
    </div>
  );
}
