import * as dagre from "dagre";
import { Node, Edge } from "reactflow";

export interface LayoutOptions {
  direction?: "TB" | "LR" | "BT" | "RL";
  ranksep?: number;
  nodesep?: number;
  align?: string;
  rankdir?: string;
}

/**
 * Estimate node size based on label length and node type
 */
export function estimateNodeSize(node: Node): { width: number; height: number } {
  const baseWidth = 180;
  const baseHeight = 60;

  // Get label from node data
  const label = node.data?.label || "";

  // Adjust width based on label length
  const charWidth = 8;
  const estimatedWidth = Math.max(baseWidth, label.length * charWidth + 40);

  // Adjust height for multi-line labels
  const lines = Math.ceil(label.length / 20);
  const estimatedHeight = baseHeight + (lines - 1) * 20;

  // Special handling for different node types
  const nodeType = node.type || "default";

  switch (nodeType) {
    case "start-event":
    case "end-event":
    case "intermediate-event":
      // Circular BPMN nodes
      return { width: 60, height: 60 };
    case "gateway":
      // Diamond-shaped gateway nodes
      return { width: 80, height: 80 };
    case "task":
    case "api":
    case "service":
    case "database":
      return { width: estimatedWidth, height: estimatedHeight };
    default:
      return { width: estimatedWidth, height: estimatedHeight };
  }
}

/**
 * Apply dagre layout algorithm to nodes and edges with collision prevention.
 *
 * Optimized to prevent overlaps and ensure proper spacing (inspired by backend collision detection).
 */
export function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  const {
    direction = "TB",
    ranksep = 180,  // Increased from 150 to 180 for more vertical spacing (matches backend MIN_V_SPACING)
    nodesep = 200,   // Increased from 120 to 200 for more horizontal spacing (matches backend MIN_H_SPACING)
  } = options;

  // Create a new directed graph
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Set graph direction and spacing
  dagreGraph.setGraph({
    rankdir: direction,
    ranksep,
    nodesep,
    marginx: 80,   // Increased from 50 for better margins
    marginy: 80,   // Increased from 50 for better margins
    align: "UL",   // Align upper-left for consistency
    acyclicer: "greedy",  // Better cycle handling
    ranker: "tight-tree",  // Use tight-tree ranker for more compact layouts
  });

  // Add nodes to the graph with accurate size estimation
  nodes.forEach((node) => {
    const { width, height } = estimateNodeSize(node);
    dagreGraph.setNode(node.id, { width, height });
  });

  // Add edges to the graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate the layout
  dagre.layout(dagreGraph);

  // Apply the layout to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    // dagre gives us the center position, but React Flow needs top-left
    const { width, height } = estimateNodeSize(node);

    return {
      ...node,
      position: {
        x: nodeWithPosition.x - width / 2,
        y: nodeWithPosition.y - height / 2,
      },
    };
  });

  return layoutedNodes;
}

/**
 * Detect and fix overlapping nodes after layout calculation.
 *
 * This is a client-side safeguard in case backend collision detection is bypassed
 * or nodes are manually repositioned.
 *
 * @param nodes - List of nodes to check for overlaps
 * @returns List of nodes with corrected positions
 */
export function fixNodeOverlaps(nodes: Node[]): Node[] {
  if (nodes.length <= 1) return nodes;

  const MIN_H_GAP = 200; // Minimum horizontal gap (center to center)
  const MIN_V_GAP = 180; // Minimum vertical gap (center to center)

  const nodeDimensions = new Map<string, { width: number; height: number }>();
  nodes.forEach(node => {
    nodeDimensions.set(node.id, estimateNodeSize(node));
  });

  function nodesOverlap(node1: Node, node2: Node): boolean {
    const dims1 = nodeDimensions.get(node1.id)!;
    const dims2 = nodeDimensions.get(node2.id)!;

    const center1 = { x: node1.position.x + dims1.width / 2, y: node1.position.y + dims1.height / 2 };
    const center2 = { x: node2.position.x + dims2.width / 2, y: node2.position.y + dims2.height / 2 };

    const dx = Math.abs(center1.x - center2.x);
    const dy = Math.abs(center1.y - center2.y);

    const minDx = (dims1.width + dims2.width) / 2 + 20;
    const minDy = (dims1.height + dims2.height) / 2 + 20;

    return dx < minDx && dy < minDy;
  }

  const fixedNodes: Node[] = [];

  for (const node of nodes) {
    let adjustedNode = { ...node };
    let iterations = 0;
    const MAX_ITERATIONS = 10;

    while (iterations < MAX_ITERATIONS) {
      let hasCollision = false;

      for (const fixedNode of fixedNodes) {
        if (nodesOverlap(adjustedNode, fixedNode)) {
          hasCollision = true;

          // If on same row, push right; otherwise push down
          if (Math.abs(adjustedNode.position.y - fixedNode.position.y) < 50) {
            adjustedNode.position.x = fixedNode.position.x + MIN_H_GAP;
          } else {
            adjustedNode.position.y = fixedNode.position.y + MIN_V_GAP;
          }

          break;
        }
      }

      if (!hasCollision) break;
      iterations++;
    }

    fixedNodes.push(adjustedNode);
  }

  return fixedNodes;
}

