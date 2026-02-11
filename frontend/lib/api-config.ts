/**
 * API Configuration
 * 统一管理所有后端 API 的 URL
 */

// 使用相对路径，通过 Next.js rewrites 代理到后端
// 在 next.config.js 中配置了 rewrites，会将 /api/* 代理到后端
// 本地开发: /api/* -> http://localhost:8003/api/*
// 生产环境: /api/* -> BACKEND_ORIGIN/api/*
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// API 端点 - 使用相对路径
export const API_ENDPOINTS = {
  // Health
  health: `${API_BASE_URL}/api/health`,

  // Models
  modelPresets: `${API_BASE_URL}/api/models/presets`,
  modelPreset: (id: string) => `${API_BASE_URL}/api/models/presets/${id}`,
  modelPresetFull: (id: string) => `${API_BASE_URL}/api/models/presets/${id}/full`,

  // Vision
  visionAnalyze: `${API_BASE_URL}/api/vision/analyze-flowchart`,

  // Mermaid
  mermaidParse: `${API_BASE_URL}/api/mermaid/parse`,
  mermaidToGraph: `${API_BASE_URL}/api/graph/to-mermaid`,

  // Chat Generator
  chatGenerator: `${API_BASE_URL}/api/chat-generator/generate`,
  chatGeneratorStream: `${API_BASE_URL}/api/chat-generator/generate-stream`,
  chatTemplates: `${API_BASE_URL}/api/chat-generator/templates`,

  // Excalidraw
  excalidrawGenerate: `${API_BASE_URL}/api/excalidraw/generate`,

  // Export
  exportPPT: `${API_BASE_URL}/api/export/ppt`,
  exportSlidev: `${API_BASE_URL}/api/export/slidev`,
  exportScript: `${API_BASE_URL}/api/export/script`,

  // RAG (if implemented)
  ragUpload: `${API_BASE_URL}/api/rag/upload`,
  ragSearch: `${API_BASE_URL}/api/rag/search`,
};

// 帮助函数：检查后端是否可用
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(API_ENDPOINTS.health, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

// 帮助函数：获取完整的 API URL
export function getApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
