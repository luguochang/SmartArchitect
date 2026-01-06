"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Globe } from "lucide-react";

export const ApiNode = memo(({ data }: NodeProps) => {
  return (
    <div className="rounded-lg border-2 border-blue-500 bg-white px-4 py-3 shadow-lg dark:bg-slate-800">
      <Handle type="target" position={Position.Left} className="!bg-blue-500" />

      <div className="flex items-center gap-2">
        <Globe className="h-5 w-5 text-blue-600" />
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">
            {data.label}
          </div>
          <div className="text-xs text-slate-500">API</div>
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-blue-500" />
    </div>
  );
});

ApiNode.displayName = "ApiNode";
