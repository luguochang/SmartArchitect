/**
 * 图片转换工具函数
 * 支持图片转Excalidraw和React Flow格式
 */

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

  // 从localStorage获取默认配置
  const defaultProvider = localStorage.getItem("selectedProvider") || "custom";
  const modelConfig = localStorage.getItem("modelConfig");
  let config: any = {};

  if (modelConfig) {
    try {
      config = JSON.parse(modelConfig);
    } catch (e) {
      console.error("Failed to parse model config:", e);
    }
  }

  // 构造请求
  const requestData = {
    image_data: base64Image,
    prompt: options.prompt || "Convert this diagram to Excalidraw format. Preserve layout and all connections.",
    provider: options.provider || config.provider || defaultProvider,
    api_key: options.apiKey || config.apiKey,
    base_url: options.baseUrl || config.baseUrl,
    model_name: options.modelName || config.modelName,
    width: options.width || 1400,
    height: options.height || 900,
  };

  // 调用API
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const response = await fetch(`${apiUrl}/api/vision/generate-excalidraw`, {
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

  // 从localStorage获取默认配置
  const defaultProvider = localStorage.getItem("selectedProvider") || "custom";
  const modelConfig = localStorage.getItem("modelConfig");
  let config: any = {};

  if (modelConfig) {
    try {
      config = JSON.parse(modelConfig);
    } catch (e) {
      console.error("Failed to parse model config:", e);
    }
  }

  // 构造请求
  const requestData = {
    image_data: base64Image,
    prompt: options.prompt || "Convert this architecture diagram to SmartArchitect React Flow format. Identify all components and connections.",
    provider: options.provider || config.provider || defaultProvider,
    api_key: options.apiKey || config.apiKey,
    base_url: options.baseUrl || config.baseUrl,
    model_name: options.modelName || config.modelName,
  };

  // 调用API
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const response = await fetch(`${apiUrl}/api/vision/generate-reactflow`, {
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
