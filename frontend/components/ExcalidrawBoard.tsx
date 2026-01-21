"use client";

import dynamic from "next/dynamic";
import "@excalidraw/excalidraw/index.css";
import { useEffect, useRef } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

// Type import - using any to avoid build-time type errors
type ExcalidrawImperativeAPI = any;

const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="p-4 text-sm text-slate-500">Loading Excalidraw…</div> }
);

export default function ExcalidrawBoard() {
  const apiRef = useRef<ExcalidrawImperativeAPI | null>(null);
  const scene = useArchitectStore((s) => s.excalidrawScene);
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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

  // Update scene when scene data changes (if API is ready)
  useEffect(() => {
    if (!apiRef.current || !scene?.elements) {
      return;
    }

    updateScene(apiRef.current, scene);
  }, [scene]);

  return (
    <div className="h-full w-full bg-white dark:bg-slate-900">
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
