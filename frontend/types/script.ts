/**
 * Speech Script Type Definitions
 *
 * These types correspond to the backend Pydantic models in
 * backend/app/models/schemas.py
 *
 * Author: Claude Code
 * Date: 2026-01-22
 */

// ============================================================
// Script Generation Options
// ============================================================

export type ScriptTone = "professional" | "casual" | "technical";
export type ScriptAudience = "executive" | "technical" | "mixed";
export type ScriptDuration = "30s" | "2min" | "5min";
export type ScriptSection = "intro" | "body" | "conclusion" | "overall";
export type Priority = "high" | "medium" | "low";

export interface ScriptOptions {
  tone: ScriptTone;
  audience: ScriptAudience;
  focus_areas: string[];
}

// Default script options
export const DEFAULT_SCRIPT_OPTIONS: ScriptOptions = {
  tone: "professional",
  audience: "mixed",
  focus_areas: ["scalability", "performance"],
};

// ============================================================
// Script Content
// ============================================================

export interface ScriptContent {
  intro: string;
  body: string;
  conclusion: string;
  full_text: string;
}

// ============================================================
// Script Metadata
// ============================================================

export interface ScriptMetadata {
  created_at?: string;
  updated_at?: string;
  duration: ScriptDuration;
  word_count: number;
  rag_sources: string[];
  architecture_snapshot?: {
    nodes: any[];
    edges: any[];
  };
  version: number;
}

// ============================================================
// Script Draft
// ============================================================

export interface ScriptDraft {
  id: string;
  content: ScriptContent;
  metadata: ScriptMetadata;
  version: number;
}

// ============================================================
// Stream Events (Server-Sent Events)
// ============================================================

export type StreamEventType =
  | "CONTEXT_SEARCH"
  | "CONTEXT_FOUND"
  | "GENERATION_START"
  | "TOKEN"
  | "SECTION_COMPLETE"
  | "COMPLETE"
  | "ERROR";

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, any>;
}

// Specific event data types for better type safety

export interface ContextSearchEventData {
  status: string;
}

export interface ContextFoundEventData {
  chunks_found: number;
  patterns: string[];
  sources: string[];
}

export interface TokenEventData {
  token: string;
}

export interface SectionCompleteEventData {
  section: ScriptSection;
  text: string;
}

export interface CompleteEventData {
  script: ScriptContent;
  word_count: number;
  rag_sources: string[];
}

export interface ErrorEventData {
  error: string;
}

// ============================================================
// API Request/Response Types
// ============================================================

export interface EnhancedSpeechScriptRequest {
  nodes: any[];
  edges: any[];
  duration: ScriptDuration;
  options: ScriptOptions;
}

export interface SaveDraftResponse {
  script_id: string;
  version: number;
  saved_at: string;
  success: boolean;
}

export interface RefinedSectionResponse {
  script_id: string;
  section: ScriptSection;
  refined_text: string;
  changes_summary: string;
  success: boolean;
}

// ============================================================
// Improvement Suggestions
// ============================================================

export interface ImprovementSuggestion {
  section: ScriptSection;
  issue: string;
  suggestion: string;
  priority: Priority;
}

export interface ImprovementSuggestions {
  overall_score: number; // 1-10
  strengths: string[];
  weaknesses: string[];
  suggestions: ImprovementSuggestion[];
  success: boolean;
}

// ============================================================
// UI State Types
// ============================================================

export interface ScriptGeneratorState {
  // Generation state
  isGenerating: boolean;
  currentEvent: StreamEvent | null;
  generatedScript: ScriptContent | null;

  // Options
  duration: ScriptDuration;
  options: ScriptOptions;

  // Progress
  progressLog: StreamEvent[];
  sources: string[];
}

export interface ScriptEditorState {
  // Draft state
  draft: ScriptDraft | null;
  isLoading: boolean;
  isSaving: boolean;
  lastSaved: Date | null;

  // Editing state
  hasUnsavedChanges: boolean;
  editingSection: ScriptSection | null;

  // Refinement state
  isRefining: boolean;
  refineFeedback: string;

  // Suggestions
  suggestions: ImprovementSuggestions | null;
  loadingSuggestions: boolean;
}

// ============================================================
// Utility Functions
// ============================================================

/**
 * Get target word count for a given duration
 */
export function getTargetWordCount(duration: ScriptDuration): number {
  const targets = {
    "30s": 140,
    "2min": 600,
    "5min": 1500,
  };
  return targets[duration];
}

/**
 * Format duration as readable string
 */
export function formatDuration(duration: ScriptDuration): string {
  const labels = {
    "30s": "30秒",
    "2min": "2分钟",
    "5min": "5分钟",
  };
  return labels[duration];
}

/**
 * Format audience type as readable string
 */
export function formatAudience(audience: ScriptAudience): string {
  const labels = {
    executive: "高管层",
    technical: "技术团队",
    mixed: "混合受众",
  };
  return labels[audience];
}

/**
 * Format tone as readable string
 */
export function formatTone(tone: ScriptTone): string {
  const labels = {
    professional: "专业正式",
    casual: "轻松随意",
    technical: "技术深入",
  };
  return labels[tone];
}

/**
 * Format section name as readable string
 */
export function formatSection(section: ScriptSection): string {
  const labels = {
    intro: "开场",
    body: "主体",
    conclusion: "结尾",
    overall: "整体",
  };
  return labels[section];
}

/**
 * Get priority badge color
 */
export function getPriorityColor(priority: Priority): string {
  const colors = {
    high: "red",
    medium: "yellow",
    low: "green",
  };
  return colors[priority];
}

/**
 * Calculate estimated reading time in seconds
 */
export function estimateReadingTime(wordCount: number): number {
  // Average speaking rate: 150 words per minute
  const wordsPerSecond = 150 / 60;
  return Math.round(wordCount / wordsPerSecond);
}

/**
 * Format reading time as human-readable string
 */
export function formatReadingTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}秒`;
  } else {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  }
}

/**
 * Parse SSE event data
 */
export function parseSSEEvent(eventData: string): StreamEvent | null {
  try {
    // Remove "data: " prefix if present
    const jsonData = eventData.startsWith("data: ")
      ? eventData.slice(6)
      : eventData;

    return JSON.parse(jsonData) as StreamEvent;
  } catch (error) {
    console.error("Failed to parse SSE event:", error);
    return null;
  }
}

/**
 * Check if word count is within target range
 */
export function isWordCountInRange(
  wordCount: number,
  duration: ScriptDuration
): boolean {
  const target = getTargetWordCount(duration);
  const lowerBound = target * 0.8;
  const upperBound = target * 1.2;
  return wordCount >= lowerBound && wordCount <= upperBound;
}

/**
 * Get word count status (too short, good, too long)
 */
export function getWordCountStatus(
  wordCount: number,
  duration: ScriptDuration
): "too-short" | "good" | "too-long" {
  const target = getTargetWordCount(duration);

  // 放宽字数限制范围：允许50%-200%的范围
  if (wordCount < target * 0.5) {
    return "too-short";
  } else if (wordCount > target * 2.0) {
    return "too-long";
  } else {
    return "good";
  }
}

// ============================================================
// Quick Action Presets for Refinement
// ============================================================

export interface QuickRefinementAction {
  label: string;
  feedback: string;
  icon?: string;
}

export const QUICK_REFINEMENT_ACTIONS: QuickRefinementAction[] = [
  {
    label: "增加数据支撑",
    feedback: "增加具体的数据和案例，让内容更有说服力",
    icon: "📊",
  },
  {
    label: "增加类比",
    feedback: "使用更生动的类比和比喻，让技术概念更易懂",
    icon: "💡",
  },
  {
    label: "调整语气",
    feedback: "调整语气，让表达更自信和专业",
    icon: "🎯",
  },
  {
    label: "简化表达",
    feedback: "简化表达，去掉冗余内容",
    icon: "✂️",
  },
  {
    label: "增强开场",
    feedback: "开场需要更有吸引力，用问题或数据引起注意",
    icon: "🎬",
  },
  {
    label: "优化结尾",
    feedback: "结尾需要更有力度，增加明确的行动号召",
    icon: "🏁",
  },
];

// ============================================================
// Focus Areas for Suggestions
// ============================================================

export interface FocusArea {
  id: string;
  label: string;
  description: string;
}

export const FOCUS_AREAS: FocusArea[] = [
  {
    id: "clarity",
    label: "清晰度",
    description: "表达是否清晰易懂",
  },
  {
    id: "engagement",
    label: "吸引力",
    description: "内容是否引人入胜",
  },
  {
    id: "flow",
    label: "流畅度",
    description: "段落之间过渡是否自然",
  },
  {
    id: "data",
    label: "数据支撑",
    description: "是否有充分的数据和案例",
  },
  {
    id: "tone",
    label: "语气基调",
    description: "语气是否符合受众和场景",
  },
];

// ============================================================
// Suggestion History (for undo/redo)
// ============================================================

export interface SuggestionHistoryItem {
  id: string;
  timestamp: Date;
  section: ScriptSection;
  suggestion: ImprovementSuggestion;
  originalText: string;
  refinedText: string;
  status: "success" | "failed" | "reverted";
}

export interface SuggestionHistory {
  items: SuggestionHistoryItem[];
  canUndo: boolean;
}

// ============================================================
// Preview State (for suggestion preview before applying)
// ============================================================

export interface SuggestionPreview {
  suggestion: ImprovementSuggestion;
  originalText: string;
  previewText: string;
  isLoading: boolean;
}
