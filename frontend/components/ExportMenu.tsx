"use client";

import { useState } from "react";
import { Download, FileText, Presentation, Mic, ChevronDown, Loader2 } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";
import ScriptGenerator from "./ScriptGenerator";
import ScriptEditor from "./ScriptEditor";
import type { ScriptContent, ScriptDuration } from "@/types/script";

export default function ExportMenu() {
  const { nodes, edges, mermaidCode, modelConfig } = useArchitectStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportType, setExportType] = useState<string>("");

  // Script generation workflow state
  const [showScriptGenerator, setShowScriptGenerator] = useState(false);
  const [showScriptEditor, setShowScriptEditor] = useState(false);
  const [currentScriptId, setCurrentScriptId] = useState<string | null>(null);
  const [currentScriptContent, setCurrentScriptContent] = useState<ScriptContent | null>(null);
  const [scriptDuration, setScriptDuration] = useState<ScriptDuration>("2min");

  const handleExportPPT = async () => {
    setIsExporting(true);
    setExportType("ppt");

    try {
      const response = await fetch("/api/export/ppt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nodes,
          edges,
          mermaid_code: mermaidCode,
          title: "Architecture Diagram",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to export PPT");
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Architecture_Diagram.pptx";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success("PowerPoint exported successfully!");
    } catch (error) {
      toast.error("Failed to export PowerPoint");
      console.error("PPT export error:", error);
    } finally {
      setIsExporting(false);
      setExportType("");
      setIsOpen(false);
    }
  };

  const handleExportSlidev = async () => {
    setIsExporting(true);
    setExportType("slidev");

    try {
      const response = await fetch("/api/export/slidev", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nodes,
          edges,
          mermaid_code: mermaidCode,
          title: "Architecture Diagram",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to export Slidev");
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Architecture_Diagram_slidev.md";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success("Slidev markdown exported successfully!");
    } catch (error) {
      toast.error("Failed to export Slidev");
      console.error("Slidev export error:", error);
    } finally {
      setIsExporting(false);
      setExportType("");
      setIsOpen(false);
    }
  };

  const handleGenerateScript = () => {
    if (!modelConfig.apiKey) {
      toast.error("API key not configured. Please configure in Settings.");
      return;
    }
    setIsOpen(false);
    setShowScriptGenerator(true);
  };

  const handleScriptComplete = (scriptId: string, content: ScriptContent, duration: ScriptDuration) => {
    setCurrentScriptId(scriptId);
    setCurrentScriptContent(content);
    setScriptDuration(duration);
    setShowScriptGenerator(false);
    setShowScriptEditor(true);
  };

  return (
    <div className="relative">
      {/* Export Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        title="Export Architecture"
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
        ) : (
          <Download className="w-4 h-4 text-indigo-600" />
        )}
        <span className="text-sm font-medium text-gray-700">Export</span>
        <ChevronDown className="w-3 h-3 text-gray-500" />
      </button>

      {/* Export Menu Dropdown */}
      {isOpen && !isExporting && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute top-full right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
            {/* PPT Export */}
            <button
              onClick={handleExportPPT}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors text-left border-b border-gray-100"
            >
              <Presentation className="w-5 h-5 text-orange-600" />
              <div>
                <div className="text-sm font-medium text-gray-900">PowerPoint</div>
                <div className="text-xs text-gray-500">Download as .pptx</div>
              </div>
            </button>

            {/* Slidev Export */}
            <button
              onClick={handleExportSlidev}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors text-left border-b border-gray-100"
            >
              <FileText className="w-5 h-5 text-blue-600" />
              <div>
                <div className="text-sm font-medium text-gray-900">Slidev</div>
                <div className="text-xs text-gray-500">Download markdown slides</div>
              </div>
            </button>

            {/* Speech Scripts */}
            <button
              onClick={handleGenerateScript}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors text-left"
            >
              <Mic className="w-5 h-5 text-purple-600" />
              <div>
                <div className="text-sm font-medium text-gray-900">生成演讲稿</div>
                <div className="text-xs text-gray-500">AI专业演讲稿生成与编辑</div>
              </div>
            </button>
          </div>
        </>
      )}

      {/* Script Generation Workflow Modals */}
      {showScriptGenerator && (
        <ScriptGenerator
          isOpen={showScriptGenerator}
          onClose={() => setShowScriptGenerator(false)}
          onComplete={handleScriptComplete}
        />
      )}

      {showScriptEditor && currentScriptContent && (
        <ScriptEditor
          scriptId={currentScriptId!}
          initialContent={currentScriptContent}
          duration={scriptDuration}
          isOpen={showScriptEditor}
          onClose={() => setShowScriptEditor(false)}
        />
      )}
    </div>
  );
}
