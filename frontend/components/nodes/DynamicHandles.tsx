import { Handle, Position } from "reactflow";

interface DynamicHandlesProps {
  color: string;
}

/**
 * Dynamic bidirectional handles - each direction can be both source and target
 * Allows React Flow to automatically choose the optimal connection point
 */
export function DynamicHandles({ color }: DynamicHandlesProps) {
  return (
    <>
      {/* Top - both source and target */}
      <Handle
        id="top-target"
        type="target"
        position={Position.Top}
        style={{
          backgroundColor: color,
          top: 0,
          left: "50%",
          transform: "translate(-50%, -50%)",
        }}
      />
      <Handle
        id="top-source"
        type="source"
        position={Position.Top}
        style={{
          backgroundColor: color,
          top: 0,
          left: "50%",
          transform: "translate(-50%, -50%)",
        }}
      />

      {/* Right - both source and target */}
      <Handle
        id="right-target"
        type="target"
        position={Position.Right}
        style={{
          backgroundColor: color,
          top: "50%",
          right: 0,
          transform: "translate(50%, -50%)",
        }}
      />
      <Handle
        id="right-source"
        type="source"
        position={Position.Right}
        style={{
          backgroundColor: color,
          top: "50%",
          right: 0,
          transform: "translate(50%, -50%)",
        }}
      />

      {/* Bottom - both source and target */}
      <Handle
        id="bottom-target"
        type="target"
        position={Position.Bottom}
        style={{
          backgroundColor: color,
          bottom: 0,
          left: "50%",
          transform: "translate(-50%, 50%)",
        }}
      />
      <Handle
        id="bottom-source"
        type="source"
        position={Position.Bottom}
        style={{
          backgroundColor: color,
          bottom: 0,
          left: "50%",
          transform: "translate(-50%, 50%)",
        }}
      />

      {/* Left - both source and target */}
      <Handle
        id="left-target"
        type="target"
        position={Position.Left}
        style={{
          backgroundColor: color,
          top: "50%",
          left: 0,
          transform: "translate(-50%, -50%)",
        }}
      />
      <Handle
        id="left-source"
        type="source"
        position={Position.Left}
        style={{
          backgroundColor: color,
          top: "50%",
          left: 0,
          transform: "translate(-50%, -50%)",
        }}
      />
    </>
  );
}
