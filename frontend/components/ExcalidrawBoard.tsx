"use client";

import dynamic from "next/dynamic";
import "@excalidraw/excalidraw/index.css";
import { useEffect, useRef } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { sanitizeExcalidrawData } from "@/lib/excalidrawUtils";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types/types";

const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="p-4 text-sm text-slate-500">Loading Excalidraw…</div> }
);

export default function ExcalidrawBoard() {
  const apiRef = useRef<ExcalidrawImperativeAPI | null>(null);
  const scene = useArchitectStore((s) => s.excalidrawScene);

  useEffect(() => {
    if (apiRef.current && scene) {
      // Sanitize scene data before rendering to prevent crashes
      const sanitized = sanitizeExcalidrawData(scene);

      if (sanitized && sanitized.elements.length > 0) {
        console.log(`[Excalidraw] Updating scene with ${sanitized.elements.length} validated elements`);
        apiRef.current.updateScene({
          elements: sanitized.elements,
          appState: sanitized.appState || {},
        });
      } else {
        console.warn("[Excalidraw] Scene validation failed or resulted in empty elements");
      }
    }
  }, [scene]);

  return (
    <div className="h-full w-full bg-white dark:bg-slate-900">
      <Excalidraw excalidrawAPI={(api) => (apiRef.current = api)} />
    </div>
  );
}
