# 剩余节点更新说明

以下节点需要应用相同的 DynamicHandles 更新模式：

## QueueNode.tsx
1. 修改导入: `import { NodeProps } from "reactflow";` + `import { DynamicHandles } from "./DynamicHandles";`
2. 移除: `import { Handle, Position, NodeProps } from "reactflow";`
3. 替换所有 Handle 标签为: `<DynamicHandles color="var(--queue-border)" />`

## StorageNode.tsx
1. 修改导入: `import { NodeProps } from "reactflow";` + `import { DynamicHandles } from "./DynamicHandles";`
2. 移除: `import { Handle, Position, NodeProps } from "reactflow";`
3. 替换所有 Handle 标签为: `<DynamicHandles color="var(--storage-border)" />`

## ClientNode.tsx
1. 修改导入: `import { NodeProps } from "reactflow";` + `import { DynamicHandles } from "./DynamicHandles";`
2. 移除: `import { Handle, Position, NodeProps } from "reactflow";`
3. 替换所有 Handle 标签为: `<DynamicHandles color="var(--client-border)" />`

## 替换模式

将以下代码块:
```tsx
{/* Input handles - Top and Left */}
<Handle id="target-top" ... />
<Handle id="target-left" ... />
{/* Output handles - Right and Bottom */}
<Handle id="source-right" ... />
<Handle id="source-bottom" ... />
```

替换为:
```tsx
<DynamicHandles color="var(--[node-type]-border)" />
```
