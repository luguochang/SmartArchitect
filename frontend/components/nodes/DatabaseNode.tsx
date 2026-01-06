"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Database } from "lucide-react";

export const DatabaseNode = memo(({ data }: NodeProps) => {
  return (
    <div className="rounded-lg border-2 border-green-500 bg-white px-4 py-3 shadow-lg dark:bg-slate-800">
      <Handle type="target" position={Position.Top} className="!bg-green-500" />

      <div className="flex items-center gap-2">
        <Database className="h-5 w-5 text-green-600" />
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">
            {data.label}
          </div>
          <div className="text-xs text-slate-500">Database</div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-green-500" />
    </div>
  );
});

DatabaseNode.displayName = "DatabaseNode";
