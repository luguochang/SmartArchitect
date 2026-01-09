"use client";

import { useEffect, useMemo, useState } from "react";
import {
  MessageSquare,
  Send,
  Wand2,
  Sparkles,
  Shield,
  Brush,
  Loader2,
  Sparkles as SparklesIcon,
  AlertCircle,
} from "lucide-react";
import { useArchitectStore, PromptScenario } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";
import { SelectedDetailsPanel } from "./SelectedDetailsPanel";

const CATEGORY_ICONS = {
  refactoring: Sparkles,
  security: Shield,
  beautification: Brush,
  custom: Wand2,
};

const CATEGORY_COLORS = {
  refactoring: "text-purple-500 bg-purple-50 dark:bg-purple-500/10",
  security: "text-red-500 bg-red-50 dark:bg-red-500/10",
  beautification: "text-blue-500 bg-blue-50 dark:bg-blue-500/10",
  custom: "text-gray-500 bg-gray-100 dark:bg-gray-500/10",
};

export function AiControlPanel() {
  const {
    modelConfig,
    // Flowchat generator
    flowTemplates,
    isGeneratingFlowchart,
    loadFlowTemplates,
    generateFlowchart,
    // Prompter
    promptScenarios,
    isExecutingPrompt,
    promptError,
    loadPromptScenarios,
    executePromptScenario,
    applyMockScenario,
  } = useArchitectStore();

  const [flowInput, setFlowInput] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [scenarioInput, setScenarioInput] = useState("");

  useEffect(() => {
    if (flowTemplates.length === 0) {
      loadFlowTemplates();
    }
    if (promptScenarios.length === 0) {
      loadPromptScenarios();
    }
  }, [flowTemplates.length, promptScenarios.length, loadFlowTemplates, loadPromptScenarios]);

  const apiReady = useMemo(() => Boolean(modelConfig.apiKey && modelConfig.apiKey.trim()), [modelConfig.apiKey]);

  const handleTemplatePick = (templateId: string, example: string) => {
    setSelectedTemplate(templateId);
    setFlowInput(example);
  };

  const handleGenerateFlow = async () => {
    if (!flowInput.trim()) {
      toast.error("Please enter a description");
      return;
    }
    if (!apiReady) {
      toast.error("API key not configured. Please set it first.");
      return;
    }
    try {
      await generateFlowchart(flowInput, selectedTemplate || undefined);
      toast.success("Flowchart generated");
    } catch (error) {
      toast.error("Generation failed");
    }
  };

  const handleExecutePrompt = async () => {
    if (!selectedScenario) {
      toast.error("Please select a scenario");
      return;
    }
    // Mock path if no API key: apply local changes only
    if (!apiReady) {
      applyMockScenario(selectedScenario);
      toast.success("Mock prompt applied locally");
      return;
    }
    try {
      await executePromptScenario(selectedScenario, scenarioInput || undefined);
      toast.success("Architecture updated");
    } catch (error) {
      // fallback to mock if backend fails
      applyMockScenario(selectedScenario);
      toast.error(promptError || "Backend unavailable, applied mock changes locally");
    }
  };

  return (
    <div className="flex h-full flex-col bg-white/90 px-4 py-5 backdrop-blur dark:bg-slate-900/90">
      <div className="mb-4 flex items-center justify-between rounded-xl border border-slate-200 bg-gradient-to-r from-indigo-50 via-white to-emerald-50 px-4 py-3 shadow-sm dark:border-slate-800 dark:from-slate-800 dark:via-slate-900 dark:to-emerald-900/20">
        <div className="flex items-center gap-3">
          <SparklesIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">AI Controls</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Generate or refactor directly from here</p>
          </div>
        </div>
        {!apiReady && (
          <div className="flex items-center gap-2 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
            <AlertCircle className="h-4 w-4" />
            API key needed
          </div>
        )}
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        <SelectedDetailsPanel />
        {/* Chat Flowchart */}
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Chat Flowchart</h3>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
              Natural language → Graph
            </span>
          </div>

          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-2 gap-2">
              {flowTemplates.map((tpl) => (
                <button
                  key={tpl.id}
                  onClick={() => handleTemplatePick(tpl.id, tpl.example_input)}
                  disabled={isGeneratingFlowchart}
                  className={`rounded-lg border px-3 py-2 text-left text-xs transition-all ${
                    selectedTemplate === tpl.id
                      ? "border-emerald-500 bg-emerald-50 shadow-sm dark:border-emerald-400 dark:bg-emerald-500/10"
                      : "border-slate-200 hover:border-emerald-300 dark:border-slate-700 dark:hover:border-emerald-400"
                  } ${isGeneratingFlowchart ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <p className="font-medium text-slate-900 dark:text-white">{tpl.name}</p>
                  <p className="mt-1 line-clamp-2 text-slate-500 dark:text-slate-400">{tpl.description}</p>
                </button>
              ))}
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold text-slate-600 dark:text-slate-300">Describe the flow</label>
              <textarea
                value={flowInput}
                onChange={(e) => setFlowInput(e.target.value)}
                placeholder="e.g. Incident response with detection, triage, rollback, and RCA steps..."
                rows={5}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-emerald-300 dark:focus:ring-emerald-500/30"
                disabled={isGeneratingFlowchart}
              />
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Tip: Include branches and end states for better BPMN mapping.</span>
              <button
                onClick={handleGenerateFlow}
                disabled={isGeneratingFlowchart}
                className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isGeneratingFlowchart ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                {isGeneratingFlowchart ? "Generating..." : "Generate"}
              </button>
            </div>
          </div>
        </section>

        {/* Prompter */}
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">AI Actions (Prompter)</h3>
            </div>
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-200">
              Refactor & optimize
            </span>
          </div>

          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-1 gap-3">
              {(promptScenarios.length > 0
                ? promptScenarios
                : ([
                    {
                      id: "beautify-bpmn",
                      name: "Beautify BPMN Layout",
                      description: "Improve spacing, align gateways, harmonize task colors, and add consistent labels.",
                      category: "beautification",
                      style_hint: "Glass + pastel gradients",
                      impact: "medium",
                      recommended_theme: "pastel",
                    },
                    {
                      id: "secure-apis",
                      name: "Harden External APIs",
                      description: "Mark API boundaries, annotate auth flows, and highlight ingress/egress nodes.",
                      category: "security",
                      style_hint: "High-contrast edges + badges",
                      impact: "high",
                      recommended_theme: "high-contrast",
                    },
                    {
                      id: "refactor-services",
                      name: "Refactor Services",
                      description: "Group related services, rename ambiguous nodes, and balance fan-in/out.",
                      category: "refactoring",
                      style_hint: "Professional gradients",
                      impact: "medium",
                      recommended_theme: "corporate-professional",
                    },
                  ] as PromptScenario[])).map((scenario) => {
                const Icon = CATEGORY_ICONS[scenario.category];
                const isSelected = selectedScenario === scenario.id;
                return (
                  <button
                    key={scenario.id}
                    onClick={() => setSelectedScenario(scenario.id)}
                    disabled={isExecutingPrompt}
                    className={`flex w-full items-start gap-3 rounded-lg border px-3 py-3 text-left transition ${
                      isSelected
                        ? "border-indigo-500 bg-indigo-50 shadow-sm dark:border-indigo-400 dark:bg-indigo-500/10"
                        : "border-slate-200 hover:border-indigo-300 dark:border-slate-700 dark:hover:border-indigo-400"
                    } ${isExecutingPrompt ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    <span className={`mt-0.5 rounded-lg p-2 ${CATEGORY_COLORS[scenario.category]}`}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{scenario.name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{scenario.description}</p>
                      <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                          Status: {isExecutingPrompt && isSelected ? "Running..." : "Ready"}
                        </span>
                        {scenario.style_hint && (
                          <span className="rounded-full bg-indigo-50 px-2 py-1 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-200">
                            Style: {scenario.style_hint}
                          </span>
                        )}
                        {scenario.recommended_theme && (
                          <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
                            Theme: {scenario.recommended_theme}
                          </span>
                        )}
                        <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
                          Preview: Structural & text changes
                        </span>
                        {scenario.impact && (
                          <span className="rounded-full bg-amber-50 px-2 py-1 text-amber-700 dark:bg-amber-500/10 dark:text-amber-200">
                            Impact: {scenario.impact}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold text-slate-600 dark:text-slate-300">
                Additional context (optional)
              </label>
              <textarea
                value={scenarioInput}
                onChange={(e) => setScenarioInput(e.target.value)}
                placeholder="Extra constraints, tech stack, SLAs..."
                rows={3}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-300 dark:focus:ring-indigo-500/30"
                disabled={isExecutingPrompt}
              />
            </div>

            <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300">
              <div className="font-semibold text-slate-800 dark:text-white">Preview (static)</div>
              <p className="mt-1">
                We’ll apply the selected scenario to your current graph. Once backend returns diff, we can show a delta view here.
              </p>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>{selectedScenario ? "Execute to apply changes to the canvas." : "Select a scenario to start."}</span>
              <button
                onClick={handleExecutePrompt}
                disabled={!selectedScenario || isExecutingPrompt}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isExecutingPrompt ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                {isExecutingPrompt ? "Running..." : "Execute"}
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
