"use client";

import { memo, useState, useCallback } from "react";
import { NodeProps } from "reactflow";
import { Box } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { DynamicHandles } from "./DynamicHandles";
import { useNodeStyle } from "@/lib/hooks/useNodeStyle";

export const ServiceNode = memo(({ id, data }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  const updateNodeLabel = useArchitectStore((state) => state.updateNodeLabel);

  // 获取样式配置
  const nodeStyle = useNodeStyle("service", data.shape);

  const handleDoubleClick = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
    if (label.trim() && label !== data.label) {
      updateNodeLabel(id, label.trim());
    } else {
      setLabel(data.label);
    }
  }, [id, label, data.label, updateNodeLabel]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      (e.target as HTMLInputElement).blur();
    } else if (e.key === "Escape") {
      setLabel(data.label);
      setIsEditing(false);
    }
  }, [data.label]);

  return (
    <div
      className="glass-node relative"
      style={nodeStyle.container}
    >
      {/* 动态双向连接点 */}
      <DynamicHandles color={nodeStyle.borderColor} />

      {/* 只在非专业模式下显示装饰条 */}
      {nodeStyle.showIcons && (
        <span
          className="absolute left-2 top-2 h-[calc(100%-16px)] w-[5px] rounded-full opacity-80"
          style={{ backgroundColor: nodeStyle.borderColor }}
        />
      )}

      <div className="flex items-center gap-3" style={{
        justifyContent: nodeStyle.showIcons ? "flex-start" : "center",
      }}>
        {/* 只在showIcons为true时显示图标 */}
        {nodeStyle.showIcons && (
          <Box
            className="h-5 w-5 transition-transform duration-200 hover:scale-110"
            style={{ color: nodeStyle.borderColor }}
          />
        )}

        <div className="flex-1" style={{
          textAlign: nodeStyle.showIcons ? "left" : "center",
        }}>
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag bg-transparent border-b-2 outline-none"
              style={{
                ...nodeStyle.typography,
                borderColor: nodeStyle.borderColor,
                width: `${Math.max(label.length, 8)}ch`,
              }}
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className="cursor-text"
              style={nodeStyle.typography}
            >
              {data.label}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

ServiceNode.displayName = "ServiceNode";
