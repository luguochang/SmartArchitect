import dagre from "dagre";
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
 * Apply dagre layout algorithm to nodes and edges
 */
export function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  const {
    direction = "TB",
    ranksep = 100,
    nodesep = 80,
  } = options;

  // Create a new directed graph
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Set graph direction and spacing
  dagreGraph.setGraph({
    rankdir: direction,
    ranksep,
    nodesep,
    marginx: 50,
    marginy: 50,
  });

  // Add nodes to the graph
  nodes.forEach((node) => {
    const width = node.width || 180;
    const height = node.height || 60;
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
    const width = node.width || 180;
    const height = node.height || 60;

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
