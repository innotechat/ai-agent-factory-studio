import React, { useState, useMemo } from 'react';
import {
  Search,
  Bot,
  Zap,
  Check,
  ChevronRight,
  Sparkles,
  ArrowRight,
  Shield,
  Radio,
  ExternalLink,
  Code2,
  Cpu,
  Layers,
  Terminal,
  X,
  FileText,
  Headphones,
  TrendingUp,
  Calendar,
  Stethoscope,
  ShoppingBag,
  LifeBuoy,
  Plus
} from 'lucide-react';
import { AgentTemplate, BootstrappedAgentPayload, TemplateCategory } from '../types/templates';
import { AGENT_TEMPLATES } from '../data/agentTemplates';
import { BootstrapAgentModal } from './BootstrapAgentModal';

interface TemplateSelectionScreenProps {
  onAgentBootstrapped: (newAgent: BootstrappedAgentPayload) => void;
  onCancelToAgents?: () => void;
}

export const TemplateSelectionScreen: React.FC<TemplateSelectionScreenProps> = ({
  onAgentBootstrapped,
  onCancelToAgents,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [providerFilter, setProviderFilter] = useState<string>('all');
  const [inspectingTemplate, setInspectingTemplate] = useState<AgentTemplate | null>(null);
  const [bootstrappingTemplate, setBootstrappingTemplate] = useState<AgentTemplate | null>(null);

  // Category counts
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {
      All: AGENT_TEMPLATES.length,
      Support: 0,
      Sales: 0,
      Operations: 0,
      Industry: 0,
    };
    AGENT_TEMPLATES.forEach(t => {
      counts[t.category] = (counts[t.category] || 0) + 1;
    });
    return counts;
  }, []);

  // Filtered templates
  const filteredTemplates = useMemo(() => {
    return AGENT_TEMPLATES.filter((tpl) => {
      // Category match
      if (selectedCategory !== 'All' && tpl.category !== selectedCategory) {
        return false;
      }
      // Provider filter
      if (providerFilter !== 'all' && tpl.recommendedProvider !== providerFilter) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = tpl.name.toLowerCase().includes(q);
        const matchesTagline = tpl.tagline.toLowerCase().includes(q);
        const matchesDesc = tpl.description.toLowerCase().includes(q);
        const matchesTool = tpl.tools.some(tool => tool.name.toLowerCase().includes(q) || tool.type.toLowerCase().includes(q));
        const matchesModel = tpl.recommendedModel.toLowerCase().includes(q);
        return matchesName || matchesTagline || matchesDesc || matchesTool || matchesModel;
      }
      return true;
    });
  }, [selectedCategory, providerFilter, searchQuery]);

  const getTemplateIcon = (iconName: string) => {
    switch (iconName) {
      case 'Headphones':
        return <Headphones className="w-5 h-5 text-indigo-600" />;
      case 'LifeBuoy':
        return <LifeBuoy className="w-5 h-5 text-blue-600" />;
      case 'TrendingUp':
        return <TrendingUp className="w-5 h-5 text-emerald-600" />;
      case 'Calendar':
        return <Calendar className="w-5 h-5 text-amber-600" />;
      case 'FileText':
        return <FileText className="w-5 h-5 text-violet-600" />;
      case 'Cpu':
        return <Cpu className="w-5 h-5 text-rose-600" />;
      case 'Stethoscope':
        return <Stethoscope className="w-5 h-5 text-teal-600" />;
      case 'ShoppingBag':
        return <ShoppingBag className="w-5 h-5 text-orange-600" />;
      default:
        return <Bot className="w-5 h-5 text-slate-700" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5 text-xs text-slate-500">
            <span>Agent Studio</span>
            <span aria-hidden="true">·</span>
            <span>Bootstrap Engine</span>
            <span aria-hidden="true">·</span>
            <span className="text-slate-800 font-medium">Production Templates</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            AI Agent Template Catalog
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-2xl mt-1 leading-relaxed">
            Jumpstart deployment with battle-tested templates for Support, Sales, and Operations. Each template comes pre-wired with production system prompts, verified HTTP/MCP tools, and model routing policies.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          {onCancelToAgents && (
            <button
              onClick={onCancelToAgents}
              className="px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition-colors"
            >
              Return to Runtime
            </button>
          )}
          <div className="flex items-center gap-2 text-xs font-medium text-slate-600 bg-slate-100 p-1.5 rounded-lg">
            <span className="bg-white px-2.5 py-1 rounded shadow-2xs text-slate-900 font-semibold flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-blue-600" />
              {AGENT_TEMPLATES.length} Canonical Blueprints
            </span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          
          {/* Category Tabs (Segmented Buttons) */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg overflow-x-auto scrollbar-none">
            {(['All', 'Support', 'Sales', 'Operations', 'Industry'] as TemplateCategory[]).map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  selectedCategory === cat
                    ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <span>{cat === 'All' ? 'All Templates' : cat}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${selectedCategory === cat ? 'bg-slate-100 text-slate-700' : 'text-slate-400'}`}>
                  {categoryCounts[cat]}
                </span>
              </button>
            ))}
          </div>

          {/* Search Input & Provider Filter */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1 sm:w-64">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates, tools..."
                className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            <select
              value={providerFilter}
              onChange={(e) => setProviderFilter(e.target.value)}
              className="text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              <option value="all">All Providers</option>
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>
        </div>

        {/* Quick Highlights / Category Helper */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
          <div>
            Showing <strong className="text-slate-800">{filteredTemplates.length}</strong> {filteredTemplates.length === 1 ? 'template' : 'templates'}
            {selectedCategory !== 'All' && <span> in <strong className="text-slate-800">{selectedCategory}</strong></span>}
            {searchQuery && <span> matching "<span className="text-slate-800">{searchQuery}</span>"</span>}
          </div>
          <div className="flex items-center gap-3 hidden sm:flex text-[11px]">
            <span>✓ Pre-filled system prompts</span>
            <span aria-hidden="true">·</span>
            <span>✓ Verified MCP & HTTP tools</span>
            <span aria-hidden="true">·</span>
            <span>✓ Multi-channel binding</span>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      {filteredTemplates.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
          <Bot className="w-8 h-8 text-slate-400 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-800">No templates match your criteria</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Try adjusting your search terms or select "All Templates" to explore all available blueprints.
          </p>
          <button
            onClick={() => {
              setSelectedCategory('All');
              setSearchQuery('');
              setProviderFilter('all');
            }}
            className="text-xs font-medium text-slate-900 underline hover:text-black mt-2"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredTemplates.map((template) => {
            return (
              <div
                key={template.id}
                className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between group"
              >
                {/* Top Section */}
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0 group-hover:bg-slate-100 transition-colors">
                      {getTemplateIcon(template.iconName)}
                    </div>
                    {/* Unboxed Category Metadata (Frontend Constitution compliant) */}
                    <div className="text-right">
                      <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                        {template.category}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {template.estimatedLatency}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {template.name}
                    </h3>
                    <p className="text-xs text-slate-500 font-medium mt-0.5">
                      {template.tagline}
                    </p>
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                    {template.description}
                  </p>

                  {/* Model & Latency Specification */}
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                    <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-700">
                      <Cpu className="w-3.5 h-3.5 text-slate-400" />
                      <span>{template.recommendedModel}</span>
                    </div>
                    <span className="text-[11px] text-slate-400">
                      {template.contextWindow}
                    </span>
                  </div>

                  {/* Pre-configured Tools List */}
                  <div className="space-y-1.5">
                    <div className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider flex items-center justify-between">
                      <span>Pre-configured Tools</span>
                      <span className="font-normal text-slate-400">{template.tools.length} available</span>
                    </div>
                    <div className="space-y-1">
                      {template.tools.slice(0, 3).map((tool) => (
                        <div
                          key={tool.id}
                          className="flex items-center justify-between text-[11px] px-2 py-1 rounded bg-slate-50 border border-slate-100 text-slate-700"
                        >
                          <span className="truncate max-w-[170px] font-medium">{tool.name}</span>
                          <span className="text-[10px] text-slate-400 shrink-0 font-mono">{tool.type}</span>
                        </div>
                      ))}
                      {template.tools.length > 3 && (
                        <div className="text-[10px] text-slate-400 pl-1">
                          +{template.tools.length - 3} additional tool schemas
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sample Query snippet */}
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-[11px] text-slate-600 italic">
                    "{template.samplePrompts[0]}"
                  </div>
                </div>

                {/* Bottom Card Actions */}
                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center gap-2">
                  <button
                    onClick={() => setInspectingTemplate(template)}
                    className="flex-1 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors flex items-center justify-center gap-1"
                  >
                    Quick Preview
                  </button>

                  <button
                    onClick={() => setBootstrappingTemplate(template)}
                    className="flex-1 px-3 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-2xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                    <span>Bootstrap</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* QUICK PREVIEW DRAWER (SLIDE-OVER / MODAL) */}
      {inspectingTemplate && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 md:p-6 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden text-slate-900">
            
            {/* Drawer Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center">
                  {getTemplateIcon(inspectingTemplate.iconName)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">
                      {inspectingTemplate.name}
                    </h3>
                    <span className="text-xs text-slate-500 font-medium">
                      · {inspectingTemplate.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">{inspectingTemplate.tagline}</p>
                </div>
              </div>

              <button
                onClick={() => setInspectingTemplate(null)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              <div>
                <h4 className="font-bold text-slate-800 uppercase tracking-wider mb-1 text-[11px]">
                  Template Overview
                </h4>
                <p className="text-slate-600 leading-relaxed">
                  {inspectingTemplate.description}
                </p>
              </div>

              {/* Recommended Infrastructure */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Recommended Model</span>
                  <span className="font-bold text-slate-800 font-mono mt-0.5 block">{inspectingTemplate.recommendedModel}</span>
                  <span className="text-slate-500 text-[10px]">{inspectingTemplate.providerLabel}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Latency Profile</span>
                  <span className="font-bold text-slate-800 mt-0.5 block">{inspectingTemplate.estimatedLatency}</span>
                  <span className="text-slate-500 text-[10px]">{inspectingTemplate.contextWindow} context</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Default Channels</span>
                  <span className="font-bold text-slate-800 mt-0.5 block">{inspectingTemplate.suggestedChannels.length} surfaces</span>
                  <span className="text-slate-500 text-[10px] truncate block">{inspectingTemplate.suggestedChannels[0]}</span>
                </div>
              </div>

              {/* Pre-filled System Instructions */}
              <div>
                <h4 className="font-bold text-slate-800 uppercase tracking-wider mb-1.5 text-[11px] flex items-center justify-between">
                  <span>Pre-filled System Instructions</span>
                  <span className="font-normal text-slate-400 font-mono">system_prompt</span>
                </h4>
                <div className="p-3.5 bg-slate-950 text-slate-200 rounded-xl font-mono text-[11px] max-h-48 overflow-y-auto leading-relaxed border border-slate-800 whitespace-pre-wrap">
                  {inspectingTemplate.prefilledInstructions}
                </div>
              </div>

              {/* Tools Breakdown */}
              <div>
                <h4 className="font-bold text-slate-800 uppercase tracking-wider mb-2 text-[11px]">
                  Tool Execution Contracts ({inspectingTemplate.tools.length})
                </h4>
                <div className="space-y-2">
                  {inspectingTemplate.tools.map((tool) => (
                    <div key={tool.id} className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{tool.name}</span>
                        <span className="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 bg-white rounded border border-slate-200">{tool.type}</span>
                      </div>
                      <p className="text-slate-600 text-[11px]">{tool.description}</p>
                      <div className="font-mono text-[10px] text-slate-500 truncate pt-1">
                        Endpoint: {tool.endpointOrMethod}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Simulated Dialogue */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                  Sample Dialogue & Tool Calling Trace
                </h4>
                <div className="space-y-2 text-xs">
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                    <strong className="text-slate-500 block text-[10px] uppercase">User Prompt:</strong>
                    <div className="text-slate-800 mt-0.5">{inspectingTemplate.sampleDialogue.user}</div>
                  </div>
                  {inspectingTemplate.sampleDialogue.toolCallExecuted && (
                    <div className="p-2.5 rounded-lg bg-slate-900 text-slate-200 font-mono text-[11px]">
                      <div className="text-emerald-400 font-semibold">
                        ⚡ Tool Executed: {inspectingTemplate.sampleDialogue.toolCallExecuted.name}
                      </div>
                      <div className="text-slate-400 text-[10px] mt-0.5">
                        Result: {inspectingTemplate.sampleDialogue.toolCallExecuted.result}
                      </div>
                    </div>
                  )}
                  <div className="bg-blue-50/80 p-2.5 rounded-lg border border-blue-100">
                    <strong className="text-blue-600 block text-[10px] uppercase">Assistant Reply:</strong>
                    <div className="text-slate-800 mt-0.5 whitespace-pre-line">{inspectingTemplate.sampleDialogue.assistant}</div>
                  </div>
                </div>
              </div>

              {/* Guardrails */}
              <div>
                <h4 className="font-bold text-slate-800 uppercase tracking-wider mb-1.5 text-[11px]">
                  Default Safety Guardrails
                </h4>
                <ul className="space-y-1 text-slate-600">
                  {inspectingTemplate.guardrails.map((rule, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-slate-400">·</span>
                      <span>{rule}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
              <button
                onClick={() => setInspectingTemplate(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
              >
                Close Preview
              </button>

              <button
                onClick={() => {
                  const t = inspectingTemplate;
                  setInspectingTemplate(null);
                  setBootstrappingTemplate(t);
                }}
                className="px-5 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-2 shadow-xs"
              >
                <Sparkles className="w-4 h-4 text-amber-300" />
                <span>Configure & Bootstrap This Agent</span>
              </button>
            </div>

          </div>
        </div>
      )}

      {/* BOOTSTRAP MODAL WIZARD */}
      <BootstrapAgentModal
        template={bootstrappingTemplate}
        isOpen={Boolean(bootstrappingTemplate)}
        onClose={() => setBootstrappingTemplate(null)}
        onBootstrapSuccess={onAgentBootstrapped}
      />
    </div>
  );
};
