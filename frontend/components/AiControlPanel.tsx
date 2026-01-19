"use client";

import { useEffect, useMemo, useState, useRef } from "react";
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
  Palette,
  Grid3x3,
} from "lucide-react";
import { useArchitectStore, PromptScenario, DiagramType } from "@/lib/store/useArchitectStore";
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
    generationLogs,
    chatHistory,
    loadFlowTemplates,
    generateFlowchart,
    generateExcalidrawScene,
    generateExcalidrawSceneStream,
    canvasMode,
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
  const [showPrompter, setShowPrompter] = useState(false);
  const [diagramType, setDiagramType] = useState<DiagramType>("flow");
  const [templateFilter, setTemplateFilter] = useState<"flow" | "architecture">("flow");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (flowTemplates.length === 0) {
      loadFlowTemplates();
    }
    if (promptScenarios.length === 0) {
      loadPromptScenarios();
    }
  }, [flowTemplates.length, promptScenarios.length, loadFlowTemplates, loadPromptScenarios]);

  // Auto-scroll to bottom when messages update (throttled)
  useEffect(() => {
    if (generationLogs.length === 0 && chatHistory.length === 0) {
      return;
    }

    // Use requestAnimationFrame to batch scroll updates
    const scrollTimeout = setTimeout(() => {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      });
    }, 100);

    return () => clearTimeout(scrollTimeout);
  }, [generationLogs, chatHistory]);

  const apiReady = useMemo(() => Boolean(modelConfig.apiKey && modelConfig.apiKey.trim()), [modelConfig.apiKey]);

  const handleTemplatePick = (templateId: string, example: string) => {
    const tpl = flowTemplates.find((t) => t.id === templateId);
    if (tpl?.category === "architecture") {
      setDiagramType("architecture");
    } else {
      setDiagramType("flow");
    }
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
      if (canvasMode === "excalidraw") {
        await generateExcalidrawSceneStream(flowInput);
        toast.success("Excalidraw scene generated");
      } else {
        await generateFlowchart(flowInput, selectedTemplate || undefined, diagramType);
        toast.success("Flowchart generated");
      }
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
      toast.success("Prompt executed successfully");
    } catch (error) {
      toast.error(promptError || "Failed to execute prompt");
    }
  };

  return (
    <aside className="flex h-full w-96 flex-col gap-4 border-l border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/50 p-4 dark:border-slate-800 dark:from-slate-900 dark:to-slate-900/50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 p-2 shadow-sm">
            {canvasMode === "excalidraw" ? (
              <Palette className="h-5 w-5 text-white" />
            ) : (
              <MessageSquare className="h-5 w-5 text-white" />
            )}
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              {canvasMode === "excalidraw" ? "AI Drawing" : "AI Generator"}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {canvasMode === "excalidraw" ? "Generate hand-drawn diagrams" : "Generate flowcharts & architectures"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPrompter((prev) => !prev)}
            className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {showPrompter ? "Hide" : "Show"} Prompter
          </button>
          {!apiReady && (
            <div className="flex items-center gap-1.5 rounded-lg bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
              <AlertCircle className="h-3.5 w-3.5" />
              No API key
            </div>
          )}
        </div>
      </div>

      <SelectedDetailsPanel />

      {/* Main Content - Full Height */}
      <div className="flex min-h-0 flex-1 flex-col gap-4">
        {/* Generator Section */}
        <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {/* Templates (only for ReactFlow mode) */}
          {canvasMode !== "excalidraw" && (
            <div className="border-b border-slate-200 p-4 dark:border-slate-800">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Templates</h3>
                <div className="flex rounded-lg border border-slate-200 bg-slate-50 text-xs dark:border-slate-700 dark:bg-slate-800">
                  <button
                    onClick={() => {
                      setTemplateFilter("flow");
                      setDiagramType("flow");
                    }}
                    className={`px-3 py-1 rounded-l-lg transition ${
                      templateFilter === "flow"
                        ? "bg-emerald-500 text-white shadow-sm"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
                    }`}
                  >
                    Flow
                  </button>
                  <button
                    onClick={() => {
                      setTemplateFilter("architecture");
                      setDiagramType("architecture");
                    }}
                    className={`px-3 py-1 rounded-r-lg transition ${
                      templateFilter === "architecture"
                        ? "bg-emerald-500 text-white shadow-sm"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
                    }`}
                  >
                    Architecture
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1">
                {(templateFilter === "flow"
                  ? flowTemplates.filter((tpl) => tpl.category !== "architecture")
                  : flowTemplates.filter((tpl) => tpl.category === "architecture")
                ).map((tpl) => (
                  <button
                    key={tpl.id}
                    onClick={() => handleTemplatePick(tpl.id, tpl.example_input)}
                    disabled={isGeneratingFlowchart}
                    className={`rounded-lg border px-2.5 py-2 text-left text-xs transition-all ${
                      selectedTemplate === tpl.id
                        ? "border-emerald-500 bg-emerald-50 shadow-sm dark:border-emerald-400 dark:bg-emerald-500/10"
                        : "border-slate-200 hover:border-emerald-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:border-emerald-400 dark:hover:bg-slate-800"
                    } ${isGeneratingFlowchart ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    <p className="font-medium text-slate-900 dark:text-white truncate">{tpl.name}</p>
                    <p className="mt-0.5 line-clamp-1 text-slate-500 dark:text-slate-400">{tpl.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages Area - Unified */}
          <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3">
            {/* Chat History */}
            {chatHistory.length > 0 && (
              <>
                {chatHistory.map((msg, idx) => (
                  <div
                    key={`chat-${idx}`}
                    className={`flex ${msg.role === "assistant" ? "justify-start" : "justify-end"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        msg.role === "assistant"
                          ? "bg-gradient-to-br from-emerald-50 to-teal-50 text-emerald-900 dark:from-emerald-900/30 dark:to-teal-900/30 dark:text-emerald-50"
                          : "bg-slate-200 text-slate-900 dark:bg-slate-700 dark:text-white"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Generation Logs */}
            {generationLogs.length > 0 && (
              <div className="space-y-2">
                {generationLogs.map((log, idx) => (
                  <div
                    key={`log-${idx}`}
                    className={`rounded-lg bg-gradient-to-br from-emerald-50 to-teal-50 px-3 py-2 text-xs font-mono text-emerald-900 dark:from-emerald-900/30 dark:to-teal-900/30 dark:text-emerald-50 ${
                      log.startsWith("[生成中]")
                        ? "overflow-x-auto whitespace-nowrap max-w-full"
                        : "whitespace-pre-wrap break-words"
                    }`}
                  >
                    {log}
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {chatHistory.length === 0 && generationLogs.length === 0 && (
              <div className="flex h-full items-center justify-center text-center">
                <div className="max-w-xs space-y-2">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30">
                    <SparklesIcon className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {canvasMode === "excalidraw" ? "Ready to draw!" : "Ready to generate"}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {canvasMode === "excalidraw"
                      ? "Describe what you want to draw, and AI will create a hand-drawn diagram for you."
                      : "Enter a description below and AI will generate a flowchart or architecture diagram."}
                  </p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area - Fixed at Bottom */}
          <div className="border-t border-slate-200 p-4 dark:border-slate-800">
            <div className="space-y-3">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-600 dark:text-slate-300">
                  {canvasMode === "excalidraw" ? "Describe your drawing" : "Describe the flow"}
                </label>
                <textarea
                  value={flowInput}
                  onChange={(e) => setFlowInput(e.target.value)}
                  placeholder={
                    canvasMode === "excalidraw"
                      ? "e.g. A colorful robot with glowing eyes..."
                      : "e.g. User authentication flow with login, verification, and error handling..."
                  }
                  rows={3}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-emerald-300 dark:focus:ring-emerald-500/30"
                  disabled={isGeneratingFlowchart}
                />
              </div>

              <button
                onClick={handleGenerateFlow}
                disabled={isGeneratingFlowchart || !apiReady}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:from-emerald-700 hover:to-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isGeneratingFlowchart ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        {/* Prompter (Collapsible) */}
        {showPrompter && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 max-h-80 overflow-y-auto">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">AI Prompter</h3>
              </div>
              <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-200">
                Refactor & optimize
              </span>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-2">
                {(promptScenarios.length > 0
                  ? promptScenarios
                  : []
                ).map((scenario) => {
                  const Icon = CATEGORY_ICONS[scenario.category as keyof typeof CATEGORY_ICONS] || Wand2;
                  const colorClass = CATEGORY_COLORS[scenario.category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.custom;
                  return (
                    <button
                      key={scenario.id}
                      onClick={() => setSelectedScenario(scenario.id)}
                      disabled={isExecutingPrompt}
                      className={`flex items-start gap-3 rounded-lg border px-3 py-2.5 text-left text-xs transition-all ${
                        selectedScenario === scenario.id
                          ? "border-indigo-500 bg-indigo-50 shadow-sm dark:border-indigo-400 dark:bg-indigo-500/10"
                          : "border-slate-200 hover:border-indigo-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:border-indigo-400 dark:hover:bg-slate-800"
                      } ${isExecutingPrompt ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                      <div className={`mt-0.5 rounded-md p-1.5 ${colorClass}`}>
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-slate-900 dark:text-white">{scenario.name}</p>
                        <p className="mt-0.5 text-slate-500 dark:text-slate-400 line-clamp-2">{scenario.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>

              {selectedScenario && (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={scenarioInput}
                    onChange={(e) => setScenarioInput(e.target.value)}
                    placeholder="Additional instructions (optional)"
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-300 dark:focus:ring-indigo-500/30"
                    disabled={isExecutingPrompt}
                  />
                  <button
                    onClick={handleExecutePrompt}
                    disabled={isExecutingPrompt}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:from-indigo-700 hover:to-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isExecutingPrompt ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Execute Prompt
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </aside>
  );
}
