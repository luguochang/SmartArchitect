"use client";

import { useState, useEffect } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { Settings, CheckCircle2, AlertCircle, Eye, EyeOff, Plus, Trash2, Edit2, Star } from "lucide-react";
import { toast } from "sonner";
import { API_ENDPOINTS } from "@/lib/api-config";

interface ModelPreset {
  id: string;
  name: string;
  provider: string;
  api_key: string;
  model_name: string;
  base_url?: string;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * AI 配置面板 - 多配置管理版本
 * 支持保存多个配置，切换默认配置
 */
export function AiConfigPanel() {
  const { modelConfig, setModelConfig } = useArchitectStore();

  // 配置列表状态
  const [presets, setPresets] = useState<ModelPreset[]>([]);
  const [loading, setLoading] = useState(true);

  // 表单状态
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [modelName, setModelName] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  // 加载配置列表
  const loadPresets = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.modelPresets);
      if (response.ok) {
        const data = await response.json();
        setPresets(data.presets || []);

        // 🔧 如果有默认配置，获取完整配置并更新 store
        const defaultPreset = data.presets?.find((p: ModelPreset) => p.is_default);
        if (defaultPreset) {
          // 调用 /full 接口获取真实 API key
          const fullConfigResponse = await fetch(API_ENDPOINTS.modelPresetFull(defaultPreset.id));
          if (fullConfigResponse.ok) {
            const fullData = await fullConfigResponse.json();
            const fullPreset = fullData.preset;

            setModelConfig({
              provider: fullPreset.provider,
              apiKey: fullPreset.api_key,
              baseUrl: fullPreset.base_url || "",
              modelName: fullPreset.model_name,
            });
          }
        }
      }
    } catch (error) {
      console.error("Failed to load presets:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPresets();
  }, []);

  // 保存配置（新增或更新）
  const handleSave = async () => {
    if (!name.trim() || !apiKey.trim() || !baseUrl.trim() || !modelName.trim()) {
      toast.error("请填写完整的配置信息");
      return;
    }

    try {
      const isEditing = !!editingId;
      const url = isEditing
        ? API_ENDPOINTS.modelPreset(editingId)
        : API_ENDPOINTS.modelPresets;

      const method = isEditing ? "PATCH" : "POST";
      const willBeDefault = presets.length === 0; // 第一个配置自动设为默认

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          provider: "custom",
          api_key: apiKey.trim(),
          base_url: baseUrl.trim(),
          model_name: modelName.trim(),
          is_default: willBeDefault,
        }),
      });

      if (response.ok) {
        toast.success(isEditing ? "配置已更新" : "配置已创建");

        // 🔧 如果是新增且自动设为默认，或者编辑的是当前默认配置，更新 store
        if (willBeDefault || (isEditing && presets.find(p => p.id === editingId)?.is_default)) {
          setModelConfig({
            provider: "custom",
            apiKey: apiKey.trim(),
            baseUrl: baseUrl.trim(),
            modelName: modelName.trim(),
          });
        }

        resetForm();
        loadPresets();
      } else {
        const error = await response.json();
        toast.error(error.detail || "保存失败");
      }
    } catch (error) {
      toast.error("保存配置失败");
      console.error(error);
    }
  };

  // 删除配置
  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除这个配置吗？")) return;

    try {
      const response = await fetch(API_ENDPOINTS.modelPreset(id), {
        method: "DELETE",
      });

      if (response.ok) {
        toast.success("配置已删除");
        loadPresets();
      } else {
        toast.error("删除失败");
      }
    } catch (error) {
      toast.error("删除配置失败");
      console.error(error);
    }
  };

  // 设置为默认配置
  const handleSetDefault = async (id: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.modelPreset(id), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_default: true }),
      });

      if (response.ok) {
        toast.success("默认配置已更新");

        // 🔧 获取完整配置（包含 API key）并更新 store
        const fullConfigResponse = await fetch(API_ENDPOINTS.modelPresetFull(id));
        if (fullConfigResponse.ok) {
          const data = await fullConfigResponse.json();
          const fullPreset = data.preset;

          setModelConfig({
            provider: fullPreset.provider,
            apiKey: fullPreset.api_key,
            baseUrl: fullPreset.base_url || "",
            modelName: fullPreset.model_name,
          });
        }

        loadPresets();
      } else {
        toast.error("更新失败");
      }
    } catch (error) {
      toast.error("更新配置失败");
      console.error(error);
    }
  };

  // 编辑配置
  const handleEdit = async (id: string) => {
    try {
      // 获取完整配置（包含 API key）
      const response = await fetch(API_ENDPOINTS.modelPresetFull(id));
      if (response.ok) {
        const data = await response.json();
        const preset = data.preset;

        setEditingId(id);
        setName(preset.name);
        setApiKey(preset.api_key);
        setBaseUrl(preset.base_url || "");
        setModelName(preset.model_name);
        setShowForm(true);
      }
    } catch (error) {
      toast.error("加载配置失败");
      console.error(error);
    }
  };

  // 重置表单
  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setName("");
    setApiKey("");
    setBaseUrl("");
    setModelName("");
  };

  const defaultPreset = presets.find(p => p.is_default);
  const isConfigured = !!defaultPreset;

  if (loading) {
    return <div className="p-4 text-center text-sm text-slate-500">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 p-2 shadow-sm">
            <Settings className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              AI 配置管理
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {isConfigured ? `使用中: ${defaultPreset.name}` : "未配置"}
            </p>
          </div>
        </div>

        {/* 配置状态 */}
        {isConfigured ? (
          <div className="flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            已配置
          </div>
        ) : (
          <div className="flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
            <AlertCircle className="h-3.5 w-3.5" />
            未配置
          </div>
        )}
      </div>

      {/* 配置列表 */}
      {presets.length > 0 && (
        <div className="space-y-2">
          {presets.map((preset) => (
            <div
              key={preset.id}
              className={`rounded-lg border-2 p-3 transition ${
                preset.is_default
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
                  : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                      {preset.name}
                    </h4>
                    {preset.is_default && (
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />
                    )}
                  </div>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 truncate">
                    {preset.model_name}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500 truncate">
                    {preset.base_url}
                  </p>
                </div>

                <div className="flex gap-1 ml-2">
                  {!preset.is_default && (
                    <button
                      onClick={() => handleSetDefault(preset.id)}
                      className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-blue-600 dark:hover:bg-slate-800"
                      title="设为默认"
                    >
                      <Star className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleEdit(preset.id)}
                    className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
                    title="编辑"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(preset.id)}
                    className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-red-600 dark:hover:bg-slate-800"
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

      {/* 新增配置按钮 */}
      {!showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="w-full rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-600 transition hover:border-blue-500 hover:bg-blue-50 hover:text-blue-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400 dark:hover:border-blue-500 dark:hover:bg-blue-950 dark:hover:text-blue-400"
        >
          <Plus className="mr-2 inline-block h-4 w-4" />
          添加新配置
        </button>
      )}

      {/* 配置表单 */}
      {showForm && (
        <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white">
              {editingId ? "编辑配置" : "新增配置"}
            </h4>
            <button
              onClick={resetForm}
              className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            >
              取消
            </button>
          </div>

          {/* 配置名称 */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              配置名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：Claude API"
              className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
            />
          </div>

          {/* API Key */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              API Key <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 pr-10 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Base URL */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Base URL <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.example.com/v1"
              className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
            />
          </div>

          {/* Model Name */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Model Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="claude-sonnet-4-5-20250929"
              className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
            />
          </div>

          {/* 保存按钮 */}
          <button
            onClick={handleSave}
            className="w-full rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-md transition hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg"
          >
            {editingId ? "更新配置" : "保存配置"}
          </button>
        </div>
      )}

      {/* 使用提示 */}
      <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-950">
        <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
          💡 配置说明
        </p>
        <ul className="mt-2 space-y-1 text-xs text-blue-700 dark:text-blue-300">
          <li>• 可保存多个 AI 配置，随时切换</li>
          <li>• 星标配置为默认配置，自动应用到所有功能</li>
          <li>• 支持国内中转站（推荐使用 Claude 模型）</li>
          <li>• Base URL 格式：https://域名/v1</li>
        </ul>
      </div>
    </div>
  );
}
