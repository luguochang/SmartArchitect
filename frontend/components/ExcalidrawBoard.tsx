"use client";

import dynamic from "next/dynamic";
import "@excalidraw/excalidraw/index.css";
import { useEffect, useRef } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import {
  getElementsWithValidBounds,
  sanitizeExcalidrawData,
} from "@/lib/excalidrawUtils";

type ExcalidrawImperativeAPI = any;

const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  {
    ssr: false,
    loading: () => <div className="p-4 text-sm text-slate-500">Loading Excalidraw...</div>,
  }
);

export default function ExcalidrawBoard() {
  const apiRef = useRef<ExcalidrawImperativeAPI | null>(null);
  const scene = useArchitectStore((s) => s.excalidrawScene);
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const updateScene = (
    api: ExcalidrawImperativeAPI,
    rawScene: typeof scene
  ) => {
    if (!rawScene?.elements || rawScene.elements.length === 0) {
      return;
    }

    const sceneData = sanitizeExcalidrawData(rawScene);
    if (!sceneData || sceneData.elements.length === 0) {
      return;
    }

    const isStreaming = Boolean((sceneData.appState as any)?.__streaming);

    api.updateScene({
      elements: sceneData.elements,
      appState: {
        viewBackgroundColor: "#ffffff",
        ...sceneData.appState,
      },
    });

    if (isStreaming) {
      return;
    }

    if (updateTimeoutRef.current) {
      clearTimeout(updateTimeoutRef.current);
    }

    // Keep generated content fully visible so large diagrams do not look clipped.
    updateTimeoutRef.current = setTimeout(() => {
      const targetElements = getElementsWithValidBounds(sceneData.elements);
      if (!apiRef.current) {
        return;
      }

      if (targetElements.length > 0) {
        apiRef.current.scrollToContent(targetElements, {
          fitToViewport: true,
          viewportZoomFactor: 0.9,
          animate: true,
          duration: 280,
          minZoom: 0.2,
          maxZoom: 1.2,
        });
      } else {
        apiRef.current.scrollToContent(undefined, {
          fitToViewport: true,
          viewportZoomFactor: 0.9,
          animate: true,
          duration: 280,
          minZoom: 0.2,
          maxZoom: 1.2,
        });
      }
    }, 220);
  };

  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!apiRef.current || !scene?.elements || scene.elements.length === 0) {
      return;
    }

    updateScene(apiRef.current, scene);
  }, [scene]);

  return (
    <div className="relative h-full w-full bg-white dark:bg-slate-900">
      <Excalidraw
        excalidrawAPI={(api) => {
          apiRef.current = api;

          const currentScene = useArchitectStore.getState().excalidrawScene;
          if (currentScene?.elements && currentScene.elements.length > 0) {
            setTimeout(() => {
              updateScene(api, currentScene);
            }, 0);
          }
        }}
        initialData={{
          elements: [],
          appState: { viewBackgroundColor: "#ffffff" },
        }}
      />
    </div>
  );
}
