/**
 * AI Provider 默认配置
 *
 * 定义各个 AI 提供商的默认参数，包括：
 * - displayName: 显示名称
 * - baseUrl: API 基础 URL
 * - modelName: 默认模型名称
 * - description: 描述信息
 * - apiKey: 预配置的测试 API Key（可选）
 */

type ProviderKey = "gemini" | "openai" | "claude" | "siliconflow" | "custom";

interface ProviderConfig {
  provider: ProviderKey;
  displayName: string;
  baseUrl: string;
  modelName: string;
  description: string;
  apiKey?: string; // 可选的预配置 API Key
}

export const PROVIDER_DEFAULTS: Record<ProviderKey, ProviderConfig> = {
  gemini: {
    provider: "gemini",
    displayName: "Google Gemini",
    baseUrl: "https://generativelanguage.googleapis.com",
    modelName: "gemini-2.0-flash-exp",
    description: "Google 最新的多模态 AI 模型，支持视觉分析和流式生成",
    apiKey: "", // 用户需自行配置
  },
  openai: {
    provider: "openai",
    displayName: "OpenAI GPT",
    baseUrl: "https://api.openai.com/v1",
    modelName: "gpt-4o-mini",
    description: "OpenAI GPT-4 系列模型，强大的通用 AI 能力",
    apiKey: "", // 用户需自行配置
  },
  claude: {
    provider: "claude",
    displayName: "Anthropic Claude",
    baseUrl: "https://api.anthropic.com",
    modelName: "claude-3-5-sonnet-20241022",
    description: "Anthropic Claude 3.5 Sonnet，擅长长文本分析和推理",
    apiKey: "", // 用户需自行配置
  },
  siliconflow: {
    provider: "siliconflow",
    displayName: "SiliconFlow",
    baseUrl: "https://api.siliconflow.cn/v1",
    modelName: "Qwen/Qwen2.5-14B-Instruct",
    description: "国内 AI 推理平台，提供高性价比的模型服务",
    apiKey: "", // 用户需自行配置
  },
  custom: {
    provider: "custom",
    displayName: "Linkflow (Claude Sonnet 4.5)",
    baseUrl: "https://www.linkflow.run/v1",
    modelName: "claude-sonnet-4-5-20250929",
    description: "Linkflow 提供的 Claude Sonnet 4.5 模型，超大 token 额度",
    apiKey: "sk-7oflvgMRXPZe0skck0qIqsFuDSvOBKiMqqGiC0Sx9gzAsALh",
  },
};

/**
 * 获取所有 provider 选项（包含详细配置）
 * 用于在 UI 中展示可用的 AI 提供商列表
 */
export function getAllProviderOptions(): ProviderConfig[] {
  return Object.values(PROVIDER_DEFAULTS);
}

/**
 * 根据 provider key 获取默认配置
 */
export function getProviderDefaults(provider: ProviderKey): ProviderConfig {
  return PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.gemini;
}

/**
 * 检查是否为有效的 provider
 */
export function isValidProvider(provider: string): provider is ProviderKey {
  return provider in PROVIDER_DEFAULTS;
}
