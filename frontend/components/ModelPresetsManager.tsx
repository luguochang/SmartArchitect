"use client";

import React, { useState, useEffect } from "react";
import { Settings, Plus, Trash2, Star, StarOff, Edit2, Check, X, Info, AlertCircle } from "lucide-react";
import { PROVIDER_DEFAULTS, getAllProviderOptions } from "@/lib/config/providerDefaults";

interface ModelPreset {
  id: string;
  name: string;
  provider: "gemini" | "openai" | "claude" | "siliconflow" | "custom";
  api_key: string;
  model_name: string;
  base_url?: string;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}

interface ModelPresetsManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPreset?: (preset: ModelPreset) => void;
}

export default function ModelPresetsManager({
  isOpen,
  onClose,
  onSelectPreset,
}: ModelPresetsManagerProps) {
  const [presets, setPresets] = useState<ModelPreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showDefaults, setShowDefaults] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // 新建/编辑表单状态
  const [formData, setFormData] = useState<{
    name: string;
    provider: "gemini" | "openai" | "claude" | "siliconflow" | "custom";
    api_key: string;
    model_name: string;
    base_url: string;
    is_default: boolean;
  }>({
    name: "",
    provider: "gemini",
    api_key: "",
    model_name: "",
    base_url: "",
    is_default: false,
  });

  useEffect(() => {
    if (isOpen) {
      loadPresets();
    }
  }, [isOpen]);

  const loadPresets = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const response = await fetch("http://localhost:8000/api/models/presets");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      if (data.success) {
        setPresets(data.presets || []);
      } else {
        throw new Error(data.message || "Failed to load presets");
      }
    } catch (error: any) {
      console.error("Failed to load presets:", error);
      setLoadError(error.message || "无法加载配置列表");
      setPresets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.api_key || !formData.model_name) {
      alert("请填写名称、API Key 和模型名称");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/models/presets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "创建失败");
      }

      if (data.success) {
        await loadPresets();
        setCreating(false);
        setFormData({
          name: "",
          provider: "gemini",
          api_key: "",
          model_name: "",
          base_url: "",
          is_default: false,
        });
      }
    } catch (error: any) {
      alert(error.message || "创建预设失败");
    }
  };

  const handleEdit = async (presetId: string) => {
    try {
      // Fetch full preset with API key
      const response = await fetch(
        `http://localhost:8000/api/models/presets/${presetId}/full`
      );
      const data = await response.json();

      if (data.success && data.preset) {
        const preset = data.preset;
        setFormData({
          name: preset.name,
          provider: preset.provider,
          api_key: preset.api_key,
          model_name: preset.model_name,
          base_url: preset.base_url || "",
          is_default: preset.is_default,
        });
        setEditing(presetId);
        setCreating(false);
      } else {
        alert("获取配置失败");
      }
    } catch (error) {
      console.error("Failed to fetch preset for editing:", error);
      alert("获取配置失败");
    }
  };

  const handleUpdate = async () => {
    if (!editing) return;

    if (!formData.name || !formData.api_key || !formData.model_name) {
      alert("请填写名称、API Key 和模型名称");
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/models/presets/${editing}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "更新失败");
      }

      if (data.success) {
        await loadPresets();
        setEditing(null);
        setFormData({
          name: "",
          provider: "gemini",
          api_key: "",
          model_name: "",
          base_url: "",
          is_default: false,
        });
      }
    } catch (error: any) {
      alert(error.message || "更新预设失败");
    }
  };

  const handleDelete = async (presetId: string) => {
    if (!confirm("确定删除此配置？")) return;

    try {
      const response = await fetch(`http://localhost:8000/api/models/presets/${presetId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        await loadPresets();
      }
    } catch (error) {
      console.error("Failed to delete preset:", error);
    }
  };

  const handleSetDefault = async (presetId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/models/presets/${presetId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_default: true }),
      });

      if (response.ok) {
        await loadPresets();
      }
    } catch (error) {
      console.error("Failed to set default:", error);
    }
  };

  if (!isOpen) return null;

  const providerLabels = {
    gemini: "Google Gemini",
    openai: "OpenAI",
    claude: "Anthropic Claude",
    siliconflow: "SiliconFlow",
    custom: "Custom",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-slate-900">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <Settings className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              AI 模型配置管理
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[calc(90vh-140px)] overflow-y-auto p-6">
          {/* Default Configurations Section */}
          <div className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950">
            <button
              onClick={() => setShowDefaults(!showDefaults)}
              className="w-full flex items-center justify-between mb-3"
            >
              <div className="flex items-center gap-2">
                <Info className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                <h3 className="font-bold text-emerald-900 dark:text-emerald-100">
                  🚀 默认配置（即开即用）
                </h3>
              </div>
              <span className="text-xs text-emerald-600 dark:text-emerald-400">
                {showDefaults ? "点击收起" : "点击展开"}
              </span>
            </button>

            {showDefaults && (
              <div className="space-y-3">
                <p className="text-sm text-emerald-700 dark:text-emerald-300 mb-3">
                  以下配置已预置好测试 API Key，可直接使用。如需使用自己的 Key，请点击"使用"后修改。
                </p>

                {getAllProviderOptions().map((config) => (
                  <div
                    key={config.provider}
                    className="rounded-lg border border-emerald-300 bg-white p-3 dark:border-emerald-700 dark:bg-slate-800"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-slate-900 dark:text-white">
                            {config.displayName}
                          </h4>
                          {config.apiKey && (
                            <span className="rounded bg-green-500 px-2 py-0.5 text-xs text-white">
                              已配置
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">
                          {config.description}
                        </p>

                        <div className="grid gap-1.5 text-xs">
                          <div className="flex items-start gap-2">
                            <span className="text-slate-500 dark:text-slate-400 font-medium w-20 flex-shrink-0">
                              Base URL:
                            </span>
                            <code className="flex-1 rounded bg-slate-100 px-2 py-0.5 font-mono text-emerald-700 dark:bg-slate-900 dark:text-emerald-300 break-all">
                              {config.baseUrl}
                            </code>
                          </div>

                          <div className="flex items-start gap-2">
                            <span className="text-slate-500 dark:text-slate-400 font-medium w-20 flex-shrink-0">
                              Model:
                            </span>
                            <code className="flex-1 rounded bg-slate-100 px-2 py-0.5 font-mono text-blue-700 dark:bg-slate-900 dark:text-blue-300 break-all">
                              {config.modelName}
                            </code>
                          </div>

                          <div className="flex items-start gap-2">
                            <span className="text-slate-500 dark:text-slate-400 font-medium w-20 flex-shrink-0">
                              API Key:
                            </span>
                            <code className="flex-1 rounded bg-slate-100 px-2 py-0.5 font-mono text-slate-600 dark:bg-slate-900 dark:text-slate-400 break-all">
                              {config.apiKey ? `${config.apiKey.substring(0, 20)}...` : "未配置（需自行提供）"}
                            </code>
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          if (onSelectPreset) {
                            // Use the default config directly
                            onSelectPreset({
                              id: `default-${config.provider}`,
                              name: `默认 ${config.displayName}`,
                              provider: config.provider,
                              api_key: config.apiKey,
                              model_name: config.modelName,
                              base_url: config.baseUrl,
                              is_default: false
                            });
                            onClose();
                          }
                        }}
                        className="ml-3 flex-shrink-0 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-700"
                      >
                        使用
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="mb-4 flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                自定义配置
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                保存多个 AI 配置，随时快速切换
              </p>
            </div>
            <button
              onClick={() => setCreating(true)}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              新建配置
            </button>
          </div>

          {/* Create/Edit Form */}
          {(creating || editing) && (
            <div className="mb-6 rounded-lg border-2 border-indigo-200 bg-indigo-50 p-4 dark:border-indigo-800 dark:bg-indigo-950">
              <h3 className="mb-3 font-semibold text-slate-900 dark:text-white">
                {editing ? "编辑配置" : "创建新配置"}
              </h3>
              <div className="grid gap-3">
                <input
                  type="text"
                  placeholder="配置名称（如：个人 Gemini）"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"
                />
                <select
                  value={formData.provider}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      provider: e.target.value as any,
                    })
                  }
                  className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"
                >
                  {Object.entries(providerLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                <input
                  type="password"
                  placeholder="API Key"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"
                />
                <input
                  type="text"
                  placeholder="模型名称"
                  value={formData.model_name}
                  onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                  className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"
                />
                <input
                  type="text"
                  placeholder={`Base URL (默认: ${PROVIDER_DEFAULTS[formData.provider]?.baseUrl || ""})`}
                  value={formData.base_url}
                  onChange={(e) =>
                    setFormData({ ...formData, base_url: e.target.value })
                  }
                  className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-800 text-sm"
                />
                <div className="text-xs text-slate-500 dark:text-slate-400 -mt-2">
                  💡 留空将使用默认 Base URL: {PROVIDER_DEFAULTS[formData.provider]?.baseUrl}
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) =>
                      setFormData({ ...formData, is_default: e.target.checked })
                    }
                    className="rounded"
                  />
                  设为默认配置
                </label>
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={editing ? handleUpdate : handleCreate}
                  className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
                >
                  <Check className="h-4 w-4" />
                  {editing ? "更新" : "保存"}
                </button>
                <button
                  onClick={() => {
                    setCreating(false);
                    setEditing(null);
                    setFormData({
                      name: "",
                      provider: "gemini",
                      api_key: "",
                      model_name: "",
                      base_url: "",
                      is_default: false,
                    });
                  }}
                  className="rounded-lg bg-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-200"
                >
                  取消
                </button>
              </div>
            </div>
          )}

          {/* Presets List */}
          {loading ? (
            <div className="py-12 text-center text-slate-500">加载中...</div>
          ) : loadError ? (
            <div className="rounded-lg border-2 border-red-200 bg-red-50 py-8 px-4 text-center dark:border-red-800 dark:bg-red-950">
              <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
              <p className="mt-3 text-red-600 dark:text-red-400 font-semibold">
                加载失败
              </p>
              <p className="mt-1 text-sm text-red-500 dark:text-red-400">
                {loadError}
              </p>
              <button
                onClick={loadPresets}
                className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
              >
                重试
              </button>
            </div>
          ) : presets.length === 0 ? (
            <div className="rounded-lg border-2 border-dashed border-slate-300 py-12 text-center dark:border-slate-700">
              <Settings className="mx-auto h-12 w-12 text-slate-400" />
              <p className="mt-3 text-slate-600 dark:text-slate-400">
                暂无配置，点击&ldquo;新建配置&rdquo;开始
              </p>
            </div>
          ) : (
            <div className="grid gap-3">
              {presets.map((preset) => (
                <div
                  key={preset.id}
                  className={`rounded-lg border p-4 ${
                    preset.is_default
                      ? "border-indigo-400 bg-indigo-50 dark:border-indigo-600 dark:bg-indigo-950"
                      : "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900 dark:text-white">
                          {preset.name}
                        </h3>
                        {preset.is_default && (
                          <span className="rounded bg-indigo-600 px-2 py-0.5 text-xs text-white">
                            默认
                          </span>
                        )}
                      </div>
                      <div className="mt-1 flex gap-4 text-sm text-slate-600 dark:text-slate-400">
                        <span>{providerLabels[preset.provider]}</span>
                        <span className="font-mono">{preset.model_name}</span>
                      </div>
                      {preset.base_url && (
                        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          <span className="font-medium">Base URL:</span>{" "}
                          <code className="rounded bg-slate-100 px-1 py-0.5 dark:bg-slate-800">
                            {preset.base_url}
                          </code>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {!preset.is_default && (
                        <button
                          onClick={() => handleSetDefault(preset.id)}
                          className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-yellow-600 dark:hover:bg-slate-700"
                          title="设为默认"
                        >
                          <StarOff className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleEdit(preset.id)}
                        className="rounded-lg p-2 text-slate-400 hover:bg-blue-100 hover:text-blue-600 dark:hover:bg-blue-950"
                        title="编辑"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      {onSelectPreset && (
                        <button
                          onClick={async () => {
                            try {
                              // Fetch full preset with API key
                              const response = await fetch(
                                `http://localhost:8000/api/models/presets/${preset.id}/full`
                              );
                              const data = await response.json();

                              if (data.success && data.preset) {
                                onSelectPreset(data.preset);
                                onClose();
                              } else {
                                alert("获取配置失败");
                              }
                            } catch (error) {
                              console.error("Failed to fetch full preset:", error);
                              alert("获取配置失败");
                            }
                          }}
                          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
                        >
                          使用
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(preset.id)}
                        className="rounded-lg p-2 text-slate-400 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-950"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 px-6 py-4 dark:border-slate-800">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            💡 提示：配置会安全保存到服务端，所有 AI 功能都可使用这些预设
          </p>
        </div>
      </div>
    </div>
  );
}
