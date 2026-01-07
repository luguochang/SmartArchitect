"use client";

import { useState } from "react";
import {
  Database,
  Globe,
  Box,
  Settings,
  Plus,
  Image as ImageIcon,
  Wand2,
  FileText,
} from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { ModelConfigModal } from "./ModelConfigModal";
import { ImageUploadModal } from "./ImageUploadModal";
import PrompterModal from "./PrompterModal";
import DocumentUploadModal from "./DocumentUploadModal";

export function Sidebar() {
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isImageUploadOpen, setIsImageUploadOpen] = useState(false);
  const [isPrompterOpen, setIsPrompterOpen] = useState(false);
  const [isDocumentUploadOpen, setIsDocumentUploadOpen] = useState(false);
  const { nodes, setNodes } = useArchitectStore();

  const handleAddNode = (type: string) => {
    const newNode = {
      id: `node-${Date.now()}`,
      type,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
      data: { label: `New ${type}` },
    };
    setNodes([...nodes, newNode]);
  };

  const nodeTypes = [
    { type: "api", icon: Globe, label: "API", color: "text-blue-600" },
    { type: "service", icon: Box, label: "Service", color: "text-purple-600" },
    { type: "database", icon: Database, label: "Database", color: "text-green-600" },
  ];

  return (
    <>
      <aside className="flex w-16 flex-col items-center gap-4 border-r border-slate-200 bg-white py-4 dark:border-slate-800 dark:bg-slate-900">
        {/* 添加节点按钮 */}
        <div className="flex flex-col gap-2">
          {nodeTypes.map(({ type, icon: Icon, label, color }) => (
            <button
              key={type}
              onClick={() => handleAddNode(type)}
              className="group relative flex h-12 w-12 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              title={`Add ${label}`}
            >
              <Icon className={`h-6 w-6 ${color}`} />
              <span className="absolute left-full ml-2 hidden whitespace-nowrap rounded bg-slate-900 px-2 py-1 text-xs text-white group-hover:block">
                Add {label}
              </span>
            </button>
          ))}
        </div>

        <div className="my-4 h-px w-8 bg-slate-200 dark:bg-slate-800" />

        {/* 图片上传按钮（Phase 2 功能） */}
        <button
          onClick={() => setIsImageUploadOpen(true)}
          className="relative flex h-12 w-12 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Upload Architecture Diagram"
        >
          <ImageIcon className="h-6 w-6 text-indigo-600" />
        </button>

        {/* AI Prompter 按钮（Phase 3 功能） */}
        <button
          onClick={() => setIsPrompterOpen(true)}
          className="relative flex h-12 w-12 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          title="AI Prompter"
        >
          <Wand2 className="h-6 w-6 text-purple-600" />
        </button>

        {/* 文档上传按钮（Phase 4 RAG 功能） */}
        <button
          onClick={() => setIsDocumentUploadOpen(true)}
          className="relative flex h-12 w-12 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Upload Documents (RAG)"
        >
          <FileText className="h-6 w-6 text-green-600" />
        </button>

        {/* 设置按钮 */}
        <button
          onClick={() => setIsConfigOpen(true)}
          className="mt-auto flex h-12 w-12 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Settings"
        >
          <Settings className="h-6 w-6 text-slate-600 dark:text-slate-400" />
        </button>
      </aside>

      {/* 模型配置弹窗 */}
      <ModelConfigModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
      />

      {/* 图片上传弹窗 */}
      <ImageUploadModal
        isOpen={isImageUploadOpen}
        onClose={() => setIsImageUploadOpen(false)}
      />

      {/* AI Prompter 弹窗 */}
      <PrompterModal
        isOpen={isPrompterOpen}
        onClose={() => setIsPrompterOpen(false)}
      />

      {/* 文档上传弹窗（Phase 4 RAG） */}
      <DocumentUploadModal
        isOpen={isDocumentUploadOpen}
        onClose={() => setIsDocumentUploadOpen(false)}
      />
    </>
  );
}
