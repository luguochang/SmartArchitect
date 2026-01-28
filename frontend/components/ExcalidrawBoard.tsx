"use client";

import dynamic from "next/dynamic";
import "@excalidraw/excalidraw/index.css";
import { useEffect, useRef, useCallback } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

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

  // Note: Image upload button removed from ExcalidrawBoard
  // Now located in AiControlPanel for Excalidraw mode

  // Function to update scene - can be called from multiple places
  const updateScene = (api: ExcalidrawImperativeAPI, sceneData: typeof scene) => {
    if (!sceneData?.elements || sceneData.elements.length === 0) {
      console.warn("[ExcalidrawBoard] Cannot update scene - no elements");
      return;
    }

    try {
      console.log("[ExcalidrawBoard] Updating scene with elements:", sceneData.elements.length);
      console.log("[ExcalidrawBoard] First element sample:", JSON.stringify(sceneData.elements[0], null, 2));

      // 设置完整的 appState
      const appState = {
        viewBackgroundColor: "#ffffff",
        zoom: { value: 1 },
        scrollX: 0,
        scrollY: 0,
        ...sceneData.appState
      };

      console.log("[ExcalidrawBoard] Calling api.updateScene...");
      api.updateScene({
        elements: sceneData.elements,
        appState
      });

      console.log("[ExcalidrawBoard] ✅ api.updateScene completed");

      // 只在完成时滚动一次，使用防抖
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
      updateTimeoutRef.current = setTimeout(() => {
        if (apiRef.current) {
          console.log("[ExcalidrawBoard] Scrolling to content...");
          apiRef.current.scrollToContent();
        }
      }, 150);

    } catch (error) {
      console.error("[ExcalidrawBoard] ❌ updateScene FAILED:", error);
    }
  };

  // Handle successful image conversion
  const handleImportSuccess = (result: ExcalidrawScene) => {
    console.log("[ExcalidrawBoard] Import success (final), elements:", result.elements.length);

    // Update Zustand store with final result
    setExcalidrawScene(result);

    toast.success(`Imported ${result.elements.length} elements to Excalidraw!`);
  };

  // Handle streaming element (called during progressive rendering)
  const handleStreamElement = useCallback((element: any) => {
    console.log("[ExcalidrawBoard] Streaming element:", element.id);

    if (!apiRef.current) {
      console.warn("[ExcalidrawBoard] API not ready, cannot stream element");
      return;
    }

    // Get current scene from API
    const currentElements = apiRef.current.getSceneElements();

    // Add new element
    const updatedElements = [...currentElements, element];

    // Update scene incrementally
    apiRef.current.updateScene({
      elements: updatedElements
    });
  }, []);

  // Expose streaming function to parent via store or window
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).__excalidrawStreamElement = handleStreamElement;
    }
    return () => {
      if (typeof window !== 'undefined') {
        delete (window as any).__excalidrawStreamElement;
      }
    };
  }, [handleStreamElement]);

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
      {/* Excalidraw Canvas - Upload button moved to AiControlPanel */}
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
    </div>
  );
}
