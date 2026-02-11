/**
 * 图片转换工具函数
 * 支持图片转Excalidraw和React Flow格式
 */

import { API_BASE_URL } from "@/lib/api-config";

export interface ExcalidrawElement {
  id: string;
  type: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  text?: string;
  strokeColor?: string;
  backgroundColor?: string;
  points?: number[][];
  [key: string]: any;
}

export interface ExcalidrawScene {
  elements: ExcalidrawElement[];
  appState?: {
    viewBackgroundColor?: string;
    [key: string]: any;
  };
  files?: Record<string, any>;
}

export interface ReactFlowDiagram {
  nodes: Array<{
    id: string;
    type: string;
    position: { x: number; y: number };
    data: {
      label: string;
      shape?: string;
      iconType?: string;
      color?: string;
    };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label?: string;
  }>;
}

/**
 * 将File转换为base64字符串
 */
export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
    reader.readAsDataURL(file);
  });
}

/**
 * 图片转Excalidraw格式
 */
export async function convertImageToExcalidraw(
  file: File,
  options: {
    prompt?: string;
    provider?: string;
    apiKey?: string;
    baseUrl?: string;
    modelName?: string;
    width?: number;
    height?: number;
  } = {}
): Promise<ExcalidrawScene> {
  // 转换为base64
  const base64Image = await fileToBase64(file);

  // 🔧 构造请求 - 使用传入的配置参数
  const requestData: any = {
    image_data: base64Image,
    prompt: options.prompt || "Convert this diagram to Excalidraw format. Preserve layout and all connections.",
    width: options.width || 1400,
    height: options.height || 900,
  };

  // 添加 AI 配置参数
  if (options.provider) requestData.provider = options.provider;
  if (options.apiKey) requestData.api_key = options.apiKey;
  if (options.baseUrl) requestData.base_url = options.baseUrl;
  if (options.modelName) requestData.model_name = options.modelName;

  // 调用API
  const response = await fetch(`${API_BASE_URL}/api/vision/generate-excalidraw`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.message || "Failed to generate Excalidraw scene");
  }

  return result.scene;
}

/**
 * 图片转React Flow格式
 */
export async function convertImageToReactFlow(
  file: File,
  options: {
    prompt?: string;
    provider?: string;
    apiKey?: string;
    baseUrl?: string;
    modelName?: string;
  } = {}
): Promise<ReactFlowDiagram> {
  // 转换为base64
  const base64Image = await fileToBase64(file);

  // 🔧 构造请求 - 使用传入的配置参数
  const requestData: any = {
    image_data: base64Image,
    prompt: options.prompt || "Convert this architecture diagram to Archboard React Flow format. Identify all components and connections.",
  };

  // 添加 AI 配置参数
  if (options.provider) requestData.provider = options.provider;
  if (options.apiKey) requestData.api_key = options.apiKey;
  if (options.baseUrl) requestData.base_url = options.baseUrl;
  if (options.modelName) requestData.model_name = options.modelName;

  // 调用API
  const response = await fetch(`${API_BASE_URL}/api/vision/generate-reactflow`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.message || "Failed to generate React Flow diagram");
  }

  return {
    nodes: result.nodes,
    edges: result.edges,
  };
}

/**
 * 验证图片文件
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // 检查文件类型
  const validTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: "Invalid file type. Only PNG, JPG, and WebP are supported.",
    };
  }

  // 检查文件大小（10MB限制）
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large. Maximum size is ${maxSize / 1024 / 1024}MB.`,
    };
  }

  return { valid: true };
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * 流式图片转Excalidraw格式
 * 支持实时接收元素并更新画板
 */
export async function* convertImageToExcalidrawStreaming(
  file: File,
  onProgress?: (message: string) => void,
  config?: {
    provider?: string;
    apiKey?: string;
    baseUrl?: string;
    modelName?: string;
  }
): AsyncGenerator<{
  type: "start_streaming" | "element" | "complete" | "error";
  total?: number;
  appState?: any;
  element?: ExcalidrawElement;
  message?: string;
  details?: any;
}> {
  // 转换为base64
  const base64Image = await fileToBase64(file);

  if (onProgress) {
    onProgress("Uploading image...");
  }

  // 🔧 构造请求 - 使用前端传入的配置参数
  const requestData: any = {
    image_data: base64Image,
    prompt: "Convert this diagram to Excalidraw format. Preserve layout and all connections.",
    width: 1400,
    height: 900,
  };

  // 如果传入了配置参数，添加到请求中
  if (config?.provider) requestData.provider = config.provider;
  if (config?.apiKey) requestData.api_key = config.apiKey;
  if (config?.baseUrl) requestData.base_url = config.baseUrl;
  if (config?.modelName) requestData.model_name = config.modelName;

  // 调用流式API
  const response = await fetch(`${API_BASE_URL}/api/vision/generate-excalidraw-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
    const errorDetails = JSON.stringify(errorData, null, 2);
    throw new Error(`${errorMessage}\n\n详细信息:\n${errorDetails}`);
  }

  if (!response.body) {
    throw new Error("Response body is null");
  }

  // 解析SSE流
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let elementCount = 0;
  let totalElements = 0;
  let appState: any = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // 保留最后一个不完整的行

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "init") {
              if (onProgress) {
                onProgress(data.message || "Starting...");
              }
            } else if (data.type === "error") {
              // 处理流式错误
              if (onProgress) {
                onProgress("Error occurred");
              }
              yield {
                type: "error",
                message: data.message || "Stream error occurred",
                details: data.details || data,
              };
              return; // 终止流
            } else if (data.type === "progress") {
              if (onProgress) {
                onProgress(data.message || "Processing...");
              }
            } else if (data.type === "element") {
              // 第一个元素时发送 start_streaming
              if (elementCount === 0 && !appState) {
                appState = { viewBackgroundColor: "#ffffff" };
                // 预估总元素数（后端会在完成时告诉我们实际数量）
                totalElements = 50; // 暂时估算
                yield {
                  type: "start_streaming",
                  total: totalElements,
                  appState,
                };
              }

              elementCount++;
              if (onProgress) {
                onProgress(`Processing element ${elementCount}...`);
              }

              yield {
                type: "element",
                element: data.element,
              };
            } else if (data.type === "complete") {
              if (onProgress) {
                onProgress(data.message || "Done!");
              }

              yield {
                type: "complete",
                message: data.message,
              };
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e, line);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

