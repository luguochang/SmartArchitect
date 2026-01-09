"use client";

import { useState } from "react";
import { Download, FileText, Presentation, Mic, ChevronDown, Loader2 } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

export default function ExportMenu() {
  const { nodes, edges, mermaidCode, modelConfig } = useArchitectStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportType, setExportType] = useState<string>("");

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

  const handleGenerateScript = async (duration: "30s" | "2min" | "5min") => {
    if (!modelConfig.apiKey) {
      toast.error("API key not configured. Please configure in Settings.");
      return;
    }

    setIsExporting(true);
    setExportType(`script-${duration}`);

    try {
      const formData = new URLSearchParams();
      formData.append("provider", modelConfig.provider);
      formData.append("api_key", modelConfig.apiKey);

      const response = await fetch(`/api/export/script?${formData.toString()}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nodes,
          edges,
          duration,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate script");
      }

      const data = await response.json();

      // Copy script to clipboard
      await navigator.clipboard.writeText(data.script);

      toast.success(
        `Generated ${duration} script (${data.word_count} words) - Copied to clipboard!`,
        { duration: 4000 }
      );

      // Also download as text file
      const blob = new Blob([data.script], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `presentation_script_${duration}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast.error("Failed to generate speech script");
      console.error("Script generation error:", error);
    } finally {
      setIsExporting(false);
      setExportType("");
      setIsOpen(false);
    }
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
            <div className="p-2">
              <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                Speech Script
              </div>

              <button
                onClick={() => handleGenerateScript("30s")}
                className="w-full px-3 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors text-left rounded"
              >
                <Mic className="w-4 h-4 text-purple-600" />
                <div className="text-sm text-gray-700">30 seconds</div>
              </button>

              <button
                onClick={() => handleGenerateScript("2min")}
                className="w-full px-3 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors text-left rounded"
              >
                <Mic className="w-4 h-4 text-purple-600" />
                <div className="text-sm text-gray-700">2 minutes</div>
              </button>

              <button
                onClick={() => handleGenerateScript("5min")}
                className="w-full px-3 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors text-left rounded"
              >
                <Mic className="w-4 h-4 text-purple-600" />
                <div className="text-sm text-gray-700">5 minutes</div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
