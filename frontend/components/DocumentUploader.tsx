"use client";

import { useState, useCallback, useEffect } from "react";
import { FileText, Upload, CheckCircle, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API_ENDPOINTS, API_BASE_URL } from "@/lib/api-config";

export function DocumentUploader() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  // Load existing documents on mount
  const loadDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error("Failed to load documents:", error);
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

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

      const response = await fetch(API_ENDPOINTS.ragUpload, {
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
      const response = await fetch(`${API_BASE_URL}/api/rag/documents/${documentId}`, {
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

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-6">
        <div className="flex flex-col items-center gap-3">
          <div className="rounded-full bg-indigo-100 dark:bg-indigo-900/30 p-2">
            <Upload className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
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

          <div className="flex gap-2">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".pdf,.md,.docx,.doc"
                onChange={handleFileSelect}
                className="hidden"
                disabled={isUploading}
              />
              <span className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs text-white hover:bg-indigo-700 disabled:opacity-50">
                {selectedFile ? "Change File" : "Select File"}
              </span>
            </label>

            {selectedFile && (
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-3 py-1.5 text-xs text-white hover:bg-green-700 disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-3 w-3" />
                    Upload
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="rounded-lg bg-indigo-50 dark:bg-indigo-900/20 p-3">
        <p className="text-xs font-medium text-indigo-900 dark:text-indigo-100">
          AI-Powered Knowledge Base
        </p>
        <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
          Upload architecture documentation, best practices, or design patterns. The AI will parse and index your documents for semantic search and RAG-enhanced interactions.
        </p>
      </div>

      {/* Existing Documents */}
      <div>
        <h3 className="text-xs font-semibold text-slate-900 dark:text-white mb-2">
          Uploaded Documents {!isLoadingDocs && `(${documents.length})`}
        </h3>

        {isLoadingDocs ? (
          <div className="flex items-center justify-center p-4">
            <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
          </div>
        ) : documents.length > 0 ? (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileText className="h-3 w-3 text-slate-600 dark:text-slate-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-900 dark:text-white truncate">
                      {doc.filename}
                    </p>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400">
                      {doc.file_type} • {new Date(doc.upload_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                  title="Delete document"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-4 text-xs text-slate-500 dark:text-slate-400 border border-dashed border-slate-200 dark:border-slate-700 rounded-lg">
            No documents uploaded yet
          </div>
        )}
      </div>
    </div>
  );
}
