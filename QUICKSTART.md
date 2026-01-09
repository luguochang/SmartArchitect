# 快速启动指南

> 环境切换后快速恢复工作的步骤清单

## 🚀 快速启动

### 1. 启动后端（必须）
```bash
# Windows
cd backend
venv\Scripts\activate
python -m app.main

# 验证：浏览器访问 http://localhost:8002/docs
```

### 2. 启动前端（必须）
```bash
# 新终端窗口
cd frontend
npm run dev

# 验证：浏览器访问 http://localhost:3000
```

### 3. 验证 BPMN 节点（刚完成的功能）
1. 打开 http://localhost:3000
2. 点击左侧 Sidebar "BPMN 节点" 分类
3. 依次添加 5 种节点：
   - ✅ Start（绿色，细边框圆形）
   - ✅ End（红色，粗边框圆形）
   - ✅ Task（蓝色，大圆角矩形）
   - ✅ Gateway（橙色，菱形+X）
   - ✅ Event（黄色，双层圆形）
4. 检查：
   - 形状正确
   - 颜色与 Sidebar 一致
   - 可连接、拖拽、编辑

---

## 📝 当前工作状态

**上次工作**：实现 BPMN 2.0 标准节点形状
**已完成**：
- ✅ Sidebar 重构（搜索+分类）
- ✅ 5 种 BPMN 标准形状
- ✅ 图标和颜色映射系统

**待测试**：
- [ ] BPMN 节点渲染
- [ ] 主题切换
- [ ] Mock 数据生成

**下一步**：
1. 更新 `backend/app/services/chat_generator.py` 的 Mock 数据
2. 重构 4 个架构节点（Cache, Queue, Storage, Client）
3. 扩展主题系统

---

## 🔍 关键文件位置

### 刚修改的文件
```
frontend/
  components/
    Sidebar.tsx                    # 重构：宽度、搜索、分类
    nodes/
      DefaultNode.tsx              # 新增：5 种 BPMN 形状
      GatewayNode.tsx              # 优化：80px + X 符号
  lib/
    utils/
      nodeShapes.ts                # 新建：形状配置

backend/
  app/
    models/schemas.py              # 扩展：shape 类型
    services/chat_generator.py     # 待更新：Mock 数据
```

### 配置文件
```
frontend/next.config.js            # API 代理：8002
backend/app/core/config.py         # 后端配置
```

---

## 🐛 常见问题

### 后端无法启动
**问题**：端口 8002 被占用
```bash
# 查找进程
netstat -ano | findstr :8002
# 杀死进程（Windows）
taskkill //F //PID <PID>
```

### 前端无法访问 API
**检查**：
1. 后端是否在 8002 端口运行
2. `next.config.js` 代理配置是否正确
3. 浏览器控制台 Network 标签查看请求

### BPMN 节点显示异常
**可能原因**：
1. 前端代码未编译（重启 `npm run dev`）
2. 缓存问题（Ctrl+Shift+R 强制刷新）
3. 后端 schema 未更新（重启后端）

---

## 📦 依赖安装（如果是全新环境）

### 后端
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r test-requirements.txt
```

### 前端
```bash
cd frontend
npm install
```

---

## 📊 查看详细进度
- **完整进度**：`PROGRESS.md`
- **项目指南**：`CLAUDE.md`
- **测试报告**：`TEST_COVERAGE_REPORT.md`
- **系统评估**：`SYSTEM_REVIEW.md`

---

**最后更新**：2026-01-08 17:30
**下次继续点**：测试 BPMN 节点 → 更新 Mock 数据

## ���¼�¼��2026-01-xx��
- BPMN �ڵ���ʽ���£��¼�/���������ͼ����У�ȱʡ iconType �ɻ��˵� iconLabel/����ĸ��
- AI Actions (Prompter) �� API Key ʱִ���߱��� mock�����������ˡ�
- Chat Generator mock ʹ�� BPMN ��״��start-event/end-event/task������ iconType/color��
- ����/����ʽ��glow edges����ͷ���������
