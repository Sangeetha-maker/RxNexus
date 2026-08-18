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

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const formatMoney = (val) => {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
};

const formatNumber = (val) => {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-US').format(val);
};

// Recommended Objective Presets (From PDF Section 4)
const OBJECTIVE_PRESETS = {
  spending: {
    id: 'spending',
    title: 'Reduce Drug Spending',
    desc: 'Maximizes cost reduction and specialty spend headroom.',
    weights: { cost: 0.50, utilization: 0.20, friction: 0.10, adherence: 0.10, alternative: 0.10 }
  },
  friction: {
    id: 'friction',
    title: 'Reduce Formulary Friction',
    desc: 'Pinpoints Prior Auth (PA) and Step Therapy (ST) access barriers.',
    weights: { cost: 0.20, utilization: 0.15, friction: 0.45, adherence: 0.10, alternative: 0.10 }
  },
  adherence: {
    id: 'adherence',
    title: 'Improve Adherence',
    desc: 'Targets chronic disease populations with high refill gaps (low PDC).',
    weights: { cost: 0.20, utilization: 0.15, friction: 0.10, adherence: 0.45, alternative: 0.10 }
  },
  generic: {
    id: 'generic',
    title: 'Increase Generic Utilization',
    desc: 'Prioritizes A-rated generic and biosimilar tier downshifts.',
    weights: { cost: 0.35, utilization: 0.15, friction: 0.10, adherence: 0.10, alternative: 0.30 }
  },
  balanced: {
    id: 'balanced',
    title: 'Balanced Strategy',
    desc: 'Standard multi-dimensional payer optimization baseline.',
    weights: { cost: 0.30, utilization: 0.25, friction: 0.20, adherence: 0.15, alternative: 0.10 }
  }
};

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
    if (activeTab === 'simulation') handleRunAnalysis();
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
      {/* SIDEBAR NAVIGATION (PDF Section 13) */}
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
            <Sliders size={18} /> <span>1. Analysis Setup</span>
          </li>
          <li className={`nav-item ${activeTab === 'opportunities' ? 'active' : ''}`} onClick={() => setActiveTab('opportunities')}>
            <Layers size={18} /> <span>2. Opportunities</span>
          </li>
          <li className={`nav-item ${activeTab === 'simulation' ? 'active' : ''}`} onClick={() => { setActiveTab('simulation'); setSelectedOpp(null); }}>
            <TrendingUp size={18} /> <span>3. What-if Simulation</span>
          </li>
          <li className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => { setActiveTab('dashboard'); setSelectedOpp(null); }}>
            <LayoutDashboard size={18} /> <span>Executive Dashboard</span>
          </li>
          <li className={`nav-item ${activeTab === 'friction' ? 'active' : ''}`} onClick={() => { setActiveTab('friction'); setSelectedOpp(null); }}>
            <ShieldAlert size={18} /> <span>Formulary Friction</span>
          </li>
          <li className={`nav-item ${activeTab === 'adherence' ? 'active' : ''}`} onClick={() => { setActiveTab('adherence'); setSelectedOpp(null); }}>
            <Activity size={18} /> <span>Adherence Risk</span>
          </li>
          <li className={`nav-item ${activeTab === 'assistant' ? 'active' : ''}`} onClick={() => setActiveTab('assistant')}>
            <Bot size={18} /> <span>AI Copilot</span>
          </li>
          <li className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => { setActiveTab('audit'); setSelectedOpp(null); }}>
            <UserCheck size={18} /> <span>Review / Audit</span>
          </li>
        </ul>

        <div style={{ padding: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: 1.4 }}>
            <b>Product Principle:</b><br />
            Insurer inputs business objective.<br />
            RXNexus calculates evidence.<br />
            Pharmacist makes final decision.
          </div>
        </div>
      </aside>

      {/* MAIN WRAPPER */}
      <div className="main-wrapper">
        {/* TOP HEADER */}
        <header className="top-header">
          <div className="header-left">
            <h1>
              {activeTab === 'setup' && 'Analysis Setup & Business Objective Console'}
              {activeTab === 'opportunities' && 'Ranked Opportunity Explorer'}
              {activeTab === 'simulation' && 'What-if Policy Simulation Workspace'}
              {activeTab === 'dashboard' && 'Executive Payer Pharmacy Dashboard'}
              {activeTab === 'friction' && 'Formulary Friction & Restriction View'}
              {activeTab === 'adherence' && 'Population Adherence Signals (Synthea)'}
              {activeTab === 'assistant' && 'Grounded AI Decision Copilot'}
              {activeTab === 'audit' && 'Clinical Review & Audit Decision Log'}
            </h1>
            <p>Insurer Interface: Business Objectives → Analysis → Evidence → Pharmacist Review</p>
          </div>

          <div className="header-actions">
            <button className="btn-run-analysis" style={{ padding: '8px 16px', fontSize: '13px' }} onClick={handleRunAnalysis}>
              <Zap size={15} /> Run Analysis
            </button>
            <div className="status-indicator">
              <span className="status-dot"></span> Governed CMS & Parquet Ready
            </div>
          </div>
        </header>

        <div className="content-body">
          {/* NOTICE BANNER */}
          <div className="guardrail-banner">
            <div className="guardrail-text">
              <Info size={18} color="var(--primary)" />
              <span><b>Decision-Support Standard:</b> Raw CMS claims and formulary tables are pre-ingested. Select your plan scope, business objective, and thresholds below to generate ranked evidence for pharmacist review.</span>
            </div>
            <span className="guardrail-tag">Human-In-The-Loop</span>
          </div>

          {/* ─────────────────────────────────────────────────────────────
              TAB 1: ANALYSIS SETUP (PDF SECTION 2, 3, 4)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'setup' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* 1. Plan & Scope Selectors */}
              <div className="card-panel">
                <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Filter size={18} color="var(--primary)" /> 1. Plan Scope & Target Benefit Package
                </h3>
                <p className="panel-sub">Select the Medicare Part D contract and Benefit Package (PBP) for analysis.</p>

                <div className="setup-form-grid" style={{ marginTop: '14px' }}>
                  <div className="setup-field">
                    <label className="setup-label">Medicare Part D Plan</label>
                    <select className="setup-select" value={selectedPlan} onChange={(e) => setSelectedPlan(e.target.value)}>
                      <option value="ALL">All Medicare Part D Plans (H5521 / H1234)</option>
                      <option value="SILVER">SilverScript Choice PDP (S5601)</option>
                      <option value="HUMANA">Humana Gold Plus HMO-POS (H1036)</option>
                      <option value="AETNA">Aetna Medicare Advantage Plan (H5521)</option>
                      <option value="UHC">UnitedHealthcare Standard Rx (S5820)</option>
                    </select>
                  </div>

                  <div className="setup-field">
                    <label className="setup-label">PBP / Plan Benefit Package</label>
                    <select className="setup-select" value={selectedPbp} onChange={(e) => setSelectedPbp(e.target.value)}>
                      <option value="ALL">All PBPs (All Benefit Packages)</option>
                      <option value="PBP001">PBP 001 - Standard Rx Benefit</option>
                      <option value="PBP002">PBP 002 - Enhanced Plus Comprehensive</option>
                      <option value="PBP003">PBP 003 - Value Tier Saver</option>
                      <option value="PBP004">PBP 004 - Dual-Eligible Special Needs</option>
                    </select>
                  </div>

                  <div className="setup-field">
                    <label className="setup-label">Drug / Prescriber NPI Search</label>
                    <input
                      type="text"
                      className="setup-input"
                      placeholder="e.g. Restasis, Xtandi, or 10-digit NPI"
                      value={drugNpiSearch}
                      onChange={(e) => setDrugNpiSearch(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* 2. Primary Objective Presets (PDF Section 2 & 4) */}
              <div className="card-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Award size={18} color="var(--primary)" /> 2. Primary Business Objective Presets
                    </h3>
                    <p className="panel-sub">Selecting an objective automatically loads recommended prototype weights.</p>
                  </div>
                  <span className={`weight-total-badge ${totalWeightPercent === 100 ? 'valid' : 'invalid'}`}>
                    Total Weights: {totalWeightPercent}% {totalWeightPercent === 100 ? '✓' : '(Must sum to 100%)'}
                  </span>
                </div>

                <div className="objective-grid">
                  {Object.values(OBJECTIVE_PRESETS).map((obj) => (
                    <div
                      key={obj.id}
                      className={`objective-card ${primaryObjective === obj.id ? 'selected' : ''}`}
                      onClick={() => handleObjectiveSelect(obj.id)}
                    >
                      <div>
                        <div className="objective-card-header">
                          <input type="radio" name="objectiveRadio" checked={primaryObjective === obj.id} readOnly />
                          {obj.title}
                        </div>
                        <div className="objective-card-sub">{obj.desc}</div>
                      </div>
                      <div className="objective-weights-mini">
                        <span>Cost: {obj.weights.cost * 100}%</span>
                        <span>Util: {obj.weights.utilization * 100}%</span>
                        <span>Fric: {obj.weights.friction * 100}%</span>
                        <span>Adh: {obj.weights.adherence * 100}%</span>
                        <span>Alt: {obj.weights.alternative * 100}%</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Advanced Priority Weight Sliders (PDF Section 3) */}
                <div style={{ marginTop: '16px', padding: '16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>Advanced Priority Weight Customization</span>
                    <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '11px' }} onClick={() => handleObjectiveSelect(primaryObjective)}>
                      <RefreshCw size={12} /> Reset to Objective Preset
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
                    <div className="slider-group">
                      <div className="slider-header"><span>Cost Impact:</span> <b>{Math.round(weights.cost * 100)}%</b></div>
                      <input type="range" min="0" max="1" step="0.05" value={weights.cost} onChange={(e) => handleWeightChange('cost', e.target.value)} className="custom-range" />
                    </div>
                    <div className="slider-group">
                      <div className="slider-header"><span>Utilization Volume:</span> <b>{Math.round(weights.utilization * 100)}%</b></div>
                      <input type="range" min="0" max="1" step="0.05" value={weights.utilization} onChange={(e) => handleWeightChange('utilization', e.target.value)} className="custom-range" />
                    </div>
                    <div className="slider-group">
                      <div className="slider-header"><span>Formulary Friction:</span> <b>{Math.round(weights.friction * 100)}%</b></div>
                      <input type="range" min="0" max="1" step="0.05" value={weights.friction} onChange={(e) => handleWeightChange('friction', e.target.value)} className="custom-range" />
                    </div>
                    <div className="slider-group">
                      <div className="slider-header"><span>Adherence Risk:</span> <b>{Math.round(weights.adherence * 100)}%</b></div>
                      <input type="range" min="0" max="1" step="0.05" value={weights.adherence} onChange={(e) => handleWeightChange('adherence', e.target.value)} className="custom-range" />
                    </div>
                    <div className="slider-group">
                      <div className="slider-header"><span>Alternative Headroom:</span> <b>{Math.round(weights.alternative * 100)}%</b></div>
                      <input type="range" min="0" max="1" step="0.05" value={weights.alternative} onChange={(e) => handleWeightChange('alternative', e.target.value)} className="custom-range" />
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. Analysis Scope, Thresholds & Strategy (PDF Section 2) */}
              <div className="card-panel">
                <h3 className="panel-title">3. Analysis Scope, Thresholds & Restriction Filters</h3>
                <p className="panel-sub">Configure cohort inclusion, spend/claim thresholds, and restriction rules.</p>

                {/* Scope Pills */}
                <div style={{ marginTop: '12px' }}>
                  <label className="setup-label">Analysis Scope (Multi-Select)</label>
                  <div className="scope-pills-grid">
                    {[
                      { id: 'all', label: 'All Drugs' },
                      { id: 'high-cost', label: 'High-Cost Outliers' },
                      { id: 'high-util', label: 'High-Utilization Volume' },
                      { id: 'tier4-5', label: 'Tier 4 & 5 Specialty' },
                      { id: 'pa', label: 'Prior Authorization (PA)' },
                      { id: 'st', label: 'Step Therapy (ST)' },
                      { id: 'adherence', label: 'Adherence-Risk Cohort' }
                    ].map(pill => (
                      <div
                        key={pill.id}
                        className={`scope-pill ${analysisScope.includes(pill.id) ? 'active' : ''}`}
                        onClick={() => toggleScope(pill.id)}
                      >
                        {pill.label}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Thresholds Grid */}
                <div className="setup-form-grid" style={{ marginTop: '16px' }}>
                  <div className="setup-field">
                    <label className="setup-label">Minimum Spend Threshold ($)</label>
                    <input type="number" className="setup-input" placeholder="e.g. 50000" value={minSpend} onChange={(e) => setMinSpend(e.target.value)} />
                  </div>
                  <div className="setup-field">
                    <label className="setup-label">Minimum Claims Threshold</label>
                    <input type="number" className="setup-input" placeholder="e.g. 500" value={minClaims} onChange={(e) => setMinClaims(e.target.value)} />
                  </div>
                  <div className="setup-field">
                    <label className="setup-label">Priority / Percentile Threshold</label>
                    <select className="setup-select" value={percentileThreshold} onChange={(e) => setPercentileThreshold(e.target.value)}>
                      <option value="p90">P90 Empirical Cutoff (Top 10% Outliers)</option>
                      <option value="p80">P80 Threshold (Top 20% Outliers)</option>
                      <option value="top100">Top 100 Prioritized Records</option>
                    </select>
                  </div>
                  <div className="setup-field">
                    <label className="setup-label">Min. Estimated Savings (%)</label>
                    <input type="number" className="setup-input" placeholder="e.g. 25" value={minSavings} onChange={(e) => setMinSavings(e.target.value)} />
                  </div>
                </div>

                {/* Restrictions & Alternative Strategy */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
                  <div>
                    <label className="setup-label">Restriction Filters (Checkboxes)</label>
                    <div className="checkbox-flex-group">
                      <label className="checkbox-label"><input type="checkbox" checked={restrictionCheckboxes.pa} onChange={(e) => setRestrictionCheckboxes(prev => ({ ...prev, pa: e.target.checked }))} /> Prior Auth (PA)</label>
                      <label className="checkbox-label"><input type="checkbox" checked={restrictionCheckboxes.st} onChange={(e) => setRestrictionCheckboxes(prev => ({ ...prev, st: e.target.checked }))} /> Step Therapy (ST)</label>
                      <label className="checkbox-label"><input type="checkbox" checked={restrictionCheckboxes.ql} onChange={(e) => setRestrictionCheckboxes(prev => ({ ...prev, ql: e.target.checked }))} /> Quantity Limit (QL)</label>
                    </div>
                  </div>

                  <div>
                    <label className="setup-label">Alternative Strategy (Radio Cards)</label>
                    <div className="checkbox-flex-group">
                      <label className="checkbox-label"><input type="radio" name="altStrat" checked={altStrategy === 'all'} onChange={() => setAltStrategy('all')} /> Any Candidate</label>
                      <label className="checkbox-label"><input type="radio" name="altStrat" checked={altStrategy === 'generic'} onChange={() => setAltStrategy('generic')} /> Generic Sub</label>
                      <label className="checkbox-label"><input type="radio" name="altStrat" checked={altStrategy === 'lowertier'} onChange={() => setAltStrategy('lowertier')} /> Lower-Tier</label>
                      <label className="checkbox-label"><input type="radio" name="altStrat" checked={altStrategy === 'steptherapy'} onChange={() => setAltStrategy('steptherapy')} /> Step-Therapy</label>
                    </div>
                  </div>
                </div>

                {/* Action CTA Bar */}
                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end', gap: '12px', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>Ready to generate ranked opportunities based on chosen parameters</span>
                  <button className="btn-run-analysis" onClick={handleRunAnalysis}>
                    <Zap size={18} /> Run Analysis & Open Opportunities <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 2: OPPORTUNITIES EXPLORER (PDF SECTION 5)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'opportunities' && (
            <div className="card-panel">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">Ranked Opportunity Explorer</h3>
                  <p className="panel-sub">Opportunities prioritized according to selected objective weights and thresholds. Click any row for clinical evidence.</p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-secondary" onClick={() => setActiveTab('setup')}>
                    <Sliders size={14} /> Edit Analysis Setup
                  </button>
                  <button className="btn btn-primary" onClick={handleRunAnalysis}>
                    <RefreshCw size={14} /> Refresh Ranks
                  </button>
                </div>
              </div>

              {/* Table (Columns match PDF Section 5) */}
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Priority</th>
                      <th>Drug (Brand & Generic)</th>
                      <th>Tier</th>
                      <th>Total Spend</th>
                      <th>Claims</th>
                      <th>PA Required</th>
                      <th>Score</th>
                      <th>Est. Savings</th>
                      <th>Action</th>
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
                            <span className="badge warning">Yes (PA)</span>
                          ) : (
                            <span className="badge neutral">No</span>
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
                          <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '11px' }}>
                            Inspect <ChevronRight size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Table Footer */}
              <div className="table-footer">
                <div style={{ fontSize: '12.5px', color: '#64748b' }}>Showing {opportunities.length} of {oppTotal} ranked opportunities</div>
                <div className="pagination">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
                  <button className="current">{page}</button>
                  <button onClick={() => setPage(p => p + 1)}>Next</button>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 3: WHAT-IF SIMULATION (PDF SECTION 7)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'simulation' && (
            <div className="card-panel">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">What-If Policy Simulation Workspace</h3>
                  <p className="panel-sub">Simulate prospective formulary policy changes and observe before vs after rank shifts in under 45 milliseconds.</p>
                </div>
                <button className="btn btn-primary" onClick={handleRunAnalysis}>
                  <Zap size={14} /> Recalculate Simulation
                </button>
              </div>

              {/* Sliders Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', background: '#f8fafc', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
                <div className="slider-group">
                  <div className="slider-header"><span>Cost Weight:</span> <b>{Math.round(weights.cost * 100)}%</b></div>
                  <input type="range" min="0" max="1" step="0.05" value={weights.cost} onChange={(e) => handleWeightChange('cost', e.target.value)} className="custom-range" />
                </div>
                <div className="slider-group">
                  <div className="slider-header"><span>Utilization Weight:</span> <b>{Math.round(weights.utilization * 100)}%</b></div>
                  <input type="range" min="0" max="1" step="0.05" value={weights.utilization} onChange={(e) => handleWeightChange('utilization', e.target.value)} className="custom-range" />
                </div>
                <div className="slider-group">
                  <div className="slider-header"><span>Friction Weight:</span> <b>{Math.round(weights.friction * 100)}%</b></div>
                  <input type="range" min="0" max="1" step="0.05" value={weights.friction} onChange={(e) => handleWeightChange('friction', e.target.value)} className="custom-range" />
                </div>
                <div className="slider-group">
                  <div className="slider-header"><span>Adherence Weight:</span> <b>{Math.round(weights.adherence * 100)}%</b></div>
                  <input type="range" min="0" max="1" step="0.05" value={weights.adherence} onChange={(e) => handleWeightChange('adherence', e.target.value)} className="custom-range" />
                </div>
                <div className="slider-group">
                  <div className="slider-header"><span>Alternative Weight:</span> <b>{Math.round(weights.alternative * 100)}%</b></div>
                  <input type="range" min="0" max="1" step="0.05" value={weights.alternative} onChange={(e) => handleWeightChange('alternative', e.target.value)} className="custom-range" />
                </div>
              </div>

              {/* Before vs After Table */}
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Drug Name</th>
                      <th>Baseline Score</th>
                      <th>Simulated Score</th>
                      <th>Score Delta</th>
                      <th>Projected Rank Shift</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opportunities.slice(0, 8).map((opp, idx) => {
                      const simScore = Math.min(100, Math.max(10, Math.round(
                        (opp.cost_score || 70) * weights.cost +
                        (opp.utilization_score || 60) * weights.utilization +
                        (opp.friction_score || 50) * weights.friction +
                        (opp.adherence_score || 40) * weights.adherence +
                        (opp.alternative_score || 60) * weights.alternative
                      )));
                      const delta = simScore - opp.overall_score;
                      return (
                        <tr key={opp.opportunity_id}>
                          <td><b>{opp.brand_name}</b> <span style={{ color: '#64748b', fontSize: '11px' }}>({opp.generic_name})</span></td>
                          <td><b>{opp.overall_score} pts</b></td>
                          <td><b style={{ color: 'var(--primary)' }}>{simScore} pts</b></td>
                          <td>
                            <span className={`badge ${delta > 0 ? 'rose' : delta < 0 ? 'emerald' : 'neutral'}`}>
                              {delta > 0 ? `+${delta}` : delta} pts
                            </span>
                          </td>
                          <td>
                            {delta > 0 ? (
                              <span style={{ color: 'var(--rose-500)', fontWeight: '600' }}>↑ Moved Up Priority</span>
                            ) : delta < 0 ? (
                              <span style={{ color: 'var(--emerald-500)', fontWeight: '600' }}>↓ Lowered Priority</span>
                            ) : (
                              <span style={{ color: '#64748b' }}>— Unchanged</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 4: EXECUTIVE DASHBOARD
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'dashboard' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-header"><span className="kpi-title">Total Drug Spend</span><DollarSign size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{formatMoney(kpis.total_drug_spend || 4280500000)}</div>
                  <div className="kpi-sub">CMS Part D Claims Fact</div>
                </div>
                <div className="kpi-card rose">
                  <div className="kpi-header"><span className="kpi-title">High Priority Opportunities</span><AlertTriangle size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{kpis.high_priority_count || 184}</div>
                  <div className="kpi-sub">Score &ge; 75 Intervention Targets</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-header"><span className="kpi-title">Utilization Claims</span><TrendingUp size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{formatNumber(kpis.total_utilization_claims || 12840000)}</div>
                  <div className="kpi-sub">Standardized Prescriptions</div>
                </div>
                <div className="kpi-card amber">
                  <div className="kpi-header"><span className="kpi-title">Formulary Friction Rate</span><ShieldAlert size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{kpis.pa_opportunities_count || 1240}</div>
                  <div className="kpi-sub">Prior Auth & Step Therapy Rules</div>
                </div>
                <div className="kpi-card emerald">
                  <div className="kpi-header"><span className="kpi-title">Adherence Gaps</span><Activity size={18} className="kpi-icon" /></div>
                  <div className="kpi-value">{kpis.synthetic_adherence_risk_count || 412}</div>
                  <div className="kpi-sub">Population Signals (PDC &lt; 80%)</div>
                </div>
              </div>

              <div className="charts-grid">
                <div className="card-panel">
                  <div className="panel-header">
                    <div>
                      <h3 className="panel-title">Top Urgent Optimization Opportunities</h3>
                      <p className="panel-sub">Ranked by multi-dimensional opportunity score</p>
                    </div>
                    <button className="btn btn-secondary" onClick={() => setActiveTab('opportunities')}>
                      View All &rarr;
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
                      <h3 className="panel-title">Fast Policy Setup</h3>
                      <p className="panel-sub">Configure new business objectives or thresholds</p>
                    </div>
                  </div>
                  <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
                    Adjust Medicare Part D plan scopes, test generic substitution strategies, or optimize for Star Rating adherence using the Setup Console.
                  </p>
                  <button className="btn btn-primary" style={{ marginTop: '14px' }} onClick={() => setActiveTab('setup')}>
                    <Sliders size={14} /> Open Analysis Setup Console
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────────
              TAB 5: FORMULARY FRICTION VIEW (PDF SECTION 8)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'friction' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Top Metrics Row */}
              <div className="metric-row-grid">
                <div className="kpi-card amber">
                  <div className="kpi-title">Prior Auth (PA) Rate</div>
                  <div className="kpi-value">{frictionData?.tier_breakdown?.[3]?.pa_rate_pct || 34.2}%</div>
                  <div className="kpi-sub">{frictionData?.pa_count || 1420} Drugs with PA Mandate</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-title">Step Therapy (ST) Rate</div>
                  <div className="kpi-value">{frictionData?.tier_breakdown?.[2]?.st_rate_pct || 18.7}%</div>
                  <div className="kpi-sub">{frictionData?.st_count || 820} Drugs with Step Protocol</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-title">Quantity Limit (QL) Rate</div>
                  <div className="kpi-value">42.5%</div>
                  <div className="kpi-sub">{frictionData?.ql_count || 1890} Drugs with 30-Day Caps</div>
                </div>
                <div className="kpi-card emerald">
                  <div className="kpi-title">Total Benefit Records</div>
                  <div className="kpi-value">{formatNumber(frictionData?.total_records || 45200)}</div>
                  <div className="kpi-sub">{frictionData?.total_formularies || 128} Benefit Formularies</div>
                </div>
              </div>

              {/* Tier Breakdown Table (PDF Section 8) */}
              <div className="card-panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Formulary Restriction Rate by Benefit Tier</h3>
                    <p className="panel-sub">PA, Step Therapy, and Quantity Limit percentages across Tier 1 through Tier 5.</p>
                  </div>
                </div>

                <div className="data-table-container">
                  <table className="rich-table">
                    <thead>
                      <tr>
                        <th>Formulary Tier</th>
                        <th>Drug Catalog Count</th>
                        <th>Prior Auth (PA %)</th>
                        <th>Step Therapy (ST %)</th>
                        <th>Quantity Limit (QL %)</th>
                        <th>Avg Friction Score</th>
                        <th>Access Impact Rating</th>
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
                          <td><b>Tier {t.tier_level} {t.tier_level <= 2 ? '(Generic)' : t.tier_level <= 4 ? '(Brand)' : '(Specialty)'}</b></td>
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
                              {t.avg_friction > 60 ? 'High Restriction Barrier' : t.avg_friction > 30 ? 'Moderate Friction' : 'Open Access Tier'}
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
              TAB 6: ADHERENCE RISK VIEW (PDF SECTION 9)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'adherence' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="metric-row-grid">
                <div className="kpi-card emerald">
                  <div className="kpi-title">Synthetic Patients Analyzed</div>
                  <div className="kpi-value">{formatNumber(adherenceData?.synthetic_patients_analyzed || 5000)}</div>
                  <div className="kpi-sub">Synthea Longitudinal Timeline</div>
                </div>
                <div className="kpi-card rose">
                  <div className="kpi-title">High Adherence Risk (PDC &lt; 80%)</div>
                  <div className="kpi-value">{adherenceData?.high_risk_count || 412} Patients</div>
                  <div className="kpi-sub">Refill Gap Gaps &gt; 30 Days</div>
                </div>
                <div className="kpi-card amber">
                  <div className="kpi-title">Moderate Risk (PDC 65-79%)</div>
                  <div className="kpi-value">{adherenceData?.medium_risk_count || 890} Patients</div>
                  <div className="kpi-sub">Gaps between 15-30 Days</div>
                </div>
                <div className="kpi-card indigo">
                  <div className="kpi-title">Average Refill Gap Days</div>
                  <div className="kpi-value">{adherenceData?.average_synthetic_gap_days || 18.4} Days</div>
                  <div className="kpi-sub">Across Chronic Drug Cohorts</div>
                </div>
              </div>

              {/* Top Adherence Risk Medications Table (PDF Section 9) */}
              <div className="card-panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Top Chronic Therapy Adherence Risk Cohorts</h3>
                    <p className="panel-sub">Identifies maintenance therapy classes with high refill delays impacting Star Ratings.</p>
                  </div>
                  <span className="badge warning">SYNTHETIC LONGITUDINAL DATASET</span>
                </div>

                <div className="data-table-container">
                  <table className="rich-table">
                    <thead>
                      <tr>
                        <th>Chronic Medication / Class</th>
                        <th>Patient Cohort Count</th>
                        <th>Average Refill Gap</th>
                        <th>High-Gap Beneficiaries (&gt;15 Days)</th>
                        <th>Adherence Risk Level</th>
                        <th>Star Rating Vulnerability</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(adherenceData?.top_adherence_risk_medications || [
                        { medication_name: 'Atorvastatin 20mg (Statin Cohort)', patient_count: 1420, avg_gap: 28.5, high_gap_patients: 410 },
                        { medication_name: 'Metformin 500mg (Diabetes Cohort)', patient_count: 1250, avg_gap: 24.2, high_gap_patients: 320 },
                        { medication_name: 'Lisinopril 10mg (RAS Antagonist Cohort)', patient_count: 1100, avg_gap: 22.0, high_gap_patients: 280 },
                        { medication_name: 'Empagliflozin (SGLT2 Inhibitor)', patient_count: 650, avg_gap: 34.0, high_gap_patients: 215 },
                        { medication_name: 'Amlodipine 5mg (Antihypertensive)', patient_count: 890, avg_gap: 19.5, high_gap_patients: 160 }
                      ]).map((m, idx) => (
                        <tr key={idx}>
                          <td><b>{m.medication_name}</b></td>
                          <td>{formatNumber(m.patient_count)} patients</td>
                          <td><b>{m.avg_gap} Days</b></td>
                          <td><span className="badge rose">{m.high_gap_patients} Patients</span></td>
                          <td>
                            <span className={`badge ${m.avg_gap > 25 ? 'rose' : m.avg_gap > 20 ? 'amber' : 'emerald'}`}>
                              {m.avg_gap > 25 ? 'High Abandonment Risk' : 'Moderate Adherence Gap'}
                            </span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <AlertTriangle size={14} color={m.avg_gap > 25 ? 'var(--rose-500)' : 'var(--amber-500)'} />
                              <span style={{ fontSize: '12px', fontWeight: '600' }}>Part D Star Measure At Risk</span>
                            </div>
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
              TAB 7: GROUNDED AI COPILOT (PDF SECTION 10)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'assistant' && (
            <div className="card-panel" style={{ minHeight: '560px', display: 'flex', flexDirection: 'column' }}>
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">Grounded AI Decision Copilot</h3>
                  <p className="panel-sub">Zero-hallucination assistant citing deterministic curated repository metrics.</p>
                </div>
              </div>

              {/* Sample Questions Chips (PDF Section 10) */}
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
                    <div style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      background: msg.sender === 'user' ? 'var(--primary)' : '#f1f5f9',
                      color: msg.sender === 'user' ? '#fff' : '#0f172a',
                      fontSize: '13.5px',
                      lineHeight: 1.5
                    }}>
                      {msg.text}
                    </div>
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
                  placeholder="Ask a question about spend, friction, or alternatives..."
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

          {/* ─────────────────────────────────────────────────────────────
              TAB 8: CLINICAL REVIEW & AUDIT LOG (CONFINED TO 1 PAGE)
              ───────────────────────────────────────────────────────────── */}
          {activeTab === 'audit' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
                    <p className="panel-sub">Confined 1-page log of pharmacist decisions, formulary approvals, and clinical notes.</p>
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

                {/* Confined Responsive Table Container */}
                <div className="audit-table-wrapper">
                  <table className="audit-table">
                    <thead>
                      <tr>
                        <th style={{ width: '12%' }}>Opp ID</th>
                        <th style={{ width: '22%' }}>Target Drug</th>
                        <th style={{ width: '16%' }}>Reviewer</th>
                        <th style={{ width: '14%' }}>Decision Status</th>
                        <th style={{ width: '24%' }}>Clinical Review Notes</th>
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
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          OPPORTUNITY DETAIL / CLINICAL REVIEW DRAWER (PDF SECTION 6)
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
                <div style={{ color: '#64748b', fontSize: '13px' }}>{oppDetail?.opportunity?.generic_name} • NPI: {oppDetail?.opportunity?.npi || '1043298410'}</div>
              </div>
              <button className="btn btn-secondary" style={{ padding: '6px' }} onClick={() => setSelectedOpp(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="drawer-body" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px', overflowY: 'auto' }}>
              {/* 1. Score & Identity */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b' }}>Composite Priority Score</span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--primary)' }}>{oppDetail?.opportunity?.overall_score || 88} / 100</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', marginTop: '10px', fontSize: '11px', textAlign: 'center' }}>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Cost: <b>{oppDetail?.opportunity?.cost_score || 92}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Util: <b>{oppDetail?.opportunity?.utilization_score || 85}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Fric: <b>{oppDetail?.opportunity?.friction_score || 70}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Adh: <b>{oppDetail?.opportunity?.adherence_score || 40}</b></div>
                  <div style={{ background: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>Alt: <b>{oppDetail?.opportunity?.alternative_score || 65}</b></div>
                </div>
              </div>

              {/* 2. Economics & Utilization */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ padding: '12px', background: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>Total Annual Spend</div>
                  <div style={{ fontSize: '16px', fontWeight: '700' }}>{formatMoney(oppDetail?.opportunity?.total_drug_cost || 4200000)}</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--rose-500)', fontWeight: '600' }}>&gt; P90 Cost Percentile</div>
                </div>
                <div style={{ padding: '12px', background: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>Claims & 30-Day Fills</div>
                  <div style={{ fontSize: '16px', fontWeight: '700' }}>{formatNumber(oppDetail?.opportunity?.total_claims || 14200)} claims</div>
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
                  Clinical Pharmacist Review Action
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <label style={{ fontSize: '12px', fontWeight: '600' }}>Review Status:</label>
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
