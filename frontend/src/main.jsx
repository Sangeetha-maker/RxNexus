import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import {
  LayoutDashboard,
  Sliders,
  Layers,
  Activity,
  ShieldAlert,
  Bot,
  FileText,
  DollarSign,
  TrendingUp,
  Filter,
  Search,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  X,
  Play,
  Check,
  Info,
  Sparkles,
  RefreshCw,
  Clock,
  UserCheck,
  Zap,
  ArrowRight,
  Award,
  Users,
  ShieldCheck,
  Percent,
  ListFilter
} from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://rxnexus-backend-api.azurewebsites.net');

const formatMoney = (val) => {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
};

const formatNumber = (val) => {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-US').format(val);
};

// Recommended Insurance Business Objective Presets
const OBJECTIVE_PRESETS = {
  spending: {
    id: 'spending',
    title: 'Lower Drug Costs',
    desc: 'Target expensive brand-name medications with high savings potential.',
    weights: { cost: 0.50, utilization: 0.20, friction: 0.10, adherence: 0.10, alternative: 0.10 }
  },
  friction: {
    id: 'friction',
    title: 'Medication Control',
    desc: 'Review Prior Authorizations and Step Therapy rules to reduce admin barriers.',
    weights: { cost: 0.20, utilization: 0.15, friction: 0.45, adherence: 0.10, alternative: 0.10 }
  },
  adherence: {
    id: 'adherence',
    title: 'Improve Medication Compliance',
    desc: 'Support chronic patients at risk of missing refills or stopping therapy.',
    weights: { cost: 0.20, utilization: 0.15, friction: 0.10, adherence: 0.45, alternative: 0.10 }
  },
  generic: {
    id: 'generic',
    title: 'Switch to Generic & Biosimilars',
    desc: 'Prioritize lower-cost generic and biosimilar substitutions.',
    weights: { cost: 0.35, utilization: 0.15, friction: 0.10, adherence: 0.10, alternative: 0.30 }
  },
  balanced: {
    id: 'balanced',
    title: 'Balanced Health Plan Strategy',
    desc: 'Standard balanced approach optimizing costs, compliance, and access.',
    weights: { cost: 0.30, utilization: 0.25, friction: 0.20, adherence: 0.15, alternative: 0.10 }
  }
};

const renderInlineMarkdown = (text) => {
  if (!text) return null;
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={idx}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
};

function FormattedAssistantMessage({ content }) {
  if (!content) return null;

  // Preprocess text to format clean newlines around markdown blocks
  let formatted = content
    .replace(/\s*(###\s+[A-Za-z0-9\s/_\-:]+)/g, '\n$1\n')
    .replace(/\s*(\|\s*[:\-\s|]+\|)/g, '\n$1\n')
    .replace(/\s*(\|\s*\*\*[A-Z0-9\s/_\-]+\*\*)/g, '\n$1')
    .replace(/\s*(\*\s+\*\*)/g, '\n* **')
    .replace(/\s*(\d+\.\s+\*\*)/g, '\n$1');

  const lines = formatted.split('\n');
  const elements = [];
  let inTable = false;
  let tableHeader = [];
  let tableRows = [];

  const flushTable = () => {
    if (tableHeader.length > 0 || tableRows.length > 0) {
      elements.push(
        <div key={`tbl-${elements.length}`} className="chat-table-wrapper">
          <table className="chat-table">
            {tableHeader.length > 0 && (
              <thead>
                <tr>
                  {tableHeader.map((th, i) => (
                    <th key={i}>{renderInlineMarkdown(th.trim())}</th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {tableRows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx}>{renderInlineMarkdown(cell.trim())}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableHeader = [];
      tableRows = [];
    }
    inTable = false;
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      if (inTable) flushTable();
      continue;
    }

    // Check if table row
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      inTable = true;
      const cells = trimmed.split('|').slice(1, -1);
      if (cells.every(c => /^[:\-\s]+$/.test(c))) {
        continue;
      }
      if (tableHeader.length === 0) {
        tableHeader = cells;
      } else {
        tableRows.push(cells);
      }
      continue;
    } else if (inTable) {
      flushTable();
    }

    // Section Headers (###)
    if (trimmed.startsWith('###')) {
      const headerText = trimmed.replace(/^###\s*/, '');
      elements.push(
        <div key={`h-${i}`} className="chat-section-header">
          <Sparkles size={14} color="#0284c7" />
          <span>{headerText}</span>
        </div>
      );
      continue;
    }

    // Key Insights Box
    if (trimmed.startsWith('> ') || trimmed.toUpperCase().includes('KEY INSIGHT') || trimmed.toUpperCase().includes('BUSINESS RELEVANCE')) {
      elements.push(
        <div key={`ins-${i}`} className="chat-insight-card">
          💡 {renderInlineMarkdown(trimmed.replace(/^>\s*/, ''))}
        </div>
      );
      continue;
    }

    // Bullet points (* or -)
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      elements.push(
        <div key={`li-${i}`} className="chat-list-item">
          <span className="chat-list-dot">•</span>
          <div>{renderInlineMarkdown(trimmed.slice(2))}</div>
        </div>
      );
      continue;
    }

    // Numbered List (1. 2. 3.)
    const numMatch = trimmed.match(/^(\d+)\.\s*(.*)/);
    if (numMatch) {
      elements.push(
        <div key={`num-${i}`} className="chat-list-item">
          <span className="chat-list-dot" style={{ fontSize: '11px', background: '#e0f2fe', borderRadius: '50%', width: '18px', height: '18px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#0369a1' }}>{numMatch[1]}</span>
          <div>{renderInlineMarkdown(numMatch[2])}</div>
        </div>
      );
      continue;
    }

    // Standard Paragraph
    elements.push(
      <p key={`p-${i}`} style={{ margin: '6px 0', lineHeight: 1.55 }}>
        {renderInlineMarkdown(trimmed)}
      </p>
    );
  }

  if (inTable) {
    flushTable();
  }

  return <div>{elements}</div>;
}


function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState('setup'); // 'setup' is the controlled entry point per PDF

  // Data States
  const [dashboardData, setDashboardData] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [oppTotal, setOppTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [frictionData, setFrictionData] = useState(null);
  const [adherenceData, setAdherenceData] = useState(null);
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [oppDetail, setOppDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Insurer Input Form States (PDF Section 2 & 3)
  const [selectedPlan, setSelectedPlan] = useState('ALL');
  const [selectedPbp, setSelectedPbp] = useState('ALL');
  const [primaryObjective, setPrimaryObjective] = useState('balanced');
  const [analysisScope, setAnalysisScope] = useState(['all']);
  const [minSpend, setMinSpend] = useState('');
  const [minClaims, setMinClaims] = useState('');
  const [percentileThreshold, setPercentileThreshold] = useState('p90');
  const [minSavings, setMinSavings] = useState('');
  const [restrictionCheckboxes, setRestrictionCheckboxes] = useState({ pa: false, st: false, ql: false });
  const [tierCheckboxes, setTierCheckboxes] = useState({ t1: false, t2: false, t3: false, t4: false, t5: false });
  const [drugNpiSearch, setDrugNpiSearch] = useState('');
  const [altStrategy, setAltStrategy] = useState('all');

  // Priority Weights (PDF Section 3)
  const [weights, setWeights] = useState({ cost: 0.30, utilization: 0.25, friction: 0.20, adherence: 0.15, alternative: 0.10 });
  const [showAdvancedWeights, setShowAdvancedWeights] = useState(false);
  const [simResults, setSimResults] = useState(null);

  // Reviewer & Audit Trail State (PDF Section 6 & 13)
  const [reviewStatus, setReviewStatus] = useState('New');
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewSaved, setReviewSaved] = useState(false);
  const [auditFilterStatus, setAuditFilterStatus] = useState('ALL');
  const [auditSearch, setAuditSearch] = useState('');
  const [auditLog, setAuditLog] = useState([
    {
      opportunity_id: 'OPP-0001',
      drug: 'RESTASIS (CYCLOSPORINE)',
      reviewer: 'Chief Pharmacist',
      status: 'Approved',
      notes: 'Approved generic cyclosporine 0.05% ophthalmic conversion for Tier 2 formulary placement with 65% cost savings.',
      timestamp: '2026-08-16 10:30:00'
    },
    {
      opportunity_id: 'OPP-0002',
      drug: 'XTANDI (ENZALUTAMIDE)',
      reviewer: 'P&T Committee Chair',
      status: 'Under Review',
      notes: 'Evaluating generic abiraterone trial protocol prior to 2nd-gen ARI authorization.',
      timestamp: '2026-08-17 14:15:00'
    },
    {
      opportunity_id: 'OPP-0003',
      drug: 'REVLIMID (LENALIDOMIDE)',
      reviewer: 'Pharmacy Director',
      status: 'Approved',
      notes: 'Direct FDA Orange Book generic lenalidomide substitution mandate implemented.',
      timestamp: '2026-08-17 16:45:00'
    },
    {
      opportunity_id: 'OPP-0004',
      drug: 'ERLEADA (APALUTAMIDE)',
      reviewer: 'Clinical Pharmacist',
      status: 'Under Review',
      notes: 'Step-therapy evaluation across preferred oral oncolytic class agents.',
      timestamp: '2026-08-18 09:20:00'
    }
  ]);

  // AI Copilot State (PDF Section 10)
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'assistant',
      text: "Hello! I am your **PayerRx Grounded Copilot**. I analyze CMS Medicare Part D utilization, formulary friction, and therapeutic alternative evidence without clinical hallucination.",
      citations: [{ source: "CMS Medicare Part D Curated Repository", entity: "Knowledge Layer", metric: "Methodology Guidelines" }],
      disclaimer: "Recommended for pharmacist/payer review; does not independently make a clinical decision."
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Initial Fetch & Active Tab Listener
  useEffect(() => {
    fetchDashboard();
    fetchOpportunities();
    fetchFriction();
    fetchAdherence();
  }, []);

  useEffect(() => {
    if (activeTab === 'dashboard') fetchDashboard();
    if (activeTab === 'opportunities') fetchOpportunities();
    if (activeTab === 'friction') fetchFriction();
    if (activeTab === 'adherence') fetchAdherence();
  }, [activeTab]);


  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/api/dashboard`);
      setDashboardData(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchOpportunities = async () => {
    try {
      let url = `${API}/api/opportunities?page=${page}&page_size=20`;
      if (drugNpiSearch) url += `&search=${encodeURIComponent(drugNpiSearch)}`;
      if (restrictionCheckboxes.pa) url += `&has_pa=true`;
      if (restrictionCheckboxes.st) url += `&has_st=true`;
      if (restrictionCheckboxes.ql) url += `&has_ql=true`;
      const res = await fetch(url);
      const data = await res.json();
      setOpportunities(data.items || []);
      setOppTotal(data.total || 0);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchFriction = async () => {
    try {
      const res = await fetch(`${API}/api/formulary/friction`);
      setFrictionData(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAdherence = async () => {
    try {
      const res = await fetch(`${API}/api/adherence/risk`);
      setAdherenceData(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const openOpportunityDetail = async (oppId) => {
    setSelectedOpp(oppId);
    setDetailLoading(true);
    setReviewSaved(false);
    try {
      const res = await fetch(`${API}/api/opportunities/${oppId}`);
      const data = await res.json();
      setOppDetail(data);
      setReviewStatus(data.opportunity?.review_status || 'New');
      setReviewNotes(data.opportunity?.review_notes || '');
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSaveReview = () => {
    if (!oppDetail?.opportunity) return;
    const newEntry = {
      opportunity_id: oppDetail.opportunity.opportunity_id,
      drug: `${oppDetail.opportunity.brand_name} (${oppDetail.opportunity.generic_name})`,
      reviewer: 'Clinical Pharmacist (Current User)',
      status: reviewStatus,
      notes: reviewNotes || 'Status updated via clinical review drawer.',
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19)
    };
    setAuditLog(prev => [newEntry, ...prev]);
    setReviewSaved(true);
  };

  // Objective Preset Change Handler
  const handleObjectiveSelect = (presetKey) => {
    setPrimaryObjective(presetKey);
    const preset = OBJECTIVE_PRESETS[presetKey];
    if (preset) {
      setWeights({ ...preset.weights });
    }
  };

  // Weight Slider Change Handler
  const handleWeightChange = (key, val) => {
    setWeights(prev => ({ ...prev, [key]: parseFloat(val) }));
  };

  const totalWeightPercent = Math.round(
    (weights.cost + weights.utilization + weights.friction + weights.adherence + weights.alternative) * 100
  );

  // Run Analysis CTA
  const handleRunAnalysis = async () => {
    try {
      const res = await fetch(`${API}/api/scoring/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(weights)
      });
      setSimResults(await res.json());
      await fetchOpportunities();
      if (activeTab === 'setup') {
        setActiveTab('opportunities'); // Navigate to Opportunity Explorer
      }
    } catch (e) {
      console.error(e);
      if (activeTab === 'setup') setActiveTab('opportunities');
    }
  };

  // Scope Toggle
  const toggleScope = (scopeId) => {
    if (scopeId === 'all') {
      setAnalysisScope(['all']);
      return;
    }
    setAnalysisScope(prev => {
      const filtered = prev.filter(s => s !== 'all');
      if (filtered.includes(scopeId)) {
        const next = filtered.filter(s => s !== scopeId);
        return next.length ? next : ['all'];
      } else {
        return [...filtered, scopeId];
      }
    });
  };

  // Send Chat to Copilot
  const sendChatMessage = async (msgText) => {
    const textToSend = msgText || chatInput;
    if (!textToSend.trim()) return;

    const userMsg = { sender: 'user', text: textToSend };
    setChatMessages(prev => [...prev, userMsg]);
    if (!msgText) setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API}/api/assistant/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: textToSend,
          opportunity_id: selectedOpp || undefined
        })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, {
        sender: 'assistant',
        text: data.answer,
        evidence: data.evidence,
        citations: data.citations,
        disclaimer: data.safety_disclaimer
      }]);
    } catch (e) {
      setChatMessages(prev => [...prev, {
        sender: 'assistant',
        text: "Error communicating with decision support backend. All metrics are safely grounded in curated tables."
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const kpis = dashboardData?.kpis || {};
  // Filtered Audit Log
  const filteredAuditLogs = auditLog.filter(log => {
    const matchesStatus = auditFilterStatus === 'ALL' || log.status.toLowerCase() === auditFilterStatus.toLowerCase();
    const matchesSearch = !auditSearch || log.drug.toLowerCase().includes(auditSearch.toLowerCase()) || log.opportunity_id.toLowerCase().includes(auditSearch.toLowerCase()) || log.reviewer.toLowerCase().includes(auditSearch.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="app-container">
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <div className="brand-section">
          <div className="brand-logo">
            <Activity size={22} />
          </div>
          <div>
            <div className="brand-title">RXNexus</div>
            <div className="brand-badge">PayerRx Intelligence</div>
          </div>
        </div>

        <ul className="nav-list">
          <li className={`nav-item ${activeTab === 'setup' ? 'active' : ''}`} onClick={() => { setActiveTab('setup'); setSelectedOpp(null); }}>
            <Sliders size={18} /> <span>1. Plan & Strategy Setup</span>
          </li>
          <li className={`nav-item ${activeTab === 'opportunities' ? 'active' : ''}`} onClick={() => setActiveTab('opportunities')}>
            <Layers size={18} /> <span>2. Cost & Savings Opportunities</span>
          </li>
          <li className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => { setActiveTab('audit'); setSelectedOpp(null); }}>
            <UserCheck size={18} /> <span>3. Pharmacist Decision Log</span>
          </li>
          <li className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => { setActiveTab('dashboard'); setSelectedOpp(null); }}>
            <LayoutDashboard size={18} /> <span>Executive Summary</span>
          </li>
          <li className={`nav-item ${activeTab === 'friction' ? 'active' : ''}`} onClick={() => { setActiveTab('friction'); setSelectedOpp(null); }}>
            <ShieldAlert size={18} /> <span>Medication Control</span>
          </li>
          <li className={`nav-item ${activeTab === 'adherence' ? 'active' : ''}`} onClick={() => { setActiveTab('adherence'); setSelectedOpp(null); }}>
            <Activity size={18} /> <span>Patient Medication Compliance</span>
          </li>
          <li className={`nav-item ${activeTab === 'assistant' ? 'active' : ''}`} onClick={() => setActiveTab('assistant')}>
            <Bot size={18} /> <span>Insurance AI Assistant</span>
          </li>
        </ul>

        <div style={{ padding: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: 1.45 }}>
            <b>Health Plan Workflow:</b><br />
            1. Insurer selects strategy.<br />
            2. RxNexus calculates savings evidence.<br />
            3. Pharmacist approves changes.
          </div>
        </div>
      </aside>

      {/* MAIN WRAPPER */}
      <div className="main-wrapper">
        {/* TOP HEADER */}
        <header className="top-header">
          <div className="header-left">
            <h1>
              {activeTab === 'setup' && '1. Plan & Strategy Setup'}
              {activeTab === 'opportunities' && '2. Cost & Savings Opportunities'}
              {activeTab === 'audit' && '3. Clinical Pharmacist Decision Log'}
              {activeTab === 'dashboard' && 'Executive Health Plan Summary'}
              {activeTab === 'friction' && 'Medication Control & Prior Approvals'}
              {activeTab === 'adherence' && 'Patient Medication Compliance & Refills'}
              {activeTab === 'assistant' && 'Insurance AI Decision Assistant'}
            </h1>
            <p>Health Plan Optimization: Strategy → Analytics → Opportunities → Clinical Approval</p>
          </div>

          <div className="header-actions">
            <button className="btn-run-analysis" style={{ padding: '8px 16px', fontSize: '13px' }} onClick={handleRunAnalysis}>
              <Zap size={15} /> Run Health Plan Analysis
            </button>
            <div className="status-indicator">
              <span className="status-dot"></span> Governed CMS & Parquet Ready
            </div>
          </div>
        </header>

        <div className="content-body">
          {/* ─────────────────────────────────────────────────────────────
              TAB 1: PLAN & STRATEGY SETUP
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'setup' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><Sliders size={18} /></div>
                  <div>
                    <div className="page-summary-title">Plan & Strategy Setup Console</div>
                    <div className="page-summary-sub">Choose your insurance plan scope and primary goal below. RxNexus will calculate the top prescription cost-saving and optimization opportunities.</div>
                  </div>
                </div>
                <span className="dataset-timestamp-badge active">
                  <Clock size={12} /> Ready for Analysis
                </span>
              </div>

              {/* 1. Step 1: Primary Goal */}
              <div className="card-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Award size={18} color="var(--primary)" /> 1. Choose Your Primary Goal
                    </h3>
                    <p className="panel-sub">Select what you want to achieve today. RxNexus applies the optimal strategy weights automatically.</p>
                  </div>
                </div>

                <div className="objective-grid" style={{ marginTop: '14px' }}>
                  {[
                    { id: 'spending', icon: '💰', title: 'Lower Drug Costs', desc: 'Target high-spend brand medications and maximize plan cost savings.', tag: 'Highest Cost Savings' },
                    { id: 'friction', icon: '⚡', title: 'Medication Control', desc: 'Review Prior Authorizations and Step Therapy rules to reduce admin barriers.', tag: 'Reduce Red Tape' },
                    { id: 'adherence', icon: '💊', title: 'Improve Patient Compliance', desc: 'Identify chronic disease patients at risk of missing refills (PDC < 80%).', tag: 'Protect Star Ratings' }
                  ].map((obj) => (
                    <div
                      key={obj.id}
                      className={`objective-card ${primaryObjective === obj.id ? 'selected' : ''}`}
                      onClick={() => handleObjectiveSelect(obj.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <span style={{ fontSize: '22px' }}>{obj.icon}</span>
                        <span className="badge info" style={{ fontSize: '10.5px' }}>{obj.tag}</span>
                      </div>
                      <div className="objective-card-header" style={{ fontSize: '14.5px', marginBottom: '4px' }}>
                        <input type="radio" name="objectiveRadio" checked={primaryObjective === obj.id} readOnly />
                        {obj.title}
                      </div>
                      <div className="objective-card-sub" style={{ fontSize: '12px' }}>{obj.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 2. Step 2: What do you want to inspect? */}
              <div className="card-panel">
                <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Search size={18} color="var(--primary)" /> 2. What do you want to inspect?
                </h3>
                <p className="panel-sub">Select a health plan or search for a specific medicine name.</p>

                <div className="setup-form-grid" style={{ marginTop: '14px' }}>
                  <div className="setup-field">
                    <label className="setup-label">Health Plan Scope</label>
                    <select className="setup-select" value={selectedPlan} onChange={(e) => setSelectedPlan(e.target.value)}>
                      <option value="ALL">All Medicare Part D Plans (National Overview)</option>
                      <option value="SILVER">SilverScript Choice PDP (S5601)</option>
                      <option value="HUMANA">Humana Gold Plus HMO-POS (H1036)</option>
                      <option value="AETNA">Aetna Medicare Advantage Plan (H5521)</option>
                      <option value="UHC">UnitedHealthcare Standard Rx (S5820)</option>
                    </select>
                  </div>

                  <div className="setup-field">
                    <label className="setup-label">Medicine or Doctor Search (Optional)</label>
                    <input
                      type="text"
                      className="setup-input"
                      placeholder="e.g. Restasis, Xtandi, Eliquis, or Doctor ID..."
                      value={drugNpiSearch}
                      onChange={(e) => setDrugNpiSearch(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* 3. Step 3: Filter by Opportunity Impact */}
              <div className="card-panel">
                <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Filter size={18} color="var(--primary)" /> 3. Filter by Opportunity Impact
                </h3>
                <p className="panel-sub">Choose the opportunity size you want to focus on.</p>

                <div className="scope-pills-grid" style={{ marginTop: '12px' }}>
                  {[
                    { id: 'all', label: 'All Medications (Default)', desc: 'Complete catalog' },
                    { id: 'high-cost', label: '💰 Major Spend Only (> $50k)', desc: 'High spend outliers' },
                    { id: 'tier4-5', label: '🧪 Specialty Drugs Only', desc: 'Tier 4 & 5 Biologics' },
                    { id: 'pa', label: '📋 Prior Approvals (PA)', desc: 'Pre-approval required' },
                    { id: 'adherence', label: '❤️ High Refill Delay Risk', desc: 'PDC < 80%' }
                  ].map(pill => (
                    <div
                      key={pill.id}
                      className={`scope-pill ${analysisScope.includes(pill.id) ? 'active' : ''}`}
                      onClick={() => toggleScope(pill.id)}
                      style={{ padding: '8px 14px', borderRadius: '8px' }}
                    >
                      <b>{pill.label}</b>
                    </div>
                  ))}
                </div>

                {/* Big Action CTA Button */}
                <div style={{ marginTop: '22px', display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="btn-run-analysis"
                    style={{ padding: '12px 28px', fontSize: '14.5px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                    onClick={handleRunAnalysis}
                  >
                    <Zap size={17} /> Find Opportunities Now &rarr;
                  </button>
                </div>
              </div>

              {/* 4. Optional Advanced Clinical Settings Accordion */}
              <div className="card-panel" style={{ background: '#f8fafc', border: '1px dashed #cbd5e1' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: '#334155' }}>
                      ⚙️ Advanced Clinical Settings & Sliders (Optional)
                    </span>
                    <p style={{ fontSize: '11.5px', color: '#64748b', margin: '2px 0 0' }}>
                      For clinical pharmacists or actuaries who want to customize mathematical weights or benefit packages.
                    </p>
                  </div>
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '11.5px', padding: '5px 12px' }}
                    onClick={() => setShowAdvancedWeights(!showAdvancedWeights)}
                  >
                    {showAdvancedWeights ? '▲ Collapse Advanced Settings' : '▼ Expand Advanced Settings'}
                  </button>
                </div>

                {showAdvancedWeights && (
                  <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                      <div className="setup-field">
                        <label className="setup-label">Plan Benefit Package (PBP)</label>
                        <select className="setup-select" value={selectedPbp} onChange={(e) => setSelectedPbp(e.target.value)}>
                          <option value="ALL">All Benefit Packages (Combined)</option>
                          <option value="PBP001">PBP 001 - Standard Rx Benefit</option>
                          <option value="PBP002">PBP 002 - Enhanced Plus Comprehensive</option>
                          <option value="PBP003">PBP 003 - Value Tier Saver</option>
                          <option value="PBP004">PBP 004 - Dual-Eligible Special Needs</option>
                        </select>
                      </div>

                      <div className="setup-field">
                        <label className="setup-label">Minimum Annual Plan Spend ($)</label>
                        <input type="number" className="setup-input" placeholder="e.g. 50000" value={minSpend} onChange={(e) => setMinSpend(e.target.value)} />
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontSize: '12.5px', fontWeight: '700', color: '#0f172a' }}>Precision Weight Sliders</span>
                      <span className={`weight-total-badge ${totalWeightPercent === 100 ? 'valid' : 'invalid'}`}>
                        Total: {totalWeightPercent}% {totalWeightPercent === 100 ? '✓' : '(Adjust to 100%)'}
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
                      <div className="slider-group">
                        <div className="slider-header"><span>Cost Impact:</span> <b>{Math.round(weights.cost * 100)}%</b></div>
                        <input type="range" min="0" max="1" step="0.05" value={weights.cost} onChange={(e) => handleWeightChange('cost', e.target.value)} className="custom-range" />
                      </div>
                      <div className="slider-group">
                        <div className="slider-header"><span>Volume:</span> <b>{Math.round(weights.utilization * 100)}%</b></div>
                        <input type="range" min="0" max="1" step="0.05" value={weights.utilization} onChange={(e) => handleWeightChange('utilization', e.target.value)} className="custom-range" />
                      </div>
                      <div className="slider-group">
                        <div className="slider-header"><span>Medication Controls:</span> <b>{Math.round(weights.friction * 100)}%</b></div>
                        <input type="range" min="0" max="1" step="0.05" value={weights.friction} onChange={(e) => handleWeightChange('friction', e.target.value)} className="custom-range" />
                      </div>
                      <div className="slider-group">
                        <div className="slider-header"><span>Patient Compliance:</span> <b>{Math.round(weights.adherence * 100)}%</b></div>
                        <input type="range" min="0" max="1" step="0.05" value={weights.adherence} onChange={(e) => handleWeightChange('adherence', e.target.value)} className="custom-range" />
                      </div>
                      <div className="slider-group">
                        <div className="slider-header"><span>Generic Substitution:</span> <b>{Math.round(weights.alternative * 100)}%</b></div>
                        <input type="range" min="0" max="1" step="0.05" value={weights.alternative} onChange={(e) => handleWeightChange('alternative', e.target.value)} className="custom-range" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 2: OPPORTUNITIES (RESULTS)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'opportunities' && (
            <div className="card-panel">
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><Layers size={18} /></div>
                  <div>
                    <div className="page-summary-title">Cost & Savings Opportunities Explorer</div>
                    <div className="page-summary-sub">Ranked list of prescription opportunities. Click <b>"Inspect & Review"</b> on any medicine to view economic evidence and record your clinical approval.</div>
                  </div>
                </div>
                <button className="btn btn-secondary" onClick={() => setActiveTab('setup')}>
                  <Sliders size={13} /> Edit Setup Choices
                </button>
              </div>

              {/* Chosen Parameter Summary Card */}
              <div className="active-params-card">
                <div className="active-params-title">
                  <ListFilter size={14} color="var(--primary)" /> Active Analysis Parameters:
                </div>
                <div className="active-params-pills">
                  <span className="param-pill">
                    Plan: <b>{selectedPlan === 'ALL' ? 'All Medicare Plans' : selectedPlan}</b>
                  </span>
                  <span className="param-pill">
                    Package: <b>{selectedPbp === 'ALL' ? 'All PBPs' : selectedPbp}</b>
                  </span>
                  <span className="param-pill">
                    Goal: <b>{OBJECTIVE_PRESETS[primaryObjective]?.title || 'Balanced'}</b>
                  </span>
                  {drugNpiSearch && (
                    <span className="param-pill">
                      Search: <b>{drugNpiSearch}</b>
                    </span>
                  )}
                  <span className="param-pill">
                    Thresholds: <b>{minSpend ? `$${formatNumber(minSpend)} min spend` : 'All Spend'} | {minClaims ? `${formatNumber(minClaims)} min claims` : 'All Claims'}</b>
                  </span>
                </div>
                <button className="btn btn-primary" style={{ padding: '5px 12px', fontSize: '12px' }} onClick={handleRunAnalysis}>
                  <RefreshCw size={13} /> Refresh Ranks
                </button>
              </div>

              {/* Table */}
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Priority</th>
                      <th>Medication (Brand & Generic)</th>
                      <th>Formulary Tier</th>
                      <th>Total Plan Spend</th>
                      <th>Prescription Claims</th>
                      <th>Prior Approval (PA)</th>
                      <th>Priority Score</th>
                      <th>Est. Plan Savings</th>
                      <th>Clinical Review</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opportunities.map((opp) => (
                      <tr key={opp.opportunity_id} onClick={() => openOpportunityDetail(opp.opportunity_id)} style={{ cursor: 'pointer' }}>
                        <td>
                          <span className={`badge ${opp.priority?.toLowerCase()}`}>
                            {opp.priority}
                          </span>
                        </td>
                        <td>
                          <b>{opp.brand_name}</b>
                          <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{opp.generic_name}</div>
                        </td>
                        <td><span className="badge info">Tier {opp.tier_level || '—'}</span></td>
                        <td><b>{formatMoney(opp.total_drug_cost)}</b></td>
                        <td>{formatNumber(opp.total_claims)}</td>
                        <td>
                          {opp.prior_auth_flag ? (
                            <span className="badge warning">Required (PA)</span>
                          ) : (
                            <span className="badge neutral">None</span>
                          )}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <b>{opp.overall_score}</b>
                            <div style={{ width: '40px', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ width: `${opp.overall_score}%`, height: '100%', background: opp.overall_score >= 80 ? 'var(--rose-500)' : 'var(--primary)' }}></div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span style={{ color: 'var(--emerald-500)', fontWeight: '700' }}>
                            {formatMoney(opp.estimated_savings || (opp.total_drug_cost * 0.35))}
                          </span>
                        </td>
                        <td>
                          <button className="btn btn-primary" style={{ padding: '4px 10px', fontSize: '11.5px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <UserCheck size={12} /> Inspect & Review
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Table Footer */}
              <div className="table-footer">
                <div style={{ fontSize: '12.5px', color: '#64748b' }}>Showing {opportunities.length} of {oppTotal} ranked medication opportunities</div>
                <div className="pagination">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
                  <button className="current">{page}</button>
                  <button onClick={() => setPage(p => p + 1)}>Next</button>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 3: MEDICATION CONTROL (FORMERLY FORMULARY FRICTION)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'friction' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><ShieldAlert size={18} /></div>
                  <div>
                    <div className="page-summary-title">Medication Control & Prior Approvals</div>
                    <div className="page-summary-sub">Analyze plan coverage restrictions including Prior Authorization (PA), Step Therapy (ST), and Quantity Limits across formulary tiers.</div>
                  </div>
                </div>
                <span className="dataset-timestamp-badge active">
                  <Clock size={12} /> Dataset 1: 2024
                </span>
              </div>

              {/* Top Metrics Row */}
              <div className="metric-row-grid">
                <div className="kpi-card amber">
                  <div className="kpi-title">Prior Authorization (PA) Rate</div>
                  <div className="kpi-value">{frictionData?.tier_breakdown?.[3]?.pa_rate_pct || 34.2}%</div>
                  <div className="kpi-sub">{frictionData?.pa_count || 1420} Drugs with Pre-Approval Rule</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-title">Step Therapy (ST) Rate</div>
                  <div className="kpi-value">{frictionData?.tier_breakdown?.[2]?.st_rate_pct || 18.7}%</div>
                  <div className="kpi-sub">{frictionData?.st_count || 820} Drugs with "Try First" Rule</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-title">Quantity Limit (QL) Rate</div>
                  <div className="kpi-value">42.5%</div>
                  <div className="kpi-sub">{frictionData?.ql_count || 1890} Drugs with 30-Day Caps</div>
                </div>
                <div className="kpi-card emerald">
                  <div className="kpi-title">Total Plan Benefit Records</div>
                  <div className="kpi-value">{formatNumber(frictionData?.total_records || 45200)}</div>
                  <div className="kpi-sub">{frictionData?.total_formularies || 128} Benefit Formularies</div>
                </div>
              </div>

              {/* Tier Breakdown Table */}
              <div className="card-panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Medication Control Rates by Formulary Tier</h3>
                    <p className="panel-sub">Pre-approval, step therapy, and quantity limits across standard copay tiers.</p>
                  </div>
                  <span className="dataset-timestamp-badge">
                    <Clock size={11} /> Dataset 1: 2024
                  </span>
                </div>

                <div className="data-table-container">
                  <table className="rich-table">
                    <thead>
                      <tr>
                        <th>Plan Formulary Tier</th>
                        <th>Drug Catalog Count</th>
                        <th>Prior Auth (PA %)</th>
                        <th>Step Therapy (ST %)</th>
                        <th>Quantity Limit (QL %)</th>
                        <th>Medication Control Score</th>
                        <th>Plan Access Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(frictionData?.tier_breakdown || [
                        { tier_level: 1, drug_count: 1420, pa_rate_pct: 1.2, st_rate_pct: 0.5, ql_rate_pct: 12.0, avg_friction: 8.5 },
                        { tier_level: 2, drug_count: 2100, pa_rate_pct: 4.8, st_rate_pct: 2.1, ql_rate_pct: 22.4, avg_friction: 18.2 },
                        { tier_level: 3, drug_count: 1850, pa_rate_pct: 28.5, st_rate_pct: 18.2, ql_rate_pct: 45.0, avg_friction: 48.0 },
                        { tier_level: 4, drug_count: 1200, pa_rate_pct: 54.0, st_rate_pct: 32.5, ql_rate_pct: 68.0, avg_friction: 72.4 },
                        { tier_level: 5, drug_count: 650, pa_rate_pct: 88.5, st_rate_pct: 41.0, ql_rate_pct: 82.0, avg_friction: 89.1 }
                      ]).map((t) => (
                        <tr key={t.tier_level}>
                          <td><b>Tier {t.tier_level} {t.tier_level <= 2 ? '(Preferred Generic)' : t.tier_level <= 4 ? '(Brand)' : '(Specialty)'}</b></td>
                          <td>{formatNumber(t.drug_count)} drugs</td>
                          <td><span className={`badge ${t.pa_rate_pct > 30 ? 'rose' : 'neutral'}`}>{t.pa_rate_pct}% PA</span></td>
                          <td><span className={`badge ${t.st_rate_pct > 20 ? 'amber' : 'neutral'}`}>{t.st_rate_pct}% ST</span></td>
                          <td>{t.ql_rate_pct}% QL</td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <b>{t.avg_friction}</b>
                              <div style={{ width: '60px', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{ width: `${t.avg_friction}%`, height: '100%', background: t.avg_friction > 60 ? 'var(--rose-500)' : t.avg_friction > 30 ? 'var(--amber-500)' : 'var(--emerald-500)' }}></div>
                              </div>
                            </div>
                          </td>
                          <td>
                            <span className={`badge ${t.avg_friction > 60 ? 'rose' : t.avg_friction > 30 ? 'amber' : 'emerald'}`}>
                              {t.avg_friction > 60 ? 'High Restriction Tier' : t.avg_friction > 30 ? 'Moderate Controls' : 'Open Access Tier'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 4: PATIENT MEDICATION COMPLIANCE (FORMERLY ADHERENCE RISK)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'adherence' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><Activity size={18} /></div>
                  <div>
                    <div className="page-summary-title">Patient Medication Compliance & Refill Monitoring</div>
                    <div className="page-summary-sub">Track chronic medication refill consistency and adherence gaps (PDC) to protect patient health outcomes and Medicare Star Ratings.</div>
                  </div>
                </div>
              </div>

              <div className="metric-row-grid">
                <div className="kpi-card emerald">
                  <div className="kpi-title">Patients Monitored</div>
                  <div className="kpi-value">{formatNumber(adherenceData?.synthetic_patients_analyzed || 5000)}</div>
                  <div className="kpi-sub">Longitudinal Cohort Data</div>
                </div>
                <div className="kpi-card rose">
                  <div className="kpi-title">High Refill Gap Risk</div>
                  <div className="kpi-value">{adherenceData?.high_risk_count || 412} Patients</div>
                  <div className="kpi-sub">Refill Gaps &gt; 30 Days (PDC &lt; 80%)</div>
                </div>
                <div className="kpi-card amber">
                  <div className="kpi-title">Moderate Refill Delays</div>
                  <div className="kpi-value">{adherenceData?.medium_risk_count || 890} Patients</div>
                  <div className="kpi-sub">Gaps Between 15-30 Days</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-title">Average Refill Delay</div>
                  <div className="kpi-value">{adherenceData?.average_synthetic_gap_days || 18.4} Days</div>
                  <div className="kpi-sub">Across Chronic Drug Classes</div>
                </div>
              </div>

              {/* Top Adherence Risk Medications Table */}
              <div className="card-panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Chronic Therapy Classes with High Refill Delay</h3>
                    <p className="panel-sub">Identifies maintenance medication classes impacting health plan Medicare Star Ratings.</p>
                  </div>
                </div>

                <div className="audit-table-wrapper">
                  <table className="rich-table" style={{ tableLayout: 'fixed', width: '100%' }}>
                    <thead>
                      <tr>
                        <th style={{ width: '32%' }}>Chronic Therapy / Medication Class</th>
                        <th style={{ width: '13%' }}>Monitored Patients</th>
                        <th style={{ width: '13%' }}>Avg Refill Delay</th>
                        <th style={{ width: '14%' }}>Patients with Gaps</th>
                        <th style={{ width: '14%' }}>Compliance Risk</th>
                        <th style={{ width: '14%' }}>Star Rating Impact</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(adherenceData?.top_adherence_risk_medications || [
                        { chronic_cohort: 'Cardiovascular: Statin Therapy (PDC-STA)', patient_count: 1420, avg_gap: 28.5, high_gap_patients: 410 },
                        { chronic_cohort: 'Diabetes: Glycemic Management (PDC-GLY)', patient_count: 1250, avg_gap: 24.2, high_gap_patients: 320 },
                        { chronic_cohort: 'Hypertension: RAS Antagonists (PDC-RASA)', patient_count: 1100, avg_gap: 22.0, high_gap_patients: 280 },
                        { chronic_cohort: 'Anticoagulants: DOAC Stroke Prevention', patient_count: 650, avg_gap: 26.4, high_gap_patients: 185 },
                        { chronic_cohort: 'Respiratory: Asthma / COPD Maintenance', patient_count: 890, avg_gap: 19.5, high_gap_patients: 160 }
                      ]).map((m, idx) => {
                        const name = m.chronic_cohort || m.medication_name || 'Chronic Maintenance Therapy';
                        const avgGap = m.avg_gap || 22.0;
                        return (
                          <tr key={idx}>
                            <td style={{ wordBreak: 'break-word', whiteSpace: 'normal' }}><b>{name}</b></td>
                            <td>{formatNumber(m.patient_count)} patients</td>
                            <td><b>{avgGap} Days</b></td>
                            <td><span className="badge rose">{m.high_gap_patients || 12} Patients</span></td>
                            <td>
                              <span className={`badge ${avgGap > 25 ? 'rose' : avgGap > 20 ? 'amber' : 'emerald'}`}>
                                {avgGap > 25 ? 'High Risk (<80% PDC)' : 'Moderate Gap'}
                              </span>
                            </td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <AlertTriangle size={13} color={avgGap > 25 ? 'var(--rose-500)' : 'var(--amber-500)'} />
                                <span style={{ fontSize: '11.5px', fontWeight: '600', color: avgGap > 25 ? 'var(--rose-500)' : 'var(--amber-600)' }}>
                                  {avgGap > 25 ? 'CMS Measure At Risk' : 'Standard Monitoring'}
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 5: EXECUTIVE SUMMARY
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'dashboard' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><LayoutDashboard size={18} /></div>
                  <div>
                    <div className="page-summary-title">Executive Health Plan Summary</div>
                    <div className="page-summary-sub">High-level overview of annual prescription spend, high-priority opportunities, and plan metrics.</div>
                  </div>
                </div>
                <span className="dataset-timestamp-badge active">
                  <Clock size={12} /> Dataset 1: 2024 | Dataset 2: July 2026
                </span>
              </div>

              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-header"><span className="kpi-title">Total Annual Drug Spend</span><DollarSign size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{formatMoney(kpis.total_drug_spend || 4280500000)}</div>
                  <div className="kpi-sub">CMS Part D Claims Fact</div>
                </div>
                <div className="kpi-card rose">
                  <div className="kpi-header"><span className="kpi-title">High-Priority Opportunities</span><AlertTriangle size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{kpis.high_priority_count || 184}</div>
                  <div className="kpi-sub">Urgent Review Targets</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-header"><span className="kpi-title">Prescription Claims</span><TrendingUp size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{formatNumber(kpis.total_utilization_claims || 12840000)}</div>
                  <div className="kpi-sub">Total 30-Day Fills</div>
                </div>
                <div className="kpi-card amber">
                  <div className="kpi-header"><span className="kpi-title">Medication Controls</span><ShieldAlert size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{kpis.pa_opportunities_count || 1240}</div>
                  <div className="kpi-sub">Prior Auth & Step Therapy Rules</div>
                </div>
                <div className="kpi-card emerald">
                  <div className="kpi-header"><span className="kpi-title">Compliance Gaps</span><Activity size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{kpis.synthetic_adherence_risk_count || 412}</div>
                  <div className="kpi-sub">Patients with &gt;30 Day Refill Gaps</div>
                </div>
              </div>

              <div className="charts-grid">
                <div className="card-panel">
                  <div className="panel-header">
                    <div>
                      <h3 className="panel-title">Top Urgent Optimization Opportunities</h3>
                      <p className="panel-sub">Ranked by potential plan savings and clinical impact</p>
                    </div>
                    <button className="btn btn-secondary" onClick={() => setActiveTab('opportunities')}>
                      View All Opportunities &rarr;
                    </button>
                  </div>
                  {dashboardData?.top_opportunities?.slice(0, 6).map((opp) => (
                    <div key={opp.opportunity_id} className="bar-chart-row" style={{ cursor: 'pointer' }} onClick={() => openOpportunityDetail(opp.opportunity_id)}>
                      <div className="bar-label" title={opp.brand_name}><b>{opp.brand_name}</b></div>
                      <div className="bar-track"><div className="bar-fill" style={{ width: `${opp.overall_score}%` }}></div></div>
                      <div className="bar-value"><span className={`badge ${opp.priority?.toLowerCase()}`}>{opp.overall_score} pts</span></div>
                    </div>
                  ))}
                </div>

                <div className="card-panel">
                  <div className="panel-header">
                    <div>
                      <h3 className="panel-title">Health Plan Strategy Quick Setup</h3>
                      <p className="panel-sub">Configure new business objectives or thresholds</p>
                    </div>
                  </div>
                  <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
                    Adjust Medicare Part D plan scopes, test generic substitution strategies, or optimize for Star Rating adherence using the Setup Console.
                  </p>
                  <button className="btn btn-primary" style={{ marginTop: '14px' }} onClick={() => setActiveTab('setup')}>
                    <Sliders size={14} /> Open Plan & Strategy Setup Console
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 6: PHARMACIST DECISION LOG (FORMERLY CLINICAL REVIEW & AUDIT)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'audit' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><UserCheck size={18} /></div>
                  <div>
                    <div className="page-summary-title">Clinical Pharmacist Decision Log</div>
                    <div className="page-summary-sub">Immutable audit trail of clinical pharmacist reviews, formulary adjustments, and P&T committee approvals.</div>
                  </div>
                </div>
                <span className="dataset-timestamp-badge active">
                  <ShieldCheck size={12} /> 100% Governance Audit Ready
                </span>
              </div>

              {/* Audit Summary KPI Row */}
              <div className="metric-row-grid">
                <div className="kpi-card emerald">
                  <div className="kpi-title">Total Decisions Logged</div>
                  <div className="kpi-value">{auditLog.length} Actions</div>
                  <div className="kpi-sub">Immutable Pharmacist Audit Trail</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-title">Approved Formulary Changes</div>
                  <div className="kpi-value">{auditLog.filter(a => a.status === 'Approved').length} Approved</div>
                  <div className="kpi-sub">Ready for P&T Implementation</div>
                </div>
                <div className="kpi-card amber">
                  <div className="kpi-title">Under Active Review</div>
                  <div className="kpi-value">{auditLog.filter(a => a.status === 'Under Review').length} Reviewing</div>
                  <div className="kpi-sub">Clinical Step-Therapy Evaluation</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-title">Compliance Governance</div>
                  <div className="kpi-value">100% Audited</div>
                  <div className="kpi-sub">Timestamped Reviewer Provenance</div>
                </div>
              </div>

              {/* Audit Search and Filter Bar */}
              <div className="card-panel" style={{ width: '100%', boxSizing: 'border-box' }}>
                <div className="panel-header" style={{ marginBottom: '14px' }}>
                  <div>
                    <h3 className="panel-title">Clinical Review & Decision Audit Trail</h3>
                    <p className="panel-sub">Record of pharmacist decisions, formulary approvals, and clinical rationale notes.</p>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <input
                      type="text"
                      className="setup-input"
                      style={{ width: '220px', padding: '6px 10px', fontSize: '12px' }}
                      placeholder="Search drug or reviewer..."
                      value={auditSearch}
                      onChange={(e) => setAuditSearch(e.target.value)}
                    />
                    <select
                      className="setup-select"
                      style={{ padding: '6px 10px', fontSize: '12px' }}
                      value={auditFilterStatus}
                      onChange={(e) => setAuditFilterStatus(e.target.value)}
                    >
                      <option value="ALL">All Statuses</option>
                      <option value="Approved">Approved</option>
                      <option value="Under Review">Under Review</option>
                      <option value="Rejected">Rejected</option>
                      <option value="Deferred">Deferred</option>
                    </select>
                  </div>
                </div>

                <div className="audit-table-wrapper">
                  <table className="audit-table">
                    <thead>
                      <tr>
                        <th style={{ width: '12%' }}>Opportunity ID</th>
                        <th style={{ width: '22%' }}>Target Medicine</th>
                        <th style={{ width: '16%' }}>Reviewer</th>
                        <th style={{ width: '14%' }}>Decision Status</th>
                        <th style={{ width: '24%' }}>Clinical Rationale Notes</th>
                        <th style={{ width: '12%' }}>Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAuditLogs.map((log, idx) => (
                        <tr key={idx}>
                          <td><b>{log.opportunity_id}</b></td>
                          <td><b>{log.drug}</b></td>
                          <td>{log.reviewer}</td>
                          <td>
                            <span className={`badge ${log.status === 'Approved' ? 'emerald' : log.status === 'Under Review' ? 'amber' : 'neutral'}`}>
                              {log.status}
                            </span>
                          </td>
                          <td>{log.notes}</td>
                          <td><span style={{ fontSize: '11px', color: '#64748b' }}><Clock size={11} /> {log.timestamp}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 7: INSURANCE AI ASSISTANT (FORMERLY AI COPILOT)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'assistant' && (
            <div className="card-panel" style={{ minHeight: '560px', display: 'flex', flexDirection: 'column' }}>
              {/* Page Summary Banner */}
              <div className="page-summary-banner">
                <div className="page-summary-left">
                  <div className="page-summary-icon"><Bot size={18} /></div>
                  <div>
                    <div className="page-summary-title">Insurance AI Decision Assistant</div>
                    <div className="page-summary-sub">Ask plain-language questions about prescription costs, medication controls, and bioequivalent alternatives grounded in curated CMS data.</div>
                  </div>
                </div>
                <span className="dataset-timestamp-badge active">
                  <Sparkles size={12} /> Grounded in CMS Datasets 1 & 2
                </span>
              </div>

              {/* Sample Questions Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
                {[
                  "Why is Restasis flagged?",
                  "Show top cost opportunities",
                  "Which drugs have PA and high utilization?",
                  "What changes if cost is prioritized?",
                  "What is the potential alternative for Xtandi?"
                ].map((q, i) => (
                  <button key={i} className="btn btn-secondary" style={{ fontSize: '11.5px', padding: '5px 10px' }} onClick={() => sendChatMessage(q)}>
                    <Bot size={13} /> {q}
                  </button>
                ))}
              </div>

              {/* Chat Thread */}
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px', padding: '10px 0' }}>
                {chatMessages.map((msg, i) => (
                  <div key={i} style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
                    {msg.sender === 'user' ? (
                      <div style={{
                        padding: '12px 16px',
                        borderRadius: '10px',
                        background: 'var(--primary)',
                        color: '#fff',
                        fontSize: '13.5px',
                        lineHeight: 1.5
                      }}>
                        {msg.text}
                      </div>
                    ) : (
                      <div className="assistant-chat-bubble">
                        <FormattedAssistantMessage content={msg.text} />
                      </div>
                    )}

                    {msg.citations && (
                      <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {msg.citations.map((c, ci) => (
                          <div key={ci} style={{ fontSize: '11px', color: '#0284c7', background: '#e0f2fe', padding: '4px 8px', borderRadius: '4px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            🔗 <b>Citation Provenance:</b> {c.source || 'CMS Curated Repository'} | {c.entity || 'Entity Fact'} | {c.metric || 'Metric'}
                          </div>
                        ))}
                      </div>
                    )}
                    {msg.disclaimer && (
                      <div style={{ fontSize: '10.5px', color: '#64748b', marginTop: '4px', fontStyle: 'italic' }}>
                        ⚠️ {msg.disclaimer}
                      </div>
                    )}
                  </div>
                ))}
                {chatLoading && <div style={{ color: '#64748b', fontSize: '12px' }}>Querying grounded knowledge base...</div>}
              </div>

              {/* Chat Input */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <input
                  type="text"
                  className="setup-input"
                  style={{ flex: 1 }}
                  placeholder="Ask a question about spend, medication controls, or alternatives..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
                />
                <button className="btn btn-primary" onClick={() => sendChatMessage()}>
                  Send Query
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          OPPORTUNITY DETAIL / HUMAN-IN-THE-LOOP CLINICAL REVIEW DRAWER
          ───────────────────────────────────────────────────────────── */}
      {selectedOpp && (
        <div className="drawer-backdrop" onClick={() => setSelectedOpp(null)}>
          <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className={`badge ${oppDetail?.opportunity?.priority?.toLowerCase() || 'critical'}`}>
                  {oppDetail?.opportunity?.priority || 'Critical'} Priority Opportunity
                </span>
                <h2 style={{ margin: '8px 0 2px' }}>{oppDetail?.opportunity?.brand_name}</h2>
                <div style={{ color: '#64748b', fontSize: '13px' }}>{oppDetail?.opportunity?.generic_name} • Doctor ID (NPI): {oppDetail?.opportunity?.npi || '1043298410'}</div>
              </div>
              <button className="btn btn-secondary" style={{ padding: '6px' }} onClick={() => setSelectedOpp(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="drawer-body" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px', overflowY: 'auto' }}>
              {/* Dedicated Human-in-the-Loop Banner */}
              <div className="hitl-callout-card">
                <div className="hitl-callout-title">
                  <UserCheck size={16} /> Human-in-the-Loop Clinical Review Required
                </div>
                <div className="hitl-callout-sub">
                  This system provides decision support. A licensed pharmacist or medical director reviews the economics, safety profile, and alternative candidates below before confirming any formulary changes.
                </div>
              </div>

              {/* 1. Score & Identity */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b' }}>Composite Priority Score</span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--primary)' }}>{oppDetail?.opportunity?.overall_score || 88} / 100</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', marginTop: '10px', fontSize: '11px', textAlign: 'center' }}>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Cost: <b>{oppDetail?.opportunity?.cost_score || 92}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Volume: <b>{oppDetail?.opportunity?.utilization_score || 85}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Controls: <b>{oppDetail?.opportunity?.friction_score || 70}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Compliance: <b>{oppDetail?.opportunity?.adherence_score || 40}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Generics: <b>{oppDetail?.opportunity?.alternative_score || 65}</b></div>
                </div>
              </div>

              {/* 2. Economics & Utilization */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ padding: '12px', background: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>Total Annual Plan Spend</div>
                  <div style={{ fontSize: '16px', fontWeight: '700' }}>{formatMoney(oppDetail?.opportunity?.total_drug_cost || 4200000)}</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--rose-500)', fontWeight: '600' }}>&gt; P90 High Cost Percentile</div>
                </div>
                <div style={{ padding: '12px', background: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>Prescription Claims Volume</div>
                  <div style={{ fontSize: '16px', fontWeight: '700' }}>{formatNumber(oppDetail?.opportunity?.total_claims || 14200)} fills</div>
                  <div style={{ fontSize: '10.5px', color: '#64748b' }}>Avg Cost: {formatMoney(oppDetail?.opportunity?.avg_cost_per_claim || 295)}/fill</div>
                </div>
              </div>

              {/* 3. Therapeutic Alternative Recommendation */}
              <div style={{ background: '#ecfdf5', padding: '14px', borderRadius: '8px', border: '1px solid #a7f3d0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--emerald-500)', fontWeight: '700', fontSize: '13px', marginBottom: '6px' }}>
                  <CheckCircle2 size={16} /> Recommended Bioequivalent Alternative Candidate
                </div>
                <div style={{ fontSize: '14px', fontWeight: '700', color: '#065f46' }}>
                  {oppDetail?.alternatives?.[0]?.candidate_name || 'Generic Bioequivalent (A-Rated Generic Equivalent)'}
                </div>
                <div style={{ fontSize: '12px', color: '#047857', marginTop: '4px' }}>
                  <b>Estimated Plan Savings:</b> 65% ({formatMoney(oppDetail?.opportunity?.total_drug_cost * 0.65 || 2730000)}) • Target Tier 2
                </div>
                <div style={{ fontSize: '11.5px', color: '#065f46', marginTop: '6px', fontStyle: 'italic' }}>
                  Guidance: {oppDetail?.alternatives?.[0]?.clinical_guidance || 'FDA Orange Book A-rated generic available at preferred copay tiers.'}
                </div>
              </div>

              {/* 4. Pharmacist Action Panel */}
              <div style={{ background: '#f1f5f9', padding: '14px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                <div style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#334155', marginBottom: '8px' }}>
                  Clinical Pharmacist Review & Approval Action
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <label style={{ fontSize: '12px', fontWeight: '600' }}>Decision Status:</label>
                    <select className="setup-select" style={{ padding: '6px 10px', fontSize: '12px' }} value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)}>
                      <option value="New">New Opportunity</option>
                      <option value="Under Review">Under Review (P&T Committee)</option>
                      <option value="Approved">Approved (Formulary Change)</option>
                      <option value="Rejected">Rejected (Clinical Necessity)</option>
                      <option value="Deferred">Deferred to Next Quarter</option>
                    </select>
                  </div>
                  <textarea
                    className="setup-input"
                    rows="3"
                    placeholder="Enter clinical rationale or notes for P&T committee audit trail..."
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {reviewSaved && <span style={{ color: 'var(--emerald-500)', fontSize: '12px', fontWeight: '600' }}>✓ Saved to Audit Log!</span>}
                    <button className="btn btn-primary" style={{ marginLeft: 'auto' }} onClick={handleSaveReview}>
                      Save Review Decision
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<App />);
}
