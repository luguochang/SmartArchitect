"use client";

import { useState, useCallback } from "react";
import { X, FileText, Upload, CheckCircle, Trash2 } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function DocumentUploadModal({ isOpen, onClose }: DocumentUploadModalProps) {
  const { modelConfig } = useArchitectStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<any[]>([]);

  // Load existing documents on open
  const loadDocuments = useCallback(async () => {
    try {
      const response = await fetch("/api/rag/documents");
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error("Failed to load documents:", error);
    }
  }, []);

  // Load documents when modal opens
  useState(() => {
    if (isOpen) {
      loadDocuments();
    }
  });

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (["pdf", "md", "docx", "doc"].includes(extension || "")) {
        setSelectedFile(file);
      } else {
        toast.error("Unsupported file type. Please upload PDF, Markdown, or Docx files.");
      }
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("/api/rag/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      toast.success(
        `Document uploaded successfully! Created ${data.chunks_created} searchable chunks.`,
        { duration: 4000 }
      );

      // Reload documents list
      await loadDocuments();

      // Clear selection
      setSelectedFile(null);

    } catch (error) {
      toast.error("Failed to upload document. Please try again.");
      console.error("Document upload error:", error);
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile, loadDocuments]);

  const handleDelete = useCallback(async (documentId: string) => {
    try {
      const response = await fetch(`/api/rag/documents/${documentId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Delete failed");
      }

      toast.success("Document deleted successfully");
      await loadDocuments();

    } catch (error) {
      toast.error("Failed to delete document");
      console.error("Document delete error:", error);
    }
  }, [loadDocuments]);

  const handleClose = useCallback(() => {
    if (!isUploading) {
      setSelectedFile(null);
      onClose();
    }
  }, [isUploading, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-3xl rounded-lg bg-white shadow-2xl dark:bg-slate-900 m-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Knowledge Base Documents
            </h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="rounded-lg p-1 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Upload Area */}
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-8">
            <div className="flex flex-col items-center gap-4">
              <div className="rounded-full bg-indigo-100 dark:bg-indigo-900/30 p-3">
                <Upload className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
              </div>

              {selectedFile ? (
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    Choose a document to upload
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    PDF, Markdown (.md), or Word (.docx) files
                  </p>
                </div>
              )}

              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".pdf,.md,.docx,.doc"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={isUploading}
                />
                <span className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50">
                  {selectedFile ? "Change File" : "Select File"}
                </span>
              </label>

              {selectedFile && (
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckCircle className="h-4 w-4" />
                  {isUploading ? "Uploading..." : "Upload Document"}
                </button>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="mt-4 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 p-4">
            <p className="text-sm font-medium text-indigo-900 dark:text-indigo-100">
              AI-Powered Knowledge Base
            </p>
            <p className="text-sm text-indigo-700 dark:text-indigo-300 mt-1">
              Upload architecture documentation, best practices, or design patterns. The AI will:
            </p>
            <ul className="text-sm text-indigo-700 dark:text-indigo-300 mt-2 space-y-1 ml-4 list-disc">
              <li>Parse and index your documents</li>
              <li>Enable semantic search across all content</li>
              <li>Provide context-aware architecture recommendations</li>
              <li>Support RAG-enhanced AI interactions</li>
            </ul>
          </div>

          {/* Existing Documents */}
          {documents.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
                Uploaded Documents ({documents.length})
              </h3>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.document_id}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <FileText className="h-4 w-4 text-slate-600 dark:text-slate-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {doc.filename}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {doc.file_type} • {new Date(doc.upload_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.document_id)}
                      className="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                      title="Delete document"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4 dark:border-slate-800">
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
