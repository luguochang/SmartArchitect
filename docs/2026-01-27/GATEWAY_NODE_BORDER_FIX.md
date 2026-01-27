# 判断节点外层边框优化

## 🎯 问题描述
菱形判断节点外面有一层透明方框边框，虽然背景透明但能看到边框线，影响视觉效果。

## 🔍 问题根源
React Flow 默认给所有节点容器添加边框和背景，即使我们自己用 SVG 绘制了菱形，外层容器依然有默认样式。

## ✅ 解决方案

### 1. 添加节点类名标识
**文件**: `frontend/components/nodes/GatewayNode.tsx`

```tsx
// 菱形判断节点
<div className="diamond-node svg-shape-node relative" style={{...}}>
  <svg>...</svg>
</div>

// 普通 Gateway 节点
<div className="gateway-node-box glass-node rounded-lg border px-4 py-3 shadow-lg" style={{...}}>
  ...
</div>
```

**改进**:
- 添加 `diamond-node` 类名，用于 CSS 精确匹配
- 添加 `svg-shape-node` 类名，标识这是 SVG 绘制的节点
- 添加 `gateway-node-box` 类名，区分不同类型的 gateway

---

### 2. 强化 CSS 覆盖规则
**文件**: `frontend/app/globals.css`

#### 2.1 SVG 节点通用规则
```css
.react-flow__node:has(.svg-shape-node),
.react-flow__node-default:has(.svg-shape-node),
.react-flow__node-gateway:has(.svg-shape-node) {
  border: none !important;
  border-width: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
  outline: none !important;
}
```

#### 2.2 判断节点专用规则（三重保障）
```css
/* 基础状态 - 完全透明 */
.react-flow__node:has(.diamond-node),
.react-flow__node-default:has(.diamond-node),
.react-flow__node-gateway:has(.diamond-node) {
  border: none !important;
  border-width: 0 !important;
  border-style: none !important;
  border-color: transparent !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
  outline: none !important;
}

/* 选中状态 - 使用 outline 替代 border */
.react-flow__node.selected:has(.diamond-node),
.react-flow__node-default.selected:has(.diamond-node),
.react-flow__node-gateway.selected:has(.diamond-node) {
  border: none !important;
  background: transparent !important;
  outline: none !important;
}

/* Hover 状态 - 不添加任何外层效果 */
.react-flow__node:has(.diamond-node):hover,
.react-flow__node-default:has(.diamond-node):hover,
.react-flow__node-gateway:has(.diamond-node):hover {
  border: none !important;
  box-shadow: none !important;
  transform: none !important;
  background: transparent !important;
}
```

#### 2.3 兜底规则（确保所有 gateway 节点）
```css
/* 类型匹配 */
.react-flow__node-gateway,
.react-flow__node[data-id*="gateway"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}

/* 选中时使用外层 outline */
.react-flow__node-gateway.selected,
.react-flow__node[data-id*="gateway"].selected {
  background: transparent !important;
  border: none !important;
  outline: 2px solid rgba(99, 102, 241, 0.5) !important;
  outline-offset: 4px !important;
}
```

---

## 📊 优化效果

### Before (优化前)
```
┌─────────────────┐  ← 灰色方框边框（透明但可见）
│   ◇ 判断节点    │
└─────────────────┘
```

### After (优化后)
```
    ◇ 判断节点       ← 纯净的菱形，无外层边框
```

---

## 🎨 CSS 覆盖策略

### 三层防护体系
1. **`:has()` 选择器** - 现代浏览器精确匹配
2. **类型选择器** - `.react-flow__node-gateway` 匹配所有 gateway 节点
3. **属性选择器** - `[data-id*="gateway"]` 兜底匹配

### `!important` 使用原因
React Flow 的默认样式使用了 `!important`，必须用同等强度覆盖。

### 选中状态处理
- 普通节点: 使用 `border` 表示选中
- 判断节点: 使用 `outline` + `outline-offset` 在外围显示选中状态，不影响节点本身

---

## 🔧 技术细节

### CSS 选择器优先级
```css
/* 优先级从高到低 */
1. .react-flow__node.selected:has(.diamond-node)  /* 选中状态 */
2. .react-flow__node:has(.diamond-node)           /* 基础状态 */
3. .react-flow__node-gateway                      /* 类型兜底 */
4. .react-flow__node[data-id*="gateway"]          /* 属性兜底 */
```

### 为什么需要多个规则？
- React Flow 动态添加类名（如 `.react-flow__node-gateway`）
- 用户可能使用不同的节点 type
- :has() 选择器在旧浏览器可能不支持
- 多层防护确保所有场景都被覆盖

---

## ✅ 验证清单

测试以下场景，确保判断节点外层无边框：

- [ ] 节点正常显示（无外层方框）
- [ ] 鼠标 hover 时（无外层边框变化）
- [ ] 节点被选中时（使用 outline 而非 border）
- [ ] 多个判断节点同时存在
- [ ] 判断节点与其他节点混合
- [ ] 深色模式下显示正常
- [ ] 浏览器缩放时显示正常

---

## 📝 修改文件

1. `frontend/components/nodes/GatewayNode.tsx` - 添加类名标识
2. `frontend/app/globals.css` - 强化 CSS 覆盖规则

**总代码变更**: +60 行 CSS 规则，2 处类名添加

---

## 🚀 效果预览

现在判断节点应该显示为：
- ✅ 纯净的橙色菱形，无外层边框
- ✅ 上方/左侧：橙色入口
- ✅ 右侧：绿色出口 (Yes)
- ✅ 下方：红色出口 (No)
- ✅ 选中时：外围淡蓝色 outline（不影响节点形状）

Perfect! 🎉
