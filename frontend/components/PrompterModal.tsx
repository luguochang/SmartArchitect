"use client";

import { useEffect, useState } from "react";
import { X, Wand2, Sparkles, Shield, Brush, Loader2 } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

interface PrompterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CATEGORY_ICONS = {
  refactoring: Sparkles,
  security: Shield,
  beautification: Brush,
  custom: Wand2,
};

const CATEGORY_COLORS = {
  refactoring: "text-purple-500 bg-purple-50",
  security: "text-red-500 bg-red-50",
  beautification: "text-blue-500 bg-blue-50",
  custom: "text-gray-500 bg-gray-50",
};

export default function PrompterModal({ isOpen, onClose }: PrompterModalProps) {
  const {
    promptScenarios,
    isExecutingPrompt,
    promptError,
    loadPromptScenarios,
    executePromptScenario,
  } = useArchitectStore();

  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [userInput, setUserInput] = useState("");

  useEffect(() => {
    if (isOpen && promptScenarios.length === 0) {
      loadPromptScenarios();
    }
  }, [isOpen, promptScenarios.length, loadPromptScenarios]);

  const handleExecute = async () => {
    if (!selectedScenario) {
      toast.error("Please select a scenario");
      return;
    }

    try {
      await executePromptScenario(selectedScenario, userInput || undefined);
      toast.success("Architecture transformed successfully!");
      onClose();
      setSelectedScenario(null);
      setUserInput("");
    } catch (error) {
      toast.error(promptError || "Failed to execute prompt");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Wand2 className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                AI Prompter
              </h2>
              <p className="text-sm text-gray-500">
                Transform your architecture with AI-powered scenarios
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={isExecutingPrompt}
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Scenarios Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {promptScenarios.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-2" />
                <p className="text-gray-500">Loading scenarios...</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {promptScenarios.map((scenario) => {
                const Icon = CATEGORY_ICONS[scenario.category];
                const isSelected = selectedScenario === scenario.id;

                return (
                  <button
                    key={scenario.id}
                    onClick={() => setSelectedScenario(scenario.id)}
                    disabled={isExecutingPrompt}
                    className={`
                      relative p-4 rounded-lg border-2 transition-all text-left
                      ${
                        isSelected
                          ? "border-purple-500 bg-purple-50 shadow-md"
                          : "border-gray-200 hover:border-purple-300 hover:shadow-sm"
                      }
                      ${isExecutingPrompt ? "opacity-50 cursor-not-allowed" : ""}
                    `}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`p-2 rounded-lg ${
                          CATEGORY_COLORS[scenario.category]
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {scenario.name}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {scenario.description}
                        </p>
                      </div>
                    </div>
                    {isSelected && (
                      <div className="absolute top-2 right-2">
                        <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                          <svg
                            className="w-3 h-3 text-white"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={3}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        </div>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* User Input Section */}
          {selectedScenario && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Context (Optional)
              </label>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Provide any additional requirements or constraints..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                rows={3}
                disabled={isExecutingPrompt}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="text-sm text-gray-500">
            {selectedScenario
              ? "Click Execute to transform your architecture"
              : "Select a scenario to get started"}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              disabled={isExecutingPrompt}
            >
              Cancel
            </button>
            <button
              onClick={handleExecute}
              disabled={!selectedScenario || isExecutingPrompt}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isExecutingPrompt ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4" />
                  Execute
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
