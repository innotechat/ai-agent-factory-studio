export type TemplateCategory = 'All' | 'Support' | 'Sales' | 'Operations' | 'Industry';

export interface TemplateToolConfig {
  id: string;
  name: string;
  type: 'Knowledge Base' | 'HTTP Webhook' | 'MCP Server' | 'System Action' | 'Internal Function' | 'Semantic RAG' | string;
  description: string;
  endpointOrMethod: string;
  parametersSummary?: string;
  requiredEnvVars?: string[];
  isOptional?: boolean;
  enabledByDefault?: boolean;
}

export interface AgentTemplate {
  id: string;
  category: 'Support' | 'Sales' | 'Operations' | 'Industry' | string;
  name: string;
  tagline: string;
  description: string;
  iconName: string;
  recommendedModel: string;
  recommendedProvider: 'gemini' | 'openai' | 'anthropic' | 'openrouter';
  providerLabel: string;
  estimatedLatency: string;
  contextWindow: string;
  prefilledInstructions: string;
  suggestedRole?: string;
  prefilledTone?: string;
  suggestedTone?: string;
  tools: TemplateToolConfig[];
  suggestedChannels: string[];
  guardrails: string[];
  samplePrompts: string[];
  sampleDialogue: {
    user: string;
    assistant: string;
    toolCallExecuted?: {
      name: string;
      args?: Record<string, any> | string;
      input?: Record<string, any> | string;
      result: string;
    };
  };
}

export interface BootstrappedAgentPayload {
  templateOriginId: string;
  name: string;
  role: string;
  model: string;
  provider: 'openai' | 'anthropic' | 'gemini' | 'openrouter';
  instructions: string;
  tone: string;
  tools: string[];
  channels: string[];
  guardrails: string[];
  maxTokensPerResponse?: number;
  temperature?: number;
}
