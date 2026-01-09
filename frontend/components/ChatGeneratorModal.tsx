"use client";

import { useEffect, useState } from "react";
import { X, MessageSquare, Loader2, Send } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

interface ChatGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FlowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  example_input: string;
  icon?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  architecture: "bg-indigo-100 text-indigo-700",
  troubleshooting: "bg-red-100 text-red-700",
  business: "bg-blue-100 text-blue-700",
  algorithm: "bg-green-100 text-green-700",
  devops: "bg-purple-100 text-purple-700",
};

export default function ChatGeneratorModal({ isOpen, onClose }: ChatGeneratorModalProps) {
  const {
    modelConfig,
    generateFlowchart,
    isGeneratingFlowchart,
    flowTemplates,
    loadFlowTemplates,
  } = useArchitectStore();

  const [userInput, setUserInput] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && flowTemplates.length === 0) {
      loadFlowTemplates();
    }
  }, [isOpen, flowTemplates.length, loadFlowTemplates]);

  const handleTemplateSelect = (template: FlowTemplate) => {
    setSelectedTemplate(template.id);
    setUserInput(template.example_input);
  };

  const handleGenerate = async () => {
    if (!userInput.trim()) {
      toast.error("Please enter a description");
      return;
    }

    if (!modelConfig.apiKey) {
      toast.error("API key not configured. Please configure in Settings.");
      return;
    }

    try {
      await generateFlowchart(userInput, selectedTemplate || undefined);
      toast.success("Flowchart generated successfully!");
      onClose();
      setUserInput("");
      setSelectedTemplate(null);
    } catch (error) {
      toast.error("Failed to generate flowchart");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <MessageSquare className="w-6 h-6 text-green-600 dark:text-green-300" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Chat Flowchart Generator
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Describe a process in natural language to generate a flowchart
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
            disabled={isGeneratingFlowchart}
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {/* Template Quick Select */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Quick Templates
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {flowTemplates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  disabled={isGeneratingFlowchart}
                  className={`
                    p-3 rounded-lg border-2 text-left transition-all
                    ${
                      selectedTemplate === template.id
                        ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                        : "border-gray-200 dark:border-slate-600 hover:border-green-300"
                    }
                    ${isGeneratingFlowchart ? "opacity-50 cursor-not-allowed" : ""}
                  `}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div className={`px-2 py-0.5 rounded text-xs ${CATEGORY_COLORS[template.category]}`}>
                      {template.category}
                    </div>
                  </div>
                  <div className="font-medium text-gray-900 dark:text-white text-sm">
                    {template.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {template.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Text Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Describe your flowchart
            </label>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Example: Generate an OOM troubleshooting flowchart with heap analysis, GC log check, and thread dump steps..."
              className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              rows={6}
              disabled={isGeneratingFlowchart}
            />
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Tip: Be specific about steps, conditions, and branches
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {userInput.trim()
              ? "Click Generate to create flowchart"
              : "Select a template or describe your own process"}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              disabled={isGeneratingFlowchart}
            >
              Cancel
            </button>
            <button
              onClick={handleGenerate}
              disabled={!userInput.trim() || isGeneratingFlowchart}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isGeneratingFlowchart ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Generate
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
