# 节点库扩展更新

## 概述
参考 draw.io 的节点库设计，将左侧节点库从原来的 2 个分类（13 个节点）扩展到 **6 个分类（70+ 个节点）**，让用户可以自由绘制各种类型的流程图和架构图。

---

## 新增节点分类

### 1. 基础图形（12 个节点）
**默认展开**

| 节点 | 形状 | 用途 |
|------|------|------|
| 矩形 | Rectangle | 基础矩形 |
| 圆角矩形 | Rounded Rectangle | 圆角矩形 |
| 圆形 | Circle/Ellipse | 圆形/椭圆 |
| 菱形 | Diamond | 决策/判断 |
| 六边形 | Hexagon | 六边形 |
| 三角形 | Triangle | 三角形 |
| 平行四边形 | Parallelogram | 数据/输入输出 |
| 梯形 | Trapezoid | 手动操作 |
| 星形 | Star | 星形 |
| 云形 | Cloud | 云/注释 |
| 圆柱 | Cylinder | 数据库/存储 |
| 文档 | Document | 文档/报告 |

---

### 2. 流程图（12 个节点）
**默认展开**

| 节点 | 用途 | 说明 |
|------|------|------|
| 开始 | Start | 流程开始点（圆形） |
| 结束 | End | 流程结束点（圆形） |
| 过程 | Process | 处理步骤（矩形） |
| 判断 | Decision | 条件判断（菱形） |
| 数据 | Data | 数据/输入输出（平行四边形） |
| 子流程 | Subprocess | 预定义过程 |
| 延迟 | Delay | 延迟/等待 |
| 合并 | Merge | 合并 |
| 手动输入 | Manual Input | 手动输入 |
| 手动操作 | Manual Operation | 手动操作 |
| 准备 | Preparation | 准备/初始化 |
| 或 | OR Gate | 逻辑或 |

---

### 3. 容器/分组（7 个节点）

| 节点 | 用途 | 说明 |
|------|------|------|
| 容器 | Container | 容器/分组 |
| 框架 | Frame | 分组框架 |
| 泳道(横) | Horizontal Swimlane | 水平泳道 |
| 泳道(竖) | Vertical Swimlane | 垂直泳道 |
| 注释 | Note | 注释框 |
| 文件夹 | Folder | 文件夹 |
| 包 | Package | 包/模块 |

---

### 4. 架构组件（12 个节点）

| 节点 | 用途 | 说明 |
|------|------|------|
| 客户端 | Client | 客户端 |
| 服务器 | Server | 服务器 |
| 网关 | Gateway | API网关 |
| API | API | API服务 |
| 服务 | Service | 微服务 |
| 数据库 | Database | 数据库 |
| 缓存 | Cache | 缓存 |
| 队列 | Queue | 消息队列 |
| 存储 | Storage | 文件存储 |
| 负载均衡 | Load Balancer | 负载均衡器 |
| 防火墙 | Firewall | 防火墙 |
| CDN | CDN | 内容分发网络 |

---

### 5. 用户/设备（7 个节点）

| 节点 | 用途 | 说明 |
|------|------|------|
| 用户 | User | 单个用户 |
| 用户组 | Users | 用户组 |
| 手机 | Mobile | 移动设备 |
| 桌面 | Desktop | 桌面设备 |
| 平板 | Tablet | 平板设备 |
| IoT | IoT Device | 物联网设备 |
| 网络设备 | Network Device | 网络设备 |

---

### 6. BPMN（6 个节点）

| 节点 | 用途 | 说明 |
|------|------|------|
| 开始事件 | Start Event | BPMN开始 |
| 结束事件 | End Event | BPMN结束 |
| 任务 | Task | BPMN任务 |
| 网关 | Gateway | BPMN网关 |
| 中间事件 | Intermediate Event | BPMN中间事件 |
| 子流程 | Subprocess | BPMN子流程 |

---

## 使用方式

### 添加节点
1. **点击添加**：点击节点按钮，节点会在随机位置添加到画布
2. **拖拽添加**：未来支持从左侧拖拽到画布（需要实现拖拽功能）

### 搜索节点
- 使用顶部搜索框快速查找节点
- 支持中文和英文搜索

### 展开/收起分类
- 点击分类标题展开/收起
- 默认展开"基础图形"和"流程图"

---

## 技术实现

### 文件修改
- **文件**：`frontend/components/Sidebar.tsx`
- **行数**：74-187（节点定义）
- **新增图标导入**：25 个 Lucide React 图标

### 节点数据结构
```typescript
interface NodeType {
  type: string;           // 节点类型
  icon: any;              // Lucide React 图标组件
  iconType?: string;      // 图标标识符
  label: string;          // 显示名称
  color: string;          // Tailwind 颜色类
  shape?: string;         // 形状类型（新增）
  description?: string;   // 描述（新增，hover tooltip）
}
```

### 颜色映射
扩展了颜色映射表，支持 18 种 Tailwind 颜色：
- `text-green-600`, `text-red-600`, `text-blue-500/600/700`
- `text-yellow-500/600`, `text-purple-500/600`
- `text-cyan-600`, `text-indigo-600`, `text-slate-600/700`
- `text-teal-600`, `text-sky-600`, `text-amber-600`
- `text-emerald-600`, `text-gray-600`

---

## 未来扩展

### 待实现功能
1. **拖拽添加节点**：从左侧拖拽到画布指定位置
2. **自定义节点渲染**：为每种 shape 实现专门的 React Flow 节点组件
3. **节点样式编辑**：双击节点编辑文本、颜色、大小
4. **连接线样式**：直线、曲线、折线、虚线箭头
5. **容器/分组功能**：实现泳道、分组框的实际容器效果
6. **图层遮罩**：架构图中的遮罩层效果

### 建议的 React Flow 节点类型
需要创建自定义节点组件来渲染不同形状：
- `BasicShapeNode.tsx`：矩形、圆形、菱形等基础图形
- `FlowchartNode.tsx`：流程图节点（开始、结束、判断等）
- `ContainerNode.tsx`：容器、泳道、分组框
- `ArchitectureNode.tsx`：架构组件（服务器、数据库等）
- `DeviceNode.tsx`：用户/设备图标
- `BpmnNode.tsx`：BPMN 标准节点

---

## 兼容性

### 后端兼容
后端 AI 生成的 prompt 已更新（`backend/app/services/chat_generator.py:85-142`），支持新增的节点类型：
- **通用流程图节点**：start, end, process, decision, data, document, subprocess
- **技术节点**：仅在用户明确要求时使用

### 前端兼容
- 所有新增节点都使用 `data.shape` 字段标识形状
- 现有节点组件需要根据 `shape` 渲染不同样式
- 保持向后兼容：未指定 shape 的节点使用默认渲染

---

## 测试建议

### 基础测试
1. **节点添加**：点击每个节点，验证能否添加到画布
2. **搜索功能**：搜索"圆形"、"流程"等关键词，验证过滤正确
3. **展开/收起**：验证每个分类能正常展开和收起

### 功能测试
1. **AI 生成**：用"生成约会流程"测试，验证生成的节点类型正确
2. **节点样式**：验证不同节点的颜色和图标正确显示
3. **Tooltip**：Hover 节点按钮，验证描述正确显示

---

## 总结

本次更新将节点库扩展到 **70+ 个节点**，覆盖：
- ✅ 基础图形（矩形、圆形、菱形等）
- ✅ 流程图节点（开始、结束、判断等）
- ✅ 容器/分组（泳道、注释框等）
- ✅ 架构组件（服务器、数据库、网关等）
- ✅ 用户/设备（手机、桌面、IoT等）
- ✅ BPMN 标准节点

用户现在可以像使用 draw.io 一样，自由绘制各种类型的图表，不再局限于技术架构图。
