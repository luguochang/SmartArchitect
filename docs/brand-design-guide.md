# SmartArchitect AI - 品牌设计指南

## 1. 品牌标识系统

### 1.1 核心视觉元素
- **主图标**: Sparkles (✨) - 代表 AI 智能和创新
- **品牌色**: Indigo (#4F46E5) - 专业、科技感
- **辅助色**: Emerald (#10B981) - 生命力、创造力

### 1.2 设计理念
SmartArchitect AI 是一个 AI 驱动的架构设计平台，品牌设计应该体现：
- 智能化：通过闪光/星光元素体现
- 专业性：使用稳重的 Indigo 色系
- 创新性：结合建筑与 AI 的概念

## 2. Favicon 设计方案

### 2.1 设计概念
将建筑（Architecture）和 AI 智能结合：
- **方案A**: 字母 "SA" 叠加 Sparkles 效果
- **方案B**: 简化的建筑图标 + 智能光点
- **方案C**: 流程图节点样式的 "S" 字母（推荐）

### 2.2 技术实现
- **主图标**: SVG 格式（支持深色模式自动切换）
- **Fallback**: ICO 格式（32x32, 16x16）
- **移动端**: 180x180 PNG (Apple Touch Icon)
- **Android**: 192x192, 512x512 PNG (Web App Manifest)

### 2.3 文件清单
```
frontend/
├── app/
│   ├── favicon.ico          # 传统 ICO 格式 (32x32)
│   ├── icon.svg             # SVG 动态图标（支持深色模式）
│   └── apple-icon.png       # Apple 设备图标 (180x180)
├── public/
│   ├── icons/
│   │   ├── icon-192.png     # Android 小图标
│   │   ├── icon-512.png     # Android 大图标
│   │   └── icon-maskable.png # Android Maskable Icon
│   └── manifest.json        # PWA Web App Manifest
```

## 3. 页面标题策略

### 3.1 标题模板
```
主页: SmartArchitect AI - AI-Powered Architecture Design Platform
功能页: [功能名] | SmartArchitect AI
文档页: [文档标题] | SmartArchitect AI Docs
```

### 3.2 动态标题支持
- 监听画布节点数量，实时更新标题
- 例如: "12 nodes | SmartArchitect AI"
- 监听编辑状态，显示未保存提示: "* Unsaved | SmartArchitect AI"

### 3.3 SEO 优化建议
- Title: 50-60 字符
- Description: 150-160 字符
- Keywords: AI, Architecture, Design, Diagram, Mermaid, React Flow

## 4. 社交媒体元数据

### 4.1 Open Graph (Facebook, LinkedIn)
```html
og:title: SmartArchitect AI - AI Architecture Design Platform
og:description: Transform your architecture diagrams into editable code with AI
og:image: https://yourdomain.com/og-image.png (1200x630)
og:type: website
```

### 4.2 Twitter Card
```html
twitter:card: summary_large_image
twitter:title: SmartArchitect AI
twitter:description: AI-Powered Architecture Design Platform
twitter:image: https://yourdomain.com/twitter-card.png (1200x600)
```

## 5. PWA 支持（可选）

### 5.1 Manifest.json 配置
```json
{
  "name": "SmartArchitect AI",
  "short_name": "SmartArchitect",
  "description": "AI-Powered Architecture Design Platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#4f46e5",
  "icons": [...]
}
```

### 5.2 安装提示
- 支持桌面安装（Chrome, Edge）
- 支持移动端添加到主屏幕（iOS, Android）

## 6. 实施计划

### 第一步：生成 Favicon 资源（15分钟）
1. 使用在线工具生成多尺寸图标
   - 推荐工具: [Favicon Generator](https://realfavicongenerator.net/)
   - 上传设计稿或使用 SVG 代码
2. 或使用命令行工具生成
   ```bash
   npm install -g sharp-cli
   sharp -i icon.png -o icon-192.png resize 192 192
   sharp -i icon.png -o icon-512.png resize 512 512
   ```

### 第二步：更新 Next.js Metadata（10分钟）
1. 修改 `app/layout.tsx` 的 metadata 配置
2. 添加 manifest 链接
3. 添加 Open Graph 和 Twitter Card 元数据

### 第三步：创建 manifest.json（5分钟）
1. 定义应用名称、图标、主题色
2. 配置启动模式和显示方式

### 第四步：测试验证（10分钟）
1. 浏览器标签页图标显示
2. 暗色模式切换
3. PWA 安装功能（可选）
4. 社交媒体分享预览

## 7. 品牌一致性检查清单

- [ ] Favicon 在所有浏览器中正常显示
- [ ] 深色模式下图标清晰可见
- [ ] 页面标题简洁且包含关键词
- [ ] 移动端图标高清无锯齿
- [ ] 社交媒体分享卡片美观
- [ ] PWA 安装图标与品牌一致
- [ ] 品牌色在所有场景下统一

## 8. 维护建议

### 定期更新
- 每个大版本发布时更新 OG Image
- 监控品牌在不同平台的显示效果
- 收集用户反馈优化图标设计

### 性能优化
- SVG 图标优化至 < 2KB
- PNG 图标使用 TinyPNG 压缩
- 使用 WebP 格式（渐进式增强）
