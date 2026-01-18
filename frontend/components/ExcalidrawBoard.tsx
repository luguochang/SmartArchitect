"use client";

import dynamic from "next/dynamic";
import "@excalidraw/excalidraw/index.css";
import { useEffect, useRef, useState } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types/types";

const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="p-4 text-sm text-slate-500">Loading Excalidraw…</div> }
);

export default function ExcalidrawBoard() {
  const apiRef = useRef<ExcalidrawImperativeAPI | null>(null);
  const scene = useArchitectStore((s) => s.excalidrawScene);

  console.log("[ExcalidrawBoard] Render, scene elements:", scene?.elements?.length || 0);

  useEffect(() => {
    console.log("[ExcalidrawBoard] Effect: api=", !!apiRef.current, "scene=", !!scene);

    if (!apiRef.current || !scene?.elements) {
      console.log("[ExcalidrawBoard] Waiting...");
      return;
    }

    console.log("[ExcalidrawBoard] CALLING updateScene with", scene.elements.length, "elements");
    console.log("[ExcalidrawBoard] First element:", scene.elements[0]);

    try {
      // 设置完整的 appState
      const appState = {
        viewBackgroundColor: "#ffffff",
        zoom: { value: 1 },
        scrollX: 0,
        scrollY: 0,
        ...scene.appState
      };

      apiRef.current.updateScene({
        elements: scene.elements,
        appState
      });

      console.log("[ExcalidrawBoard] ✅ updateScene SUCCESS");

      // 强制滚动到内容
      setTimeout(() => {
        if (apiRef.current) {
          console.log("[ExcalidrawBoard] Scrolling to content...");
          apiRef.current.scrollToContent();
          console.log("[ExcalidrawBoard] ✅ Scrolled");
        }
      }, 100);

    } catch (error) {
      console.error("[ExcalidrawBoard] ❌ updateScene FAILED:", error);
    }
  }, [scene]);

  return (
    <div className="h-full w-full bg-white dark:bg-slate-900">
      <Excalidraw
        excalidrawAPI={(api) => {
          console.log("[ExcalidrawBoard] API callback fired");
          apiRef.current = api;
        }}
        initialData={{
          elements: [],
          appState: { viewBackgroundColor: "#ffffff" }
        }}
      />
    </div>
  );
}
