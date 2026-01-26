# Brand Assets Generation Scripts

这个目录包含用于生成 Archboard 品牌资源的脚本。

## 📜 脚本列表

### 1. generate-icons.js
生成所有尺寸的应用图标

**功能:**
- 从 `app/icon.svg` 生成多尺寸 PNG
- 自动创建 maskable icon（带 padding）
- 生成浏览器和移动端所需的所有格式

**使用:**
```bash
npm run icons:generate
# 或
node scripts/generate-icons.js
```

**依赖:**
```bash
npm install sharp --save-dev
```

**生成的文件:**
- `app/apple-icon.png` (180x180)
- `public/icons/icon-192.png` (192x192)
- `public/icons/icon-512.png` (512x512)
- `public/icons/icon-maskable.png` (512x512, with padding)
- `public/icons/favicon-16.png` (16x16)
- `public/icons/favicon-32.png` (32x32)

### 2. generate-og-image.js
生成社交媒体分享图片

**功能:**
- 使用 Canvas API 绘制品牌图片
- 生成 Open Graph 图片 (1200x630)
- 生成 Twitter Card 图片 (1200x600)
- 包含品牌色、标题、装饰元素

**使用:**
```bash
npm run og:generate
# 或
node scripts/generate-og-image.js
```

**依赖:**
```bash
npm install canvas --save-dev
```

**生成的文件:**
- `public/og-image.png` (1200x630)
- `public/twitter-card.png` (1200x600)

## 🚀 快速开始

### 一键生成所有资源
```bash
# 1. 安装依赖
npm install sharp canvas --save-dev

# 2. 生成所有品牌资源
npm run brand:setup

# 3. 手动转换 favicon.ico（可选）
# 访问 https://realfavicongenerator.net/
# 上传 app/icon.svg，下载 favicon.ico
```

## 🛠️ 自定义配置

### 修改图标尺寸
编辑 `generate-icons.js`:
```javascript
const sizes = [
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-512.png', size: 512 },
  // 添加更多尺寸...
];
```

### 修改 OG 图片样式
编辑 `generate-og-image.js`:
```javascript
const colors = {
  background: '#0f172a',  // 背景色
  primary: '#4f46e5',     // 主品牌色
  secondary: '#10b981',   // 辅助色
  // 修改品牌色...
};
```

### 修改 OG 图片文案
编辑 `generate-og-image.js`:
```javascript
// Title
ctx.fillText('Archboard', canvas.width / 2, 240);

// Subtitle
ctx.fillText('AI-Powered Architecture Design Platform', canvas.width / 2, 310);
```

## 📋 依赖说明

### sharp
图像处理库，用于转换 SVG 到 PNG

**安装:**
```bash
npm install sharp --save-dev
```

**平台支持:** Windows, macOS, Linux

### canvas
Node.js Canvas API 实现，用于绘制 OG 图片

**安装:**
```bash
npm install canvas --save-dev
```

**注意:**
- Windows 用户可能需要额外的 Visual Studio 构建工具
- 如果安装失败，可以跳过 OG 图片生成（不影响核心功能）
- 或使用在线工具手动创建 OG 图片

## 🔍 验证生成结果

### 检查图标质量
```bash
# 查看生成的文件
ls -lh app/apple-icon.png
ls -lh public/icons/

# 在浏览器中预览
start app/apple-icon.png  # Windows
open app/apple-icon.png   # macOS
```

### 验证 OG 图片
```bash
# 查看文件大小（应该 < 500KB）
ls -lh public/og-image.png
ls -lh public/twitter-card.png

# 在浏览器中预览
start public/og-image.png  # Windows
open public/og-image.png   # macOS
```

### 在线验证
- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) - 测试 OG 图片
- [Twitter Card Validator](https://cards-dev.twitter.com/validator) - 测试 Twitter Card

## ⚠️ 常见问题

### Q: sharp 安装失败
**A:**
```bash
# 清除缓存重试
npm cache clean --force
npm install sharp --save-dev

# 或使用预编译二进制
npm install sharp --save-dev --ignore-scripts=false
```

### Q: canvas 安装失败 (Windows)
**A:**
```bash
# 安装 Windows 构建工具
npm install --global windows-build-tools

# 或跳过 canvas，手动创建 OG 图片
# 使用 Figma/Canva 等设计工具
```

### Q: 生成的图标模糊
**A:**
- 检查源 SVG 是否清晰
- 增加输出尺寸
- 使用 [SVGOMG](https://jakearchibald.github.io/svgomg/) 优化 SVG

### Q: OG 图片太大
**A:**
```bash
# 使用 TinyPNG 压缩
# 或添加压缩到脚本中
const sharp = require('sharp');
await sharp(inputPath)
  .png({ quality: 80, compressionLevel: 9 })
  .toFile(outputPath);
```

## 📚 相关文档

- `../docs/brand-design-guide.md` - 品牌设计指南
- `../docs/favicon-implementation-guide.md` - 实施指南
- `../docs/brand-design-summary.md` - 设计总结

## 🔄 更新日志

- **2026-01-21**: 初始版本
  - 添加 icon 生成脚本
  - 添加 OG 图片生成脚本
  - 集成到 npm scripts

## 🤝 贡献

如果你改进了脚本或发现了 bug，欢迎提交 PR！

改进建议：
- [ ] 添加 WebP 格式支持
- [ ] 自动优化图片大小
- [ ] 支持自定义模板
- [ ] 添加批量处理模式
- [ ] 集成 CI/CD 自动生成
