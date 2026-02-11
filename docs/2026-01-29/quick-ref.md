# 快速参考 - 2026-01-29

## TL;DR
1. ✅ 实现了流式图片上传功能（SSE + 聊天面板显示进度）
2. ✅ 修复了 Claude 模型 API 调用的重大 bug

## 关键修复

### Bug: `'Anthropic' object has no attribute 'chat'`

**根因**: 使用了 OpenAI API 调用 Anthropic SDK 客户端

**修复位置**:
```python
# backend/app/services/ai_vision.py:782
self.client.messages.create(...)  # ✅ 正确

# backend/app/api/chat_generator.py:128
self.client.messages.stream(...)  # ✅ 流式调用
```

## 新增 API

### POST `/api/vision/analyze-flowchart-stream-v2`
流式图片识别，实时返回处理进度

**请求**:
```json
{
  "image_data": "data:image/png;base64,...",
  "provider": "custom",
  "api_key": "sk-...",
  "preserve_layout": true,
  "fast_mode": true
}
```

**响应**: SSE 流
```
data: {"type": "init", "message": "开始分析流程图..."}
data: {"type": "progress", "message": "🔍 正在分析图片结构..."}
data: {"type": "complete", "message": "✅ 识别完成！", "result": {...}}
```

## 端口配置
- 默认端口: 8003 (用户已统一配置)
- 配置文件: `backend/app/core/config.py`

## 重启服务器
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003
```

## 下次继续的点
- [ ] 添加单元测试
- [ ] 更新 API 文档
- [ ] 端口配置标准化确认
