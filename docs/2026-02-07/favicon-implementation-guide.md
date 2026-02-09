# Favicon 和页面标题实施指南

## 快速开始

本指南将帮助你在 5 分钟内完成 SmartArchitect AI 的品牌标识配置。

## 📋 前置条件

- Node.js 已安装
- 前端开发服务器可运行
- 基本的命令行知识

## 🚀 实施步骤

### 第一步：安装依赖

```bash
cd frontend
npm install sharp --save-dev
```

### 第二步：生成图标资源

```bash
# 运行图标生成脚本
node scripts/generate-icons.js
```

这将生成以下文件：
- ✅ `app/apple-icon.png` (180x180) - Apple 设备图标
- ✅ `public/icons/icon-192.png` - Android 小图标
- ✅ `public/icons/icon-512.png` - Android 大图标
- ✅ `public/icons/icon-maskable.png` - Android Maskable 图标
- ✅ `public/icons/favicon-16.png` - 小尺寸 Favicon
- ✅ `public/icons/favicon-32.png` - 标准 Favicon

### 第三步：生成 favicon.ico（可选）

由于 ICO 格式需要特殊处理，你可以选择以下方式之一：

**方式 A：在线转换（推荐，最简单）**
1. 访问 [Real Favicon Generator](https://realfavicongenerator.net/)
2. 上传 `app/icon.svg`
3. 下载生成的 `favicon.ico`
4. 将其放到 `frontend/app/` 目录

**方式 B：使用命令行工具**
```bash
# 安装 png-to-ico
npm install -g png-to-ico

# 生成 favicon.ico
png-to-ico public/icons/favicon-32.png --out app/favicon.ico
```

**方式 C：跳过（SVG 已足够）**
现代浏览器支持 SVG favicon，可以暂时跳过 ICO 格式。

### 第四步：创建 Open Graph 图片（可选但推荐）

为社交媒体分享创建预览图：

1. 使用 Figma/Canva 设计一个 1200x630 的图片
2. 包含 SmartArchitect AI logo 和简短描述
3. 保存为 `public/og-image.png`

**设计要点：**
- 背景：深色（#0f172a）或浅色（#ffffff）
- 主标题：SmartArchitect AI
- 副标题：AI-Powered Architecture Design
- 图标/示例：流程图或架构图截图

**快速生成方法（使用 Canvas API）：**
```bash
node scripts/generate-og-image.js
```

### 第五步：验证配置

启动开发服务器并验证：

```bash
npm run dev
```

**验证清单：**
- [ ] 浏览器标签页显示正确图标
- [ ] 页面标题为 "SmartArchitect AI - AI-Powered Architecture Design Platform"
- [ ] 使用浏览器开发工具检查 `<head>` 中的元数据
- [ ] 暗色模式下图标清晰可见
- [ ] 移动端浏览器图标正常

**开发工具验证：**
```javascript
// 在浏览器控制台运行
document.querySelector('link[rel="icon"]').href
document.querySelector('meta[property="og:title"]').content
document.querySelector('meta[name="theme-color"]').content
```

### 第六步：测试 PWA 功能（可选）

1. 在 Chrome/Edge 中打开应用
2. 点击地址栏右侧的"安装"图标（如果支持）
3. 验证安装后的应用图标和名称
4. 测试离线功能（需要额外配置 Service Worker）

## 🎨 自定义品牌

### 修改品牌色

编辑 `app/icon.svg` 中的颜色：

```svg
<!-- 主品牌色（当前：Indigo #4F46E5） -->
<circle cx="64" cy="64" r="60" fill="#4F46E5"/>

<!-- 辅助色（当前：Emerald #10B981） -->
<g fill="#10B981">
```

推荐的品牌色组合：
- **科技蓝**：`#2563eb` + `#14b8a6`
- **创新紫**：`#7c3aed` + `#ec4899`
- **专业深蓝**：`#1e40af` + `#0ea5e9`

### 修改图标设计

`app/icon.svg` 的设计概念是流程图风格的抽象字母：
- 上部：输入节点（矩形）
- 中部：决策节点（菱形）
- 下部：输出节点（矩形）
- 右侧：AI 智能光点（动画）

你可以根据需要修改：
1. 节点形状和大小
2. 连接线样式
3. 光点位置和动画
4. 整体布局

### 修改页面标题模板

编辑 `app/layout.tsx`:

```typescript
export const metadata: Metadata = {
  title: {
    default: "你的自定义标题",
    template: "%s | 你的品牌名"
  },
  // ...
};
```

### 为不同页面设置不同标题

在页面组件中覆盖标题：

```typescript
// app/docs/page.tsx
export const metadata = {
  title: "Documentation",  // 将变成 "Documentation | SmartArchitect AI"
  description: "Complete guide to using SmartArchitect AI"
};
```

## 📊 效果预览

### 浏览器标签页
- **Chrome/Edge**: 显示彩色 SVG 图标 + 完整标题
- **Firefox**: 显示 SVG 图标（支持动画）
- **Safari**: 显示 Apple Touch Icon

### 移动设备
- **iOS**: 添加到主屏幕显示 apple-icon.png
- **Android**: 显示 icon-192.png 或 icon-maskable.png

### 社交媒体
- **Facebook/LinkedIn**: 显示 og-image.png (1200x630)
- **Twitter**: 显示 twitter-card.png (1200x600)
- **Slack/Discord**: 显示 og-image.png

## 🐛 常见问题

### Q: 图标不显示？
**A:**
1. 清除浏览器缓存（Ctrl+Shift+R）
2. 检查文件路径是否正确
3. 验证 SVG 语法是否有错误
4. 查看浏览器控制台的网络请求

### Q: 深色模式下图标看不清？
**A:**
1. 确保 SVG 使用白色填充
2. 或在 `icon.svg` 中添加媒体查询：
```svg
<style>
  @media (prefers-color-scheme: dark) {
    circle { fill: #1e293b; }
  }
</style>
```

### Q: manifest.json 不生效？
**A:**
1. 确保 `layout.tsx` 中有 `manifest: "/manifest.json"`
2. 检查 JSON 格式是否正确（使用 JSONLint 验证）
3. 清除浏览器缓存并重新加载

### Q: Open Graph 图片不显示？
**A:**
1. 确保图片路径是绝对 URL（不是相对路径）
2. 图片尺寸必须是 1200x630
3. 使用 [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) 测试
4. 缓存可能需要几小时才能更新

### Q: 图标生成脚本失败？
**A:**
```bash
# 确保 sharp 已正确安装
npm install sharp --save-dev

# 检查 Node.js 版本（需要 14+）
node --version

# 手动运行并查看详细错误
node scripts/generate-icons.js
```

## 🔧 高级配置

### 添加动态标题

创建一个 hook 来动态更新标题：

```typescript
// hooks/useDocumentTitle.ts
import { useEffect } from 'react';

export function useDocumentTitle(title: string, suffix = true) {
  useEffect(() => {
    const fullTitle = suffix
      ? `${title} | SmartArchitect AI`
      : title;
    document.title = fullTitle;
  }, [title, suffix]);
}

// 使用示例
function MyComponent() {
  const nodeCount = useArchitectStore(s => s.nodes.length);
  useDocumentTitle(`${nodeCount} nodes`);
  // 标题变为: "12 nodes | SmartArchitect AI"
}
```

### 添加未保存状态提示

```typescript
function Canvas() {
  const hasUnsavedChanges = useArchitectStore(s => s.hasChanges);

  useDocumentTitle(
    hasUnsavedChanges ? "* Unsaved Changes" : "Canvas"
  );
}
```

### 配置 PWA Service Worker

```bash
# 安装 next-pwa
npm install next-pwa

# 配置 next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
});

module.exports = withPWA({
  // 你的 Next.js 配置
});
```

### 生成多语言 manifest

```javascript
// public/manifest-zh.json (中文版)
{
  "name": "SmartArchitect AI - AI 架构设计平台",
  "short_name": "SmartArchitect",
  "description": "使用 AI 将架构图转换为可编辑代码",
  // ...
}

// layout.tsx 中根据语言选择
<link rel="manifest" href={`/manifest-${locale}.json`} />
```

## 📚 参考资源

### 设计工具
- [Figma](https://figma.com) - 图标和 OG Image 设计
- [Canva](https://canva.com) - 快速生成社交媒体图片
- [SVGOMG](https://jakearchibald.github.io/svgomg/) - SVG 优化工具

### 图标生成
- [Real Favicon Generator](https://realfavicongenerator.net/) - 全面的 Favicon 生成器
- [Favicon.io](https://favicon.io/) - 简单的 Favicon 工具
- [PWA Builder](https://www.pwabuilder.com/) - PWA 图标和 Manifest 生成

### 验证工具
- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) - OG 标签测试
- [Twitter Card Validator](https://cards-dev.twitter.com/validator) - Twitter Card 测试
- [Google Rich Results Test](https://search.google.com/test/rich-results) - 结构化数据测试
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - PWA 审计

### 文档
- [Next.js Metadata](https://nextjs.org/docs/app/api-reference/functions/generate-metadata)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Open Graph Protocol](https://ogp.me/)
- [Twitter Cards](https://developer.twitter.com/en/docs/twitter-for-websites/cards/overview/abouts-cards)

## ✅ 完成检查清单

部署前确保所有项目已完成：

### 必需项
- [ ] SVG 图标已创建并优化
- [ ] 浏览器标签页图标正常显示
- [ ] 页面标题符合 SEO 最佳实践
- [ ] manifest.json 配置正确
- [ ] 深色模式支持
- [ ] 移动端图标清晰

### 推荐项
- [ ] Open Graph 图片已创建
- [ ] Twitter Card 图片已创建
- [ ] Apple Touch Icon 已配置
- [ ] PWA 安装功能测试通过
- [ ] 多尺寸图标全部生成
- [ ] 社交媒体分享预览正常

### 优化项
- [ ] 图标文件已压缩（< 50KB）
- [ ] SVG 文件已优化（< 2KB）
- [ ] 动态标题功能已实现
- [ ] 未保存状态提示已添加
- [ ] 多语言支持（如需要）
- [ ] Service Worker 配置（如需要）

## 🎉 下一步

品牌标识配置完成后，你可以：
1. 部署到生产环境并测试
2. 在社交媒体上分享，查看预览效果
3. 收集用户反馈，持续优化
4. 添加更多品牌元素（启动画面、加载动画等）

祝你的 SmartArchitect AI 项目越来越好！🚀
