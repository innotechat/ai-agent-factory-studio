import React, { useState } from 'react';
import {
  Server,
  Layers,
  Bot,
  Cpu,
  Coins,
  Code2,
  Building2,
  Shield,
  Radio,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Zap,
  Lock,
  Globe,
  MessageSquare,
  Terminal,
  Activity,
  ArrowRight,
  Database,
  Sliders,
  Check,
  ChevronRight,
  ExternalLink,
  Sparkles
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  role: string;
  model: string;
  provider: 'openai' | 'anthropic' | 'gemini' | 'openrouter';
  status: 'active' | 'draft' | 'deploying';
  channels: string[];
  tools: string[];
  knowledgeDocs: number;
  monthlyTokens: number;
}

interface ProviderModel {
  id: string;
  name: string;
  provider: string;
  inputCostPer1M: number;
  outputCostPer1M: number;
  latencyMs: number;
  health: 'healthy' | 'degraded';
  contextWindow: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'gateway' | 'credits' | 'api' | 'roadmap'>('overview');
  const [tenantMode, setTenantMode] = useState<'agency' | 'direct' | 'reseller'>('agency');
  const [selectedAgent, setSelectedAgent] = useState<string>('agent-1');
  const [apiSimulating, setApiSimulating] = useState(false);
  const [apiResponse, setApiResponse] = useState<string | null>(null);
  const [testPrompt, setTestPrompt] = useState('Summarize the customer refund policy and propose an escalation workflow.');

  const agents: Agent[] = [
    {
      id: 'agent-1',
      name: 'InnoTech Support Dispatcher',
      role: 'Tier 1 Triage & SLA Routing',
      model: 'gemini-2.5-flash',
      provider: 'gemini',
      status: 'active',
      channels: ['WhatsApp Cloud', 'Webchat Widget', 'Client Portal'],
      tools: ['Knowledge Search', 'Ticket Escalation HTTP', 'CRM Lookup MCP'],
      knowledgeDocs: 14,
      monthlyTokens: 482100,
    },
    {
      id: 'agent-2',
      name: 'Sales Qualifier & Booking',
      role: 'Inbound Discovery & Calendar Sync',
      model: 'gpt-4.1-mini',
      provider: 'openai',
      status: 'active',
      channels: ['WhatsApp QR (Baileys)', 'Webchat Widget'],
      tools: ['Booking Calendar HTTP', 'Lead Qualification'],
      knowledgeDocs: 8,
      monthlyTokens: 215400,
    },
    {
      id: 'agent-3',
      name: 'Operations Assistant',
      role: 'Internal Policy & Data Queries',
      model: 'claude-3-5-sonnet',
      provider: 'anthropic',
      status: 'active',
      channels: ['Client Portal', 'API v1'],
      tools: ['Database Read MCP', 'Document Summarizer'],
      knowledgeDocs: 32,
      monthlyTokens: 741000,
    },
  ];

  const models: ProviderModel[] = [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google Gemini', inputCostPer1M: 0.15, outputCostPer1M: 0.60, latencyMs: 240, health: 'healthy', contextWindow: '1M tokens' },
    { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', provider: 'OpenAI', inputCostPer1M: 0.40, outputCostPer1M: 1.60, latencyMs: 380, health: 'healthy', contextWindow: '128k tokens' },
    { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', inputCostPer1M: 3.00, outputCostPer1M: 15.00, latencyMs: 510, health: 'healthy', contextWindow: '200k tokens' },
    { id: 'deepseek-r1', name: 'DeepSeek R1', provider: 'OpenRouter', inputCostPer1M: 0.55, outputCostPer1M: 2.19, latencyMs: 640, health: 'healthy', contextWindow: '64k tokens' },
  ];

  const handleSimulateExecution = () => {
    setApiSimulating(true);
    setApiResponse(null);
    setTimeout(() => {
      setApiSimulating(false);
      setApiResponse(JSON.stringify({
        id: "chatcmpl-" + Math.random().toString(36).substring(2, 11),
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: "innotech/gemini-2.5-flash",
        provider_routed: "gemini",
        tenant_id: "tenant-innotech-prod-01",
        credit_reservation: {
          reserved_units: 50,
          settled_units: 18,
          status: "settled_confirmed"
        },
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: "Refund Policy Summary:\n1. Standard refunds are processed within 14 calendar days of request.\n2. Digital license keys and consumed API credits are non-refundable once activated.\n3. Escalations require supervisor approval when exceeding $250.00.\n\nEscalation Proposal:\n• Ticket auto-routed to Tier 2 Lead\n• Ledger hold placed on transaction ID\n• Customer notified via WhatsApp and Webhook."
            },
            finish_reason: "stop"
          }
        ],
        usage: {
          prompt_tokens: 64,
          completion_tokens: 98,
          total_tokens: 162,
          estimated_cost_usd: 0.000068
        }
      }, null, 2));
    }, 600);
  };

  const currentAgent = agents.find(a => a.id === selectedAgent) || agents[0];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-lg shadow-sm">
              IF
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900 tracking-tight text-base">InnoTech AI Agent Factory</span>
                <span className="text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Online · Port 3000
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">Production SaaS Control Plane & Multi-Tenant AI Gateway</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 bg-slate-100 p-1 rounded-lg text-xs font-medium text-slate-600">
              <span className="px-2 py-1 bg-white rounded shadow-xs text-slate-800 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-blue-600" />
                29 Models (Head 0039)
              </span>
              <span className="px-2 py-1 text-slate-500 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-emerald-600" />
                RBAC Active
              </span>
            </div>

            <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
              <span className="text-xs text-slate-500 hidden lg:inline">Mode:</span>
              <select
                id="tenant-mode-select"
                value={tenantMode}
                onChange={(e) => setTenantMode(e.target.value as any)}
                className="text-xs font-medium bg-white border border-slate-300 rounded-md px-2 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-900"
              >
                <option value="agency">Agency / Reseller</option>
                <option value="direct">Direct SaaS Tenant</option>
                <option value="reseller">White-label Partner</option>
              </select>
            </div>
          </div>
        </div>

        {/* Primary Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 border-t border-slate-100 overflow-x-auto scrollbar-none">
          <button
            id="tab-overview"
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === 'overview'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Layers className="w-4 h-4" />
            Platform Hierarchy
          </button>
          <button
            id="tab-agents"
            onClick={() => setActiveTab('agents')}
            className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === 'agents'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Bot className="w-4 h-4" />
            Agent Runtime ({agents.length})
          </button>
          <button
            id="tab-gateway"
            onClick={() => setActiveTab('gateway')}
            className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === 'gateway'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Cpu className="w-4 h-4" />
            AI Gateway & Models
          </button>
          <button
            id="tab-credits"
            onClick={() => setActiveTab('credits')}
            className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === 'credits'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Coins className="w-4 h-4" />
            Usage & Credits
          </button>
          <button
            id="tab-api"
            onClick={() => setActiveTab('api')}
            className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === 'api'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Code2 className="w-4 h-4" />
            Public API (/v1)
          </button>
          <button
            id="tab-roadmap"
            onClick={() => setActiveTab('roadmap')}
            className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === 'roadmap'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Activity className="w-4 h-4" />
            Migration Roadmap
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* System Baseline Alert Banner */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
              <Server className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-slate-900">InnoTech AI Agent Factory Codebase Initialized</h2>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  Target: Production SaaS
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                Upstream foundation preserved: FastAPI + SQLAlchemy 2.0 (Head 0039), Baileys WhatsApp runtime, multi-channel agents, and Next.js portal.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setActiveTab('api')}
              className="text-xs font-medium bg-slate-900 text-white px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-1.5"
            >
              <Terminal className="w-3.5 h-3.5" />
              Test AI Gateway API
            </button>
          </div>
        </div>

        {/* TAB 1: PLATFORM HIERARCHY */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Tenant Layer</span>
                  <Building2 className="w-4 h-4 text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">42 Tenants</div>
                <p className="text-xs text-slate-500 mt-1">
                  {tenantMode === 'agency' ? 'Agency Mode: Agencies with isolated clients' : 'Direct Mode: Customer organizations with RBAC'}
                </p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                  <span>Isolated DB schemas/FKs</span>
                  <span className="text-emerald-600 font-medium">100% Isolated</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">AI Runtime</span>
                  <Bot className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">128 Active Agents</div>
                <p className="text-xs text-slate-500 mt-1">Multi-channel routing: WhatsApp, Web, Portal & API</p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                  <span>Knowledge Documents</span>
                  <span className="font-medium text-slate-800">1,490 chunks indexed</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">AI Gateway & Metering</span>
                  <Zap className="w-4 h-4 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">4 Providers Routed</div>
                <p className="text-xs text-slate-500 mt-1">OpenAI, Anthropic, Gemini, OpenRouter</p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                  <span>Credit Settlements</span>
                  <span className="text-emerald-600 font-medium">Atomic 2-Phase Hold</span>
                </div>
              </div>
            </div>

            {/* Target Hierarchy Blueprint Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-slate-900">Authoritative Platform Hierarchy</h3>
                  <p className="text-xs text-slate-500 mt-0.5">As defined in <code className="text-slate-700 bg-slate-100 px-1 py-0.5 rounded">docs/INNOTECH-PRODUCTION-SAAS-STRATEGY.md</code></p>
                </div>
                <span className="text-xs font-medium px-2.5 py-1 rounded bg-slate-100 text-slate-700">Production Model</span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-7 gap-3 items-stretch">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center flex flex-col justify-center">
                  <span className="text-[11px] font-semibold uppercase text-slate-400">Level 1</span>
                  <div className="font-bold text-slate-800 mt-1">InnoTech Platform</div>
                  <span className="text-[11px] text-slate-500 mt-1">Global Control Plane</span>
                </div>

                <div className="hidden lg:flex items-center justify-center text-slate-300">
                  <ArrowRight className="w-5 h-5" />
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center flex flex-col justify-center">
                  <span className="text-[11px] font-semibold uppercase text-blue-500">Level 2</span>
                  <div className="font-bold text-slate-800 mt-1">Tenant / Org</div>
                  <span className="text-[11px] text-slate-500 mt-1">Direct / Agency / Reseller</span>
                </div>

                <div className="hidden lg:flex items-center justify-center text-slate-300">
                  <ArrowRight className="w-5 h-5" />
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center flex flex-col justify-center">
                  <span className="text-[11px] font-semibold uppercase text-indigo-500">Level 3</span>
                  <div className="font-bold text-slate-800 mt-1">Clients & Agents</div>
                  <span className="text-[11px] text-slate-500 mt-1">Workspaces & Personas</span>
                </div>

                <div className="hidden lg:flex items-center justify-center text-slate-300">
                  <ArrowRight className="w-5 h-5" />
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center flex flex-col justify-center">
                  <span className="text-[11px] font-semibold uppercase text-emerald-500">Level 4</span>
                  <div className="font-bold text-slate-800 mt-1">AI Gateway</div>
                  <span className="text-[11px] text-slate-500 mt-1">Meters, Models, Credits</span>
                </div>
              </div>
            </div>

            {/* Architecture Principles Checklist */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Production Engineering Principles Status</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  { title: "Incremental Migration Only", status: "Active", desc: "FastAPI + Next.js preserved; zero rewrite." },
                  { title: "Server-Side Tenant Isolation", status: "Active", desc: "Never trust frontend tenant IDs or body slugs." },
                  { title: "Provider-Neutral AI Gateway", status: "Active", desc: "All provider logic moved behind unified adapter." },
                  { title: "Atomic Credit Settlement", status: "Active", desc: "Quota reservation before inference; settle after." },
                  { title: "Encrypted Secrets Only", status: "Active", desc: "Fernet encryption; no keys leaked to frontend." },
                  { title: "OpenAI-Compatible Public /v1", status: "Active", desc: "Standard /v1/chat/completions endpoints." },
                ].map((principle, idx) => (
                  <div key={idx} className="p-3.5 rounded-lg border border-slate-100 bg-slate-50/60 flex items-start gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-semibold text-slate-800">{principle.title}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{principle.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: AGENTS */}
        {activeTab === 'agents' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Active Agents</h3>
                <span className="text-xs text-slate-500 font-medium">{agents.length} configured</span>
              </div>
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedAgent === agent.id
                      ? 'bg-white border-slate-900 shadow-sm ring-1 ring-slate-900'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-slate-900">{agent.name}</span>
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {agent.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{agent.role}</p>
                  <div className="mt-3 flex items-center gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]">{agent.model}</span>
                    <span className="text-slate-400">·</span>
                    <span className="text-slate-500">{agent.channels.length} channels</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-bold text-slate-900">{currentAgent.name}</h3>
                  <p className="text-xs text-slate-500">{currentAgent.role}</p>
                </div>
                <span className="text-xs font-medium px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  ID: {currentAgent.id}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-[11px] text-slate-500 block">Routed Model</span>
                  <span className="text-xs font-semibold text-slate-800 font-mono">{currentAgent.model}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-[11px] text-slate-500 block">Knowledge Chunks</span>
                  <span className="text-xs font-semibold text-slate-800">{currentAgent.knowledgeDocs} verified docs</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-[11px] text-slate-500 block">Monthly Usage</span>
                  <span className="text-xs font-semibold text-slate-800">{currentAgent.monthlyTokens.toLocaleString()} tokens</span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Connected Channels</h4>
                <div className="flex flex-wrap gap-2">
                  {currentAgent.channels.map((ch, idx) => (
                    <span key={idx} className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-medium flex items-center gap-1.5">
                      <Radio className="w-3 h-3 text-emerald-600" />
                      {ch}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Execution Tools (HTTP & MCP)</h4>
                <div className="flex flex-wrap gap-2">
                  {currentAgent.tools.map((t, idx) => (
                    <span key={idx} className="text-xs px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 font-medium border border-blue-100 flex items-center gap-1.5">
                      <Zap className="w-3 h-3 text-blue-600" />
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-500">Security boundary: Tenant-isolated</span>
                <button
                  onClick={() => setActiveTab('api')}
                  className="text-xs font-medium text-slate-800 hover:text-black flex items-center gap-1"
                >
                  Invoke via /v1 API <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: AI GATEWAY */}
        {activeTab === 'gateway' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-slate-900">Provider-Neutral AI Gateway</h3>
                  <p className="text-xs text-slate-500">Normalizes models, parameters, tool-calling, and cost attribution across all vendors.</p>
                </div>
                <span className="text-xs font-medium px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Circuit Breakers Active
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                      <th className="py-3 px-3">Model</th>
                      <th className="py-3 px-3">Provider</th>
                      <th className="py-3 px-3">Input / 1M</th>
                      <th className="py-3 px-3">Output / 1M</th>
                      <th className="py-3 px-3">Context</th>
                      <th className="py-3 px-3">Avg Latency</th>
                      <th className="py-3 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {models.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-50/80">
                        <td className="py-3 px-3 font-semibold text-slate-900">{m.name}</td>
                        <td className="py-3 px-3 text-slate-600">{m.provider}</td>
                        <td className="py-3 px-3 font-mono text-slate-700">${m.inputCostPer1M.toFixed(2)}</td>
                        <td className="py-3 px-3 font-mono text-slate-700">${m.outputCostPer1M.toFixed(2)}</td>
                        <td className="py-3 px-3 text-slate-600">{m.contextWindow}</td>
                        <td className="py-3 px-3 text-slate-600">{m.latencyMs} ms</td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                            <Check className="w-3 h-3 text-emerald-600" />
                            Healthy
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <h4 className="text-sm font-semibold text-slate-900 mb-2">Platform-Managed vs BYOK</h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  The InnoTech AI Gateway dynamically resolves credentials:
                  direct and free users consume platform-managed wholesale model pools, while enterprise and agency tenants can attach their own encrypted keys (BYOK).
                </p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Encryption Standard</span>
                  <span className="font-mono text-slate-700">Fernet AES-128 CBC</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <h4 className="text-sm font-semibold text-slate-900 mb-2">Routing Policies</h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Define automated failover rules. When upstream provider error rates exceed 5% over 60 seconds, the circuit breaker shifts traffic to fallback models seamlessly.
                </p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Active Fallback</span>
                  <span className="font-medium text-emerald-700">OpenAI → Gemini 2.5</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: CREDITS */}
        {activeTab === 'credits' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Tenant Credit Balance</span>
                <div className="text-2xl font-bold text-slate-900 mt-2">14,250 Units</div>
                <p className="text-xs text-slate-500 mt-1">Equivalent to ~$142.50 in compute quota</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Current Month Consumed</span>
                <div className="text-2xl font-bold text-slate-900 mt-2">1,820 Units</div>
                <p className="text-xs text-slate-500 mt-1">Across 128 active agents</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Reservation Engine</span>
                <div className="text-2xl font-bold text-emerald-600 mt-2">2-Phase Commit</div>
                <p className="text-xs text-slate-500 mt-1">Zero balance overdraft guarantee</p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <h3 className="text-base font-semibold text-slate-900 mb-3">Double-Entry Credit Settlement Lifecycle</h3>
              <p className="text-xs text-slate-600 mb-4">
                Never mutate billing balances directly on frontend triggers. All AI inferences adhere to the strict 5-stage accounting pipeline:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-center">
                {[
                  { step: "1. Quota Check", desc: "Validate tenant positive balance" },
                  { step: "2. Atomic Reserve", desc: "Hold estimated max tokens" },
                  { step: "3. Gateway Execution", desc: "Stream tokens from provider" },
                  { step: "4. Settle & Release", desc: "Deduct actual, return delta" },
                  { step: "5. Audit Ledger", desc: "Immutable usage_event row" },
                ].map((s, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-xs font-bold text-slate-800">{s.step}</span>
                    <span className="text-[11px] text-slate-500 block mt-1">{s.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: PUBLIC API */}
        {activeTab === 'api' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div>
                <h3 className="text-base font-semibold text-slate-900">OpenAI-Compatible Public Gateway</h3>
                <p className="text-xs text-slate-500">Directly drop InnoTech into any OpenAI SDK client by pointing base URL to <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-800">/v1</code>.</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Target Endpoint</label>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1.5 rounded-md bg-emerald-100 text-emerald-800 font-mono text-xs font-bold">POST</span>
                  <input
                    type="text"
                    readOnly
                    value="/v1/chat/completions"
                    className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-md px-3 py-1.5 text-slate-700"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Interactive Test Prompt</label>
                <textarea
                  id="test-prompt-input"
                  rows={3}
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-md p-2.5 text-slate-800 focus:outline-none focus:ring-1 focus:ring-slate-900"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[11px] text-slate-500 font-mono">Header: Authorization: Bearer sk-innotech-...</span>
                <button
                  id="btn-simulate-execution"
                  onClick={handleSimulateExecution}
                  disabled={apiSimulating}
                  className="text-xs font-semibold bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors flex items-center gap-1.5"
                >
                  {apiSimulating ? (
                    <>
                      <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                      Routing to Gateway...
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      Execute Request
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="bg-slate-900 text-slate-100 rounded-xl p-6 shadow-xs flex flex-col">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                <span className="text-xs font-mono text-slate-400">Gateway Response Payload</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-slate-700">
                  HTTP 200 OK
                </span>
              </div>
              <pre className="text-[11px] font-mono leading-relaxed overflow-x-auto text-emerald-300 flex-1 scrollbar-none">
                {apiResponse || (
                  <span className="text-slate-500">// Click "Execute Request" to test the AI Gateway routing engine</span>
                )}
              </pre>
            </div>
          </div>
        )}

        {/* TAB 6: ROADMAP */}
        {activeTab === 'roadmap' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Execution Phase Order</h3>
              <p className="text-xs text-slate-500">Tracking implementation progress according to <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-800">docs/INNOTECH-PRODUCTION-SAAS-STRATEGY.md</code>.</p>
            </div>

            <div className="divide-y divide-slate-100">
              {[
                { phase: "Phase 0", title: "Audit & Baseline Freeze", status: "Completed", note: "Cloned upstream repo, audited 29 models, Alembic Head 0039, and established zero-breaking baseline." },
                { phase: "Phase 1", title: "Tenant Foundation & RBAC", status: "Ready to Implement", note: "Canonical Tenant, TenantMembership, roles, and get_current_principal dependencies." },
                { phase: "Phase 2", title: "AI Gateway Abstraction", status: "Pending", note: "ProviderRegistry, ModelRegistry, ProviderAdapter, routing, and circuit breakers." },
                { phase: "Phase 3", title: "Public API & OpenAI Compatibility", status: "Pending", note: "Stable /v1/chat/completions, /v1/models, /v1/responses with scoped API keys." },
                { phase: "Phase 4", title: "Usage & Credit Ledger", status: "Pending", note: "Atomic credit reservations, double-entry settlement, and usage events." },
                { phase: "Phase 5", title: "Plans & Billing", status: "Pending", note: "Entitlements engine, subscription lifecycle, and idempotent webhooks." },
                { phase: "Phase 6", title: "White-label & Brand Settings", status: "Pending", note: "Centralized BrandSettings, custom domain verification, and portal isolation." },
                { phase: "Phase 7", title: "Reseller Platform", status: "Pending", note: "Reseller tenant hierarchy, ancestry validation, and sub-tenant billing." },
                { phase: "Phase 8", title: "Scale Architecture", status: "Pending", note: "Redis task queues, object storage abstraction (S3/R2), and worker separation." },
                { phase: "Phase 9", title: "Production Certification", status: "Pending", note: "Full tenant isolation audit, SSRF verification, load testing, and disaster recovery." },
              ].map((p, idx) => (
                <div key={idx} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-start sm:items-center gap-3">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      p.status === 'Completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : p.status === 'Ready to Implement'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {p.phase}
                    </span>
                    <div>
                      <span className="text-xs font-semibold text-slate-800">{p.title}</span>
                      <p className="text-[11px] text-slate-500 mt-0.5">{p.note}</p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium shrink-0 ${
                    p.status === 'Completed'
                      ? 'text-emerald-600'
                      : p.status === 'Ready to Implement'
                      ? 'text-blue-600 font-semibold'
                      : 'text-slate-400'
                  }`}>
                    {p.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Bottom Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div>InnoTech AI Agent Factory · Multi-Tenant Agentic SaaS</div>
          <div className="flex items-center gap-4">
            <span>Alembic Head: 0039</span>
            <span>FastAPI Backend Active</span>
            <span>Port: 3000</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
