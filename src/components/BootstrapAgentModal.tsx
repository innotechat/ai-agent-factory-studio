import React, { useState } from 'react';
import {
  X,
  Bot,
  Zap,
  Check,
  RotateCcw,
  Sparkles,
  Shield,
  Layers,
  Radio,
  ExternalLink,
  ChevronRight,
  Terminal,
  Cpu,
  ArrowRight,
  Sliders,
  CheckCircle2,
  FileCode2,
  AlertCircle
} from 'lucide-react';
import { AgentTemplate, BootstrappedAgentPayload, TemplateToolConfig } from '../types/templates';

interface BootstrapAgentModalProps {
  template: AgentTemplate | null;
  isOpen: boolean;
  onClose: () => void;
  onBootstrapSuccess: (newAgent: BootstrappedAgentPayload) => void;
}

export const BootstrapAgentModal: React.FC<BootstrapAgentModalProps> = ({
  template,
  isOpen,
  onClose,
  onBootstrapSuccess,
}) => {
  if (!isOpen || !template) return null;

  // Form State
  const [activeStep, setActiveStep] = useState<'configure' | 'preview'>('configure');
  const [agentName, setAgentName] = useState(template.name);
  const [agentRole, setAgentRole] = useState(template.tagline);
  const [selectedModel, setSelectedModel] = useState(template.recommendedModel);
  const [selectedProvider, setSelectedProvider] = useState(template.recommendedProvider);
  const [instructions, setInstructions] = useState(template.prefilledInstructions);
  const [tone, setTone] = useState(template.prefilledTone);
  const [enabledToolIds, setEnabledToolIds] = useState<string[]>(
    template.tools.filter(t => t.enabledByDefault).map(t => t.id)
  );
  const [selectedChannels, setSelectedChannels] = useState<string[]>(template.suggestedChannels);
  const [guardrails, setGuardrails] = useState<string[]>(template.guardrails);
  const [newGuardrailInput, setNewGuardrailInput] = useState('');

  // Execution state
  const [isBootstrapping, setIsBootstrapping] = useState(false);
  const [bootstrapStepText, setBootstrapStepText] = useState('');

  const toggleTool = (toolId: string) => {
    setEnabledToolIds(prev =>
      prev.includes(toolId) ? prev.filter(id => id !== toolId) : [...prev, toolId]
    );
  };

  const toggleChannel = (channel: string) => {
    setSelectedChannels(prev =>
      prev.includes(channel) ? prev.filter(c => c !== channel) : [...prev, channel]
    );
  };

  const handleResetInstructions = () => {
    setInstructions(template.prefilledInstructions);
    setTone(template.prefilledTone);
  };

  const handleAddGuardrail = () => {
    if (newGuardrailInput.trim()) {
      setGuardrails([...guardrails, newGuardrailInput.trim()]);
      setNewGuardrailInput('');
    }
  };

  const handleRemoveGuardrail = (index: number) => {
    setGuardrails(guardrails.filter((_, idx) => idx !== index));
  };

  const handleExecuteBootstrap = () => {
    setIsBootstrapping(true);
    setBootstrapStepText('Validating tenant workspace...');

    setTimeout(() => {
      setBootstrapStepText('Generating encrypted tool credentials & MCP contracts...');
      setTimeout(() => {
        setBootstrapStepText('Compiling system prompt & routing rules...');
        setTimeout(() => {
          setIsBootstrapping(false);
          const payload: BootstrappedAgentPayload = {
            name: agentName,
            role: agentRole,
            model: selectedModel,
            provider: selectedProvider,
            instructions: instructions,
            tone: tone,
            tools: template.tools
              .filter(t => enabledToolIds.includes(t.id))
              .map(t => t.name),
            channels: selectedChannels,
            guardrails: guardrails,
            templateOriginId: template.id,
          };
          onBootstrapSuccess(payload);
          onClose();
        }, 400);
      }, 400);
    }, 400);
  };

  const availableModels = [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'gemini' as const, note: 'Ultra-low latency (240ms), 1M window' },
    { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', provider: 'openai' as const, note: 'High precision, cost-effective (128k)' },
    { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'anthropic' as const, note: 'Deep reasoning & tool calling (200k)' },
    { id: 'deepseek-r1', name: 'DeepSeek R1', provider: 'openrouter' as const, note: 'Open weights via OpenRouter' },
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 md:p-6 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">
                  Bootstrap New Agent
                </h2>
                <span className="text-xs text-slate-500 font-medium">
                  from {template.name}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Customize pre-filled instructions, tool bindings, and routing policies before deploying to tenant.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Tabs */}
        <div className="px-6 pt-3 border-b border-slate-100 flex items-center gap-4 text-xs font-medium">
          <button
            onClick={() => setActiveStep('configure')}
            className={`pb-2.5 border-b-2 transition-colors flex items-center gap-1.5 ${
              activeStep === 'configure'
                ? 'border-slate-900 text-slate-900 font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            1. Configure Identity & Tools
          </button>
          <button
            onClick={() => setActiveStep('preview')}
            className={`pb-2.5 border-b-2 transition-colors flex items-center gap-1.5 ${
              activeStep === 'preview'
                ? 'border-slate-900 text-slate-900 font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            2. System Prompt & Dialogue Preview
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-800">

          {activeStep === 'configure' ? (
            <div className="space-y-6">
              {/* Agent Identity Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Agent Name
                  </label>
                  <input
                    type="text"
                    value={agentName}
                    onChange={(e) => setAgentName(e.target.value)}
                    className="w-full text-xs font-medium bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                    placeholder="e.g., Tier 1 InnoTech Support Dispatcher"
                  />
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Visible to customers and in chat transcripts
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Persona & Role Definition
                  </label>
                  <input
                    type="text"
                    value={agentRole}
                    onChange={(e) => setAgentRole(e.target.value)}
                    className="w-full text-xs font-medium bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                    placeholder="e.g., Triage, SLA prioritization, and booking"
                  />
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Internal role description for multi-agent routing
                  </span>
                </div>
              </div>

              {/* Target Model Selection */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-800">
                      Primary AI Model & Gateway Provider
                    </label>
                    <p className="text-[11px] text-slate-500">
                      Pre-selected based on template requirements. Fallback routing will be configured automatically.
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                    Template recommended: {template.recommendedModel}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {availableModels.map((m) => (
                    <div
                      key={m.id}
                      onClick={() => {
                        setSelectedModel(m.id);
                        setSelectedProvider(m.provider);
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start gap-3 ${
                        selectedModel === m.id
                          ? 'bg-white border-slate-900 ring-1 ring-slate-900 shadow-xs'
                          : 'bg-white/80 border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <Cpu className={`w-4 h-4 mt-0.5 shrink-0 ${selectedModel === m.id ? 'text-slate-900' : 'text-slate-400'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900">{m.name}</span>
                          <span className="text-[10px] font-mono uppercase text-slate-500">{m.provider}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{m.note}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pre-configured Tools Selection */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Tool Integrations ({enabledToolIds.length}/{template.tools.length} Enabled)
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      These HTTP endpoints and MCP servers will be registered for tool execution in this agent.
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  {template.tools.map((tool) => {
                    const isChecked = enabledToolIds.includes(tool.id);
                    return (
                      <div
                        key={tool.id}
                        onClick={() => toggleTool(tool.id)}
                        className={`p-3 rounded-xl border cursor-pointer transition-all flex items-start gap-3.5 ${
                          isChecked
                            ? 'bg-white border-slate-300 shadow-2xs'
                            : 'bg-slate-50/70 border-slate-200 opacity-60'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900 cursor-pointer"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900">{tool.name}</span>
                            <span className="text-[10px] font-medium text-slate-500">
                              {tool.type}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 mt-0.5">{tool.description}</p>
                          <div className="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-slate-500">
                            <span className="truncate max-w-md bg-slate-100 px-1.5 py-0.5 rounded">
                              {tool.endpointOrMethod}
                            </span>
                            {tool.requiredEnvVars && (
                              <span className="text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded text-[10px]">
                                Requires {tool.requiredEnvVars.join(', ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Connected Communication Channels */}
              <div>
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Active Surface Channels
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    'Webchat Widget',
                    'WhatsApp Cloud',
                    'WhatsApp QR (Baileys)',
                    'Client Portal',
                    'Email Gateway',
                    'Slack Connect',
                    'REST API (/v1)'
                  ].map((ch) => {
                    const active = selectedChannels.includes(ch);
                    return (
                      <button
                        type="button"
                        key={ch}
                        onClick={() => toggleChannel(ch)}
                        className={`p-2.5 rounded-lg border text-xs font-medium text-left flex items-center gap-2 transition-colors ${
                          active
                            ? 'bg-slate-900 text-white border-slate-900'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <Radio className={`w-3.5 h-3.5 ${active ? 'text-emerald-400' : 'text-slate-400'}`} />
                        <span className="truncate">{ch}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Safety Guardrails */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-slate-700" />
                    <span className="text-xs font-bold text-slate-800">Operational Guardrails</span>
                  </div>
                  <span className="text-[11px] text-slate-500">Injected into system instructions</span>
                </div>

                <div className="space-y-1.5">
                  {guardrails.map((rule, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs bg-white px-3 py-1.5 rounded-md border border-slate-200">
                      <span className="text-slate-700">· {rule}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveGuardrail(idx)}
                        className="text-slate-400 hover:text-red-600 text-xs ml-2"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={newGuardrailInput}
                    onChange={(e) => setNewGuardrailInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddGuardrail();
                      }
                    }}
                    placeholder="Add custom rule (e.g. Always request account ID before issuing refunds)"
                    className="flex-1 text-xs bg-white border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-900"
                  />
                  <button
                    type="button"
                    onClick={handleAddGuardrail}
                    className="text-xs font-medium px-3 py-1.5 bg-slate-200 hover:bg-slate-300 rounded-md transition-colors text-slate-800"
                  >
                    Add Rule
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Tab 2: System Prompt & Dialogue Preview */
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Pre-filled System Instructions
                    </label>
                    <p className="text-[11px] text-slate-500">
                      This system prompt steers persona behavior, workflow execution, tool triggers, and guardrails.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleResetInstructions}
                    className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Reset to Template Default
                  </button>
                </div>

                <textarea
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  rows={13}
                  className="w-full font-mono text-xs p-3.5 bg-slate-950 text-slate-100 rounded-xl border border-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-700 leading-relaxed"
                />
                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                  <span>~{Math.round(instructions.length / 4)} estimated prompt tokens</span>
                  <span>Markdown & Tool schema variables supported</span>
                </div>
              </div>

              {/* Sample Dialogue & Tool Execution Inspection */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Simulated Conversation Walkthrough
                  </h4>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Template Verification Dialogue
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  {/* User message */}
                  <div className="flex items-start gap-2.5">
                    <span className="font-semibold text-slate-500 shrink-0 mt-0.5">User:</span>
                    <div className="bg-white p-2.5 rounded-lg border border-slate-200 text-slate-800 shadow-2xs">
                      {template.sampleDialogue.user}
                    </div>
                  </div>

                  {/* Tool Execution */}
                  {template.sampleDialogue.toolCallExecuted && (
                    <div className="ml-8 p-2.5 rounded-lg bg-slate-900 text-slate-200 font-mono text-[11px] border border-slate-800 space-y-1">
                      <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                        <Terminal className="w-3 h-3" />
                        <span>Tool Invoked: {template.sampleDialogue.toolCallExecuted.name}()</span>
                      </div>
                      <div className="text-slate-400">
                        Input: {template.sampleDialogue.toolCallExecuted.input}
                      </div>
                      <div className="text-slate-300">
                        Output: {template.sampleDialogue.toolCallExecuted.result}
                      </div>
                    </div>
                  )}

                  {/* Assistant response */}
                  <div className="flex items-start gap-2.5">
                    <span className="font-semibold text-blue-600 shrink-0 mt-0.5">Agent:</span>
                    <div className="bg-blue-50/80 p-2.5 rounded-lg border border-blue-100 text-slate-800 whitespace-pre-line">
                      {template.sampleDialogue.assistant}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Tenant isolation active · 0 credentials exposed</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
            >
              Cancel
            </button>

            {activeStep === 'configure' ? (
              <button
                type="button"
                onClick={() => setActiveStep('preview')}
                className="px-4 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg transition-colors flex items-center gap-1.5"
              >
                Review Instructions <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setActiveStep('configure')}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
              >
                Back to Config
              </button>
            )}

            <button
              type="button"
              disabled={isBootstrapping || !agentName.trim()}
              onClick={handleExecuteBootstrap}
              className="px-5 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-all shadow-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isBootstrapping ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>{bootstrapStepText || 'Bootstrapping...'}</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>Bootstrap Agent</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
