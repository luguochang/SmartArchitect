"use client";

import { useState, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { Code2, RefreshCw } from "lucide-react";

export function CodeEditor() {
  const { mermaidCode, updateFromMermaid } = useArchitectStore();
  const [localCode, setLocalCode] = useState(mermaidCode);
  const [isModified, setIsModified] = useState(false);

  // 同步外部变化到本地编辑器
  useEffect(() => {
    if (!isModified) {
      setLocalCode(mermaidCode);
    }
  }, [mermaidCode, isModified]);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setLocalCode(value);
      setIsModified(value !== mermaidCode);
    }
  };

  const handleApplyChanges = () => {
    updateFromMermaid(localCode);
    setIsModified(false);
  };

  const handleRevert = () => {
    setLocalCode(mermaidCode);
    setIsModified(false);
  };

  return (
    <div className="flex h-full flex-col bg-white dark:bg-slate-900">
      {/* 编辑器标题栏 */}
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Code2 className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <h2 className="font-semibold text-slate-900 dark:text-white">
            Mermaid Code
          </h2>
        </div>

        {isModified && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleRevert}
              className="rounded-md px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            >
              Revert
            </button>
            <button
              onClick={handleApplyChanges}
              className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700"
            >
              <RefreshCw className="h-3 w-3" />
              Apply
            </button>
          </div>
        )}
      </div>

      {/* Monaco 编辑器 */}
      <div className="flex-1">
        <Editor
          height="100%"
          defaultLanguage="mermaid"
          value={localCode}
          onChange={handleEditorChange}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: false,
            automaticLayout: true,
            tabSize: 2,
          }}
        />
      </div>

      {/* 底部提示 */}
      <div className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500 dark:border-slate-800">
        Edit Mermaid code and click Apply to update canvas
      </div>
    </div>
  );
}
