# 模型与 API Key 管理系统重构方案

**日期：** 2026-01-20
**状态：** 技术方案待讨论
**优先级：** 🔴 高（严重影响用户体验）

---

## 核心问题

### 当前实现的痛点

**现状分析：**

1. **单一配置模式** - 每次只能设置一个提供商的 API Key
```python
# backend/app/api/models.py
@router.post("/models/config")
async def set_model_config(config: ModelConfig):
    # 只能存储一个提供商的配置
    settings.set_model_config(config.provider, config.api_key, config.model_name)
```

2. **频繁替换体验差**
```
用户想用 Gemini 生成架构图 → 输入 Gemini API Key
用户想用 OpenAI 分析截图 → 删除 Gemini Key，输入 OpenAI Key
用户想回到 Gemini → 又要重新输入 Gemini Key
```

3. **无法对比不同模型效果**
- 想测试 GPT-4 vs Claude vs Gemini 的生成质量
- 需要反复切换配置，效率极低

4. **缺少预设管理**
- 无法保存多个配置（如"个人 Key" vs "公司 Key"）
- 无法给配置命名
- 无法设置默认模型

---

## 用户需求场景

### 场景1：多提供商并行使用

**用户：** 个人开发者
**需求：**
- Gemini API Key（免费额度）→ 用于日常架构图生成
- OpenAI API Key（付费）→ 用于重要项目的高质量分析
- Claude API Key（测试）→ 对比不同模型效果

**期望交互：**
```
[下拉选择框]
  ✓ Gemini Flash (我的免费额度) ← 默认
  ○ GPT-4 Vision (公司付费账号)
  ○ Claude Sonnet (测试账号)

[生成架构图] 按钮 → 使用选中的模型
```

---

### 场景2：同一提供商的多个账号

**用户：** 团队协作
**需求：**
- 个人 Gemini Key（每日配额有限）
- 团队 Gemini Key（共享额度）
- 测试环境 Gemini Key（独立计费）

**期望交互：**
```
提供商: Gemini
配置列表:
  • Gemini - 个人账号 (gemini-2.0-flash)
  • Gemini - 团队共享 (gemini-1.5-pro)
  • Gemini - 测试环境 (gemini-2.0-flash)

快速切换，无需重新输入 API Key
```

---

### 场景3：不同功能使用不同模型

**用户：** 成本优化
**需求：**
- 截图识别 → 使用便宜的 Qwen2.5-VL（SiliconFlow）
- 架构优化 → 使用强大的 GPT-4
- 文档生成 → 使用平衡的 Gemini Flash

**期望交互：**
```
功能模块内嵌模型选择:
┌────────────────────────────┐
│ 截图识别                   │
│ 模型: [Qwen2.5-VL ▼]       │
│ [上传图片]                 │
└────────────────────────────┘

┌────────────────────────────┐
│ 架构优化                   │
│ 模型: [GPT-4 Vision ▼]     │
│ [开始分析]                 │
└────────────────────────────┘
```

---

## 技术方案设计

### 方案A：多配置管理系统（推荐 ⭐⭐⭐⭐⭐）

**核心设计：**
1. 支持同时保存多个提供商的多个配置
2. 每个配置有唯一 ID、名称、默认标记
3. 前端下拉选择，无需频繁输入 API Key
4. 配置持久化到文件（JSON）或数据库

**数据模型：**

```python
# backend/app/models/schemas.py

class ModelPreset(BaseModel):
    """模型预设配置"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # 用户自定义名称，如 "我的 Gemini"
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"]
    api_key: str
    model_name: str  # 如 "gemini-2.0-flash", "gpt-4-vision-preview"
    base_url: Optional[str] = None  # 自定义端点
    is_default: bool = False  # 是否为默认配置
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None

class ModelPresetsConfig(BaseModel):
    """全局预设配置管理"""
    presets: List[ModelPreset] = []

    def add_preset(self, preset: ModelPreset):
        # 如果设置为默认，取消其他同提供商的默认标记
        if preset.is_default:
            for p in self.presets:
                if p.provider == preset.provider:
                    p.is_default = False
        self.presets.append(preset)

    def get_default_for_provider(self, provider: str) -> Optional[ModelPreset]:
        for preset in self.presets:
            if preset.provider == provider and preset.is_default:
                return preset
        # 如果没有默认，返回第一个该提供商的配置
        for preset in self.presets:
            if preset.provider == provider:
                return preset
        return None

    def delete_preset(self, preset_id: str):
        self.presets = [p for p in self.presets if p.id != preset_id]

    def update_preset(self, preset_id: str, updates: dict):
        for preset in self.presets:
            if preset.id == preset_id:
                for key, value in updates.items():
                    setattr(preset, key, value)
                break
```

**持久化方案（文件存储）：**

```python
# backend/app/services/model_config_service.py
import json
from pathlib import Path

CONFIG_FILE = Path("model_presets.json")

class ModelConfigService:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> ModelPresetsConfig:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ModelPresetsConfig(**data)
        return ModelPresetsConfig()

    def _save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config.dict(), f, ensure_ascii=False, indent=2)

    def add_preset(self, preset: ModelPreset) -> ModelPreset:
        self.config.add_preset(preset)
        self._save_config()
        return preset

    def get_all_presets(self) -> List[ModelPreset]:
        return self.config.presets

    def get_preset_by_id(self, preset_id: str) -> Optional[ModelPreset]:
        for preset in self.config.presets:
            if preset.id == preset_id:
                return preset
        return None

    def delete_preset(self, preset_id: str):
        self.config.delete_preset(preset_id)
        self._save_config()

    def update_preset(self, preset_id: str, updates: dict):
        self.config.update_preset(preset_id, updates)
        self._save_config()

    def mark_as_used(self, preset_id: str):
        """记录最后使用时间"""
        self.update_preset(preset_id, {
            "last_used": datetime.now().isoformat()
        })

# 全局单例
_model_config_service = None

def get_model_config_service() -> ModelConfigService:
    global _model_config_service
    if _model_config_service is None:
        _model_config_service = ModelConfigService()
    return _model_config_service
```

**新增 API 端点：**

```python
# backend/app/api/models.py
from app.services.model_config_service import get_model_config_service

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/presets", response_model=List[ModelPreset])
async def get_all_presets():
    """获取所有模型预设配置"""
    service = get_model_config_service()
    return service.get_all_presets()

@router.post("/presets", response_model=ModelPreset, status_code=201)
async def create_preset(preset: ModelPreset):
    """创建新的模型预设"""
    service = get_model_config_service()
    return service.add_preset(preset)

@router.get("/presets/{preset_id}", response_model=ModelPreset)
async def get_preset(preset_id: str):
    """获取单个预设配置"""
    service = get_model_config_service()
    preset = service.get_preset_by_id(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset

@router.put("/presets/{preset_id}", response_model=ModelPreset)
async def update_preset(preset_id: str, updates: dict):
    """更新预设配置"""
    service = get_model_config_service()
    service.update_preset(preset_id, updates)
    preset = service.get_preset_by_id(preset_id)
    return preset

@router.delete("/presets/{preset_id}", status_code=204)
async def delete_preset(preset_id: str):
    """删除预设配置"""
    service = get_model_config_service()
    service.delete_preset(preset_id)

@router.post("/presets/{preset_id}/use")
async def mark_preset_used(preset_id: str):
    """标记预设为已使用（更新 last_used）"""
    service = get_model_config_service()
    service.mark_as_used(preset_id)
    return {"message": "Preset marked as used"}
```

**修改现有 AI 功能 API（以截图识别为例）：**

```python
# backend/app/api/vision.py

@router.post("/vision/analyze", response_model=ImageAnalysisResponse)
async def analyze_architecture(
    file: UploadFile = File(...),
    preset_id: Optional[str] = Query(None),  # 新增：预设 ID
    provider: Optional[str] = Query(None),   # 兼容旧版
    api_key: Optional[str] = Query(None)     # 兼容旧版
):
    """
    分析架构图截图
    优先使用 preset_id，如果未提供则使用 provider + api_key
    """
    service = get_model_config_service()

    # 方式1：使用预设配置（推荐）
    if preset_id:
        preset = service.get_preset_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset not found")

        provider = preset.provider
        api_key = preset.api_key
        model_name = preset.model_name
        base_url = preset.base_url

        # 标记为已使用
        service.mark_as_used(preset_id)

    # 方式2：临时配置（兼容旧版 API）
    else:
        if not provider or not api_key:
            raise HTTPException(
                status_code=400,
                detail="Either preset_id or (provider + api_key) required"
            )
        model_name = None  # 使用默认模型
        base_url = None

    # 调用 AI Vision 服务
    vision_service = AIVisionService(
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        base_url=base_url
    )

    result = await vision_service.analyze_architecture(file)
    return result
```

---

**前端管理界面：**

```typescript
// frontend/components/ModelPresetsManager.tsx
import { useState, useEffect } from 'react';

interface ModelPreset {
  id: string;
  name: string;
  provider: string;
  model_name: string;
  is_default: boolean;
  last_used: string | null;
}

export function ModelPresetsManager() {
  const [presets, setPresets] = useState<ModelPreset[]>([]);
  const [isAdding, setIsAdding] = useState(false);

  // 表单状态
  const [newPresetName, setNewPresetName] = useState('');
  const [newProvider, setNewProvider] = useState('gemini');
  const [newApiKey, setNewApiKey] = useState('');
  const [newModelName, setNewModelName] = useState('gemini-2.0-flash');
  const [isDefault, setIsDefault] = useState(false);

  useEffect(() => {
    fetchPresets();
  }, []);

  const fetchPresets = async () => {
    const response = await fetch('http://localhost:8000/api/models/presets');
    const data = await response.json();
    setPresets(data);
  };

  const handleAddPreset = async () => {
    const response = await fetch('http://localhost:8000/api/models/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newPresetName,
        provider: newProvider,
        api_key: newApiKey,
        model_name: newModelName,
        is_default: isDefault
      })
    });

    if (response.ok) {
      fetchPresets();
      setIsAdding(false);
      // 重置表单
      setNewPresetName('');
      setNewApiKey('');
    }
  };

  const handleDeletePreset = async (id: string) => {
    if (!confirm('确定删除此配置？')) return;

    await fetch(`http://localhost:8000/api/models/presets/${id}`, {
      method: 'DELETE'
    });
    fetchPresets();
  };

  const handleSetDefault = async (id: string) => {
    await fetch(`http://localhost:8000/api/models/presets/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_default: true })
    });
    fetchPresets();
  };

  return (
    <div className="model-presets-manager">
      <h3>模型配置管理</h3>

      {/* 预设列表 */}
      <div className="presets-list">
        {presets.map(preset => (
          <div key={preset.id} className="preset-card">
            <div className="preset-header">
              <h4>{preset.name}</h4>
              {preset.is_default && <span className="badge">默认</span>}
            </div>

            <div className="preset-details">
              <p>提供商: {preset.provider}</p>
              <p>模型: {preset.model_name}</p>
              <p>API Key: {preset.api_key.substring(0, 8)}***</p>
              {preset.last_used && (
                <p className="text-sm text-gray-500">
                  最后使用: {new Date(preset.last_used).toLocaleString()}
                </p>
              )}
            </div>

            <div className="preset-actions">
              {!preset.is_default && (
                <button onClick={() => handleSetDefault(preset.id)}>
                  设为默认
                </button>
              )}
              <button onClick={() => handleDeletePreset(preset.id)}>
                删除
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 添加按钮 */}
      <button onClick={() => setIsAdding(true)}>+ 添加新配置</button>

      {/* 添加对话框 */}
      {isAdding && (
        <div className="modal">
          <h4>添加模型配置</h4>

          <input
            placeholder="配置名称（如：我的 Gemini）"
            value={newPresetName}
            onChange={e => setNewPresetName(e.target.value)}
          />

          <select value={newProvider} onChange={e => setNewProvider(e.target.value)}>
            <option value="gemini">Gemini</option>
            <option value="openai">OpenAI</option>
            <option value="claude">Claude</option>
            <option value="siliconflow">SiliconFlow</option>
            <option value="custom">自定义</option>
          </select>

          <input
            placeholder="API Key"
            type="password"
            value={newApiKey}
            onChange={e => setNewApiKey(e.target.value)}
          />

          <input
            placeholder="模型名称（如：gemini-2.0-flash）"
            value={newModelName}
            onChange={e => setNewModelName(e.target.value)}
          />

          <label>
            <input
              type="checkbox"
              checked={isDefault}
              onChange={e => setIsDefault(e.target.checked)}
            />
            设为默认配置
          </label>

          <div className="actions">
            <button onClick={handleAddPreset}>保存</button>
            <button onClick={() => setIsAdding(false)}>取消</button>
          </div>
        </div>
      )}
    </div>
  );
}
```

**前端模型选择组件（通用）：**

```typescript
// frontend/components/ModelPresetSelector.tsx
import { useState, useEffect } from 'react';

interface ModelPresetSelectorProps {
  onSelect: (presetId: string) => void;
  filterProvider?: string;  // 可选：只显示特定提供商
  defaultPresetId?: string;
}

export function ModelPresetSelector({
  onSelect,
  filterProvider,
  defaultPresetId
}: ModelPresetSelectorProps) {
  const [presets, setPresets] = useState([]);
  const [selectedId, setSelectedId] = useState(defaultPresetId || '');

  useEffect(() => {
    fetchPresets();
  }, []);

  const fetchPresets = async () => {
    const response = await fetch('http://localhost:8000/api/models/presets');
    let data = await response.json();

    // 过滤提供商
    if (filterProvider) {
      data = data.filter(p => p.provider === filterProvider);
    }

    setPresets(data);

    // 自动选择默认配置
    const defaultPreset = data.find(p => p.is_default);
    if (defaultPreset && !selectedId) {
      setSelectedId(defaultPreset.id);
      onSelect(defaultPreset.id);
    }
  };

  const handleChange = (presetId: string) => {
    setSelectedId(presetId);
    onSelect(presetId);
  };

  return (
    <select
      value={selectedId}
      onChange={e => handleChange(e.target.value)}
      className="model-preset-selector"
    >
      <option value="">选择模型配置...</option>
      {presets.map(preset => (
        <option key={preset.id} value={preset.id}>
          {preset.name} ({preset.model_name})
          {preset.is_default && ' - 默认'}
        </option>
      ))}
    </select>
  );
}
```

**集成到功能模块（以截图识别为例）：**

```typescript
// frontend/components/FlowchartUploader.tsx
import { ModelPresetSelector } from './ModelPresetSelector';

export function FlowchartUploader() {
  const [selectedPresetId, setSelectedPresetId] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file);

    // 使用选中的预设配置
    const response = await fetch(
      `http://localhost:8000/api/vision/analyze-flowchart?preset_id=${selectedPresetId}`,
      {
        method: 'POST',
        body: formData
      }
    );

    const result = await response.json();
    // 处理结果...
  };

  return (
    <div>
      <h3>上传流程图截图</h3>

      {/* 模型选择 */}
      <div className="model-selection">
        <label>选择模型:</label>
        <ModelPresetSelector onSelect={setSelectedPresetId} />
      </div>

      {/* 文件上传 */}
      <input type="file" onChange={e => setFile(e.target.files[0])} />

      <button onClick={handleUpload} disabled={!selectedPresetId || !file}>
        开始识别
      </button>
    </div>
  );
}
```

---

### 方案B：LocalStorage 存储（轻量级方案）

**适用场景：** 不想修改后端，纯前端实现

**实现方式：**
```typescript
// frontend/lib/modelPresets.ts
interface ModelPreset {
  id: string;
  name: string;
  provider: string;
  apiKey: string;
  modelName: string;
  isDefault: boolean;
}

export function savePreset(preset: ModelPreset) {
  const presets = getPresets();
  presets.push(preset);
  localStorage.setItem('model_presets', JSON.stringify(presets));
}

export function getPresets(): ModelPreset[] {
  const stored = localStorage.setItem('model_presets');
  return stored ? JSON.parse(stored) : [];
}
```

**优点：**
- ✅ 实现简单，无需后端改动

**缺点：**
- ❌ 安全性差（API Key 明文存储在浏览器）
- ❌ 无法跨设备同步
- ❌ 清空浏览器数据后丢失

---

## 推荐方案

### 方案 A（后端持久化）⭐⭐⭐⭐⭐

**理由：**
1. ✅ **安全性** - API Key 存储在服务器，不暴露给浏览器 DevTools
2. ✅ **跨设备** - 未来引入用户系统后可跨设备同步
3. ✅ **功能完整** - 支持最后使用时间、使用统计等高级功能
4. ✅ **符合架构** - 后端已有配置管理模块，易于扩展

**实现优先级：**
- Week 1: 核心功能（预设管理、前端选择器）
- Week 2: 集成到所有 AI 功能（截图识别、架构生成、Excalidraw 生成）
- Week 3: 高级功能（使用统计、配置导入导出）

---

## 实现清单

### Phase 6.3: 模型配置管理系统（2-3天）

**Day 1: 后端核心**
- [ ] 创建数据模型（`ModelPreset`, `ModelPresetsConfig`）
- [ ] 实现 `ModelConfigService`（文件存储）
- [ ] 新增 API 端点（CRUD + mark_used）
- [ ] 测试 API（Postman/pytest）

**Day 2: 前端管理界面**
- [ ] 创建 `ModelPresetsManager.tsx` - 配置管理页面
- [ ] 创建 `ModelPresetSelector.tsx` - 通用选择器组件
- [ ] 集成到侧边栏/设置页面
- [ ] 测试添加/删除/设为默认流程

**Day 3: 集成到现有功能**
- [ ] 修改 `/api/vision/analyze` - 支持 `preset_id` 参数
- [ ] 修改 `/api/vision/analyze-flowchart` - 支持预设
- [ ] 修改 `/api/excalidraw/generate` - 支持预设
- [ ] 修改 `/api/chat-generator/*` - 支持预设
- [ ] 前端所有 AI 功能组件集成模型选择器
- [ ] 测试完整流程

---

## 兼容性策略

为了不破坏现有 API，采用渐进式迁移：

**阶段1：双模式支持**
```python
# 同时支持旧版（provider + api_key）和新版（preset_id）
@router.post("/vision/analyze")
async def analyze(
    preset_id: Optional[str] = None,  # 新增
    provider: Optional[str] = None,   # 保留
    api_key: Optional[str] = None     # 保留
):
    if preset_id:
        # 使用预设
    elif provider and api_key:
        # 使用临时配置（兼容旧版）
    else:
        raise HTTPException(400, "Either preset_id or provider+api_key required")
```

**阶段2：弃用警告（Phase 7）**
```python
elif provider and api_key:
    warnings.warn("provider+api_key is deprecated, use preset_id", DeprecationWarning)
    # 仍然可用
```

**阶段3：移除旧参数（Phase 8）**
```python
# 只保留 preset_id
```

---

## 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| API Key 文件泄露 | 低 | 高 | 添加到 .gitignore，权限控制（600） |
| 配置文件损坏 | 低 | 中 | 自动备份，JSON 校验 |
| 现有功能回归 | 中 | 高 | 保持向后兼容，渐进式迁移 |
| 用户不理解预设概念 | 中 | 低 | 提供引导教程和示例配置 |

---

## 未来扩展

### Phase 7+（可选）

1. **使用统计仪表盘**
   - 每个预设的调用次数、成功率
   - 成本估算（基于 Token 数）

2. **配置导入/导出**
   - JSON 格式导出（API Key 脱敏）
   - 团队配置分享

3. **智能推荐**
   - 根据任务类型推荐最佳模型
   - 成本优先 vs 质量优先模式

4. **配额管理**
   - 每个预设设置调用限额
   - 超限自动切换备用配置

---

## 参考文档

- `backend/app/api/models.py` - 现有模型配置 API
- `backend/app/core/config.py` - 全局配置管理
- `doc/2026-01-20/RAG_AND_PROMPT_DESIGN.md` - Prompt 管理系统（类似架构）

---

**文档状态：** 待用户确认方案
**下一步：** 确认是否采用方案 A（后端持久化）并开始实现
