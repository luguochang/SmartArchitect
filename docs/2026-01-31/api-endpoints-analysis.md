# 需要 ikuncode 兼容的所有 API 端点分析

## API 端点清单

### 1. Flow Canvas (React Flow)

#### 1.1 聊天框生成 - 流式 ✅ 已修改
- **端点**: `POST /api/chat-generator/generate-stream`
- **文件**: `backend/app/api/chat_generator.py:79`
- **功能**: 根据用户文本描述生成流程图（流式）
- **状态**: ✅ 已兼容 ikuncode
- **使用场景**: 用户在聊天框输入文字生成流程图

#### 1.2 聊天框生成 - 非流式
- **端点**: `POST /api/chat-generator/generate`
- **文件**: `backend/app/api/chat_generator.py:38`
- **功能**: 根据用户文本描述生成流程图（非流式）
- **状态**: ❓ 需要检查
- **使用场景**: 降级方案或特殊情况

#### 1.3 图片上传分析 ❌ 未修改
- **端点**: `POST /api/vision/analyze`
- **文件**: `backend/app/api/vision.py`
- **功能**: 上传图片，AI 分析后生成流程图
- **状态**: ❌ 未兼容 ikuncode
- **使用场景**: 用户上传架构图/流程图图片

### 2. Excalidraw Canvas

#### 2.1 聊天框生成 - 流式 ❌ 未修改
- **端点**: `POST /api/excalidraw/generate-stream`
- **文件**: `backend/app/api/excalidraw.py:75`
- **功能**: 根据用户文本描述生成 Excalidraw 场景（流式）
- **状态**: ❌ 未兼容 ikuncode
- **使用场景**: 用户在聊天框输入文字生成手绘图
- **特殊性**: 支持画板流式打印（增量渲染元素）

#### 2.2 聊天框生成 - 非流式
- **端点**: `POST /api/excalidraw/generate`
- **文件**: `backend/app/api/excalidraw.py:14`
- **功能**: 根据用户文本描述生成 Excalidraw 场景（非流式）
- **状态**: ❓ 需要检查
- **使用场景**: 降级方案

#### 2.3 图片上传分析 ❌ 未修改
- **端点**: 可能复用 `/api/vision/analyze` 或有独立端点
- **功能**: 上传图片，AI 分析后生成 Excalidraw 场景
- **状态**: ❌ 未兼容 ikuncode
- **使用场景**: 用户上传手绘图/原型图

### 3. 其他端点

#### 3.1 诊断测试
- **端点**: `POST /api/diagnosis/test-ai`
- **文件**: `backend/app/api/diagnosis.py:24`
- **功能**: 测试 AI 连接
- **状态**: ❓ 需要检查（可能不重要）

---

## 详细分析

### Flow Canvas - 图片上传 (`/api/vision/analyze`)

让我检查这个端点的实现...
