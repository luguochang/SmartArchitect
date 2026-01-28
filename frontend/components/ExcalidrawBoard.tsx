"use client";

import dynamic from "next/dynamic";
import "@excalidraw/excalidraw/index.css";
import { useEffect, useRef, useState } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { ImageIcon } from "lucide-react";
import { ImageConversionModal } from "./ImageConversionModal";
import { toast } from "sonner";
import type { ExcalidrawScene } from "@/lib/utils/imageConversion";

// Type import - using any to avoid build-time type errors
type ExcalidrawImperativeAPI = any;

const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="p-4 text-sm text-slate-500">Loading Excalidraw…</div> }
);

export default function ExcalidrawBoard() {
  const apiRef = useRef<ExcalidrawImperativeAPI | null>(null);
  const scene = useArchitectStore((s) => s.excalidrawScene);
  const setExcalidrawScene = useArchitectStore((s) => s.setExcalidrawScene);
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);

  // Function to update scene - can be called from multiple places
  const updateScene = (api: ExcalidrawImperativeAPI, sceneData: typeof scene) => {
    if (!sceneData?.elements || sceneData.elements.length === 0) {
      return;
    }

    try {
      // 设置完整的 appState
      const appState = {
        viewBackgroundColor: "#ffffff",
        zoom: { value: 1 },
        scrollX: 0,
        scrollY: 0,
        ...sceneData.appState
      };

      api.updateScene({
        elements: sceneData.elements,
        appState
      });

      // 只在完成时滚动一次，使用防抖
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
      updateTimeoutRef.current = setTimeout(() => {
        if (apiRef.current) {
          apiRef.current.scrollToContent();
        }
      }, 150);

    } catch (error) {
      console.error("[ExcalidrawBoard] ❌ updateScene FAILED:", error);
    }
  };

  // Handle successful image conversion
  const handleImportSuccess = (result: ExcalidrawScene) => {
    console.log("[ExcalidrawBoard] Import success, elements:", result.elements.length);

    // Update Zustand store
    setExcalidrawScene(result);

    // If API is ready, update immediately
    if (apiRef.current) {
      updateScene(apiRef.current, result);
    }

    toast.success(`Imported ${result.elements.length} elements to Excalidraw!`);
  };

  // Update scene when scene data changes (if API is ready)
  useEffect(() => {
    console.log(`🔔 [ExcalidrawBoard] useEffect triggered, scene elements: ${scene?.elements?.length || 0}`);

    if (!apiRef.current || !scene?.elements) {
      console.log(`⏭️ [ExcalidrawBoard] Skipping update - API ready: ${!!apiRef.current}, has elements: ${!!scene?.elements}`);
      return;
    }

    // 🔥 IMPORTANT: Only update if we have elements to show
    if (scene.elements.length === 0) {
      console.warn("[ExcalidrawBoard] ⚠️ Received scene with 0 elements, ignoring update");
      return;
    }

    console.log(`✅ [ExcalidrawBoard] Updating Excalidraw canvas with ${scene.elements.length} elements`);
    console.log(`   First 5 element IDs:`, scene.elements.slice(0, 5).map(e => e.id));
    updateScene(apiRef.current, scene);
  }, [scene]);

  return (
    <div className="relative h-full w-full bg-white dark:bg-slate-900">
      {/* Import from Image Button */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={() => setShowImportModal(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-lg transition-colors"
          title="Import diagram from image"
        >
          <ImageIcon className="h-4 w-4" />
          Import from Image
        </button>
      </div>

      {/* Excalidraw Canvas */}
      <Excalidraw
        excalidrawAPI={(api) => {
          apiRef.current = api;

          // CRITICAL FIX: If scene data arrived before API was ready, render it now
          const currentScene = useArchitectStore.getState().excalidrawScene;
          if (currentScene?.elements && currentScene.elements.length > 0) {
            setTimeout(() => updateScene(api, currentScene), 0);
          }
        }}
        initialData={{
          elements: [],
          appState: { viewBackgroundColor: "#ffffff" }
        }}
      />

      {/* Image Conversion Modal */}
      <ImageConversionModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        mode="excalidraw"
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}
