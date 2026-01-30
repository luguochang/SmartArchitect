import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  FlowchartPresentationStyle,
  FontStyleOption,
  FLOWCHART_PRESENTATION_STYLES,
  FONT_STYLE_OPTIONS,
  DEFAULT_PRESENTATION_STYLE_ID,
  DEFAULT_FONT_STYLE_ID,
  getPresentationStyleById,
  getFontStyleById,
} from "@/lib/themes/flowchartPresentationStyles";

interface FlowchartStyleState {
  // Current selected style IDs
  presentationStyleId: string;
  fontStyleId: string;

  // Computed styles (derived from IDs)
  currentPresentationStyle: FlowchartPresentationStyle;
  currentFontStyle: FontStyleOption;

  // Actions
  setPresentationStyle: (styleId: string) => void;
  setFontStyle: (fontId: string) => void;
  resetToDefaults: () => void;

  // Computed helper properties
  showIcons: boolean;
  edgeType: "orthogonal" | "straight" | "smoothstep" | "step";
}

/**
 * Flowchart Style Store
 *
 * Manages the professional presentation styles for React Flow flowcharts.
 * Persists user preferences to localStorage.
 */
export const useFlowchartStyleStore = create<FlowchartStyleState>()(
  persist(
    (set, get) => {
      // Helper function to recompute derived state
      const recomputeStyles = (
        presentationStyleId: string,
        fontStyleId: string
      ) => {
        const presentationStyle =
          getPresentationStyleById(presentationStyleId) ||
          FLOWCHART_PRESENTATION_STYLES[DEFAULT_PRESENTATION_STYLE_ID];

        const fontStyle =
          getFontStyleById(fontStyleId) ||
          FONT_STYLE_OPTIONS[DEFAULT_FONT_STYLE_ID];

        return {
          presentationStyleId,
          fontStyleId,
          currentPresentationStyle: presentationStyle,
          currentFontStyle: fontStyle,
          showIcons: presentationStyle.node.showIcons,
          edgeType: presentationStyle.edge.type,
        };
      };

      return {
        ...recomputeStyles(DEFAULT_PRESENTATION_STYLE_ID, DEFAULT_FONT_STYLE_ID),

        setPresentationStyle: (styleId: string) => {
          const { fontStyleId } = get();
          set(recomputeStyles(styleId, fontStyleId));
        },

        setFontStyle: (fontId: string) => {
          const { presentationStyleId } = get();
          set(recomputeStyles(presentationStyleId, fontId));
        },

        resetToDefaults: () => {
          set(recomputeStyles(DEFAULT_PRESENTATION_STYLE_ID, DEFAULT_FONT_STYLE_ID));
        },
      };
    },
    {
      name: "flowchart-presentation-style-storage",
      // Only persist the IDs, not the computed styles
      partialize: (state) => ({
        presentationStyleId: state.presentationStyleId,
        fontStyleId: state.fontStyleId,
      }),
    }
  )
);
