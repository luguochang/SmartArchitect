<div align="center">

# ArchBoard

**把脑子里的想法，变成清晰的流程图**

AI 驱动的思维可视化工具 · 让复杂的想法一目了然

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.5.0-green.svg)](https://github.com/luguochang/SmartArchitect/releases)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

[English](./README_EN.md) | 简体中文

[快速体验](#-快速开始) · [核心理念](#-核心理念) · [应用场景](#-应用场景) · [功能演示](#-功能演示)

</div>

---

## 💡 ArchBoard 是什么？

你有没有遇到过这些情况：

- 💭 **脑子里有个想法，但说不清楚**
- 🌀 **业务流程太复杂，理不清头绪**
- 🤯 **技术方案讨论时，大家理解不一致**
- 📝 **开会记了一堆笔记，但事后看不懂**

**ArchBoard 就是来解决这个问题的。**

> 用自然语言描述你的想法 → AI 自动生成流程图 → 边看边调整 → 思路越来越清晰

不是画图工具，而是**思维整理助手**。

---

## 🎯 核心理念

### 从混乱到清晰的三步法

```
步骤 1: 倾倒想法          步骤 2: AI 可视化         步骤 3: 迭代优化

"我想做个用户注册      →    [生成流程图]      →    "加上短信验证"
 登录、密码重置..."            ┌─────────┐              [自动调整]
                              │ 注册流程 │                ↓
 说不清的模糊想法              │ 登录逻辑 │           清晰的执行方案
                              └─────────┘
```

### 核心价值

不是"画得好不好看"，而是**"想得清不清楚"**。

- ✅ **快速具象化** - 3 分钟把想法变成图，不用纠结怎么画
- ✅ **暴露盲区** - 看到流程图后发现：这里没考虑到，那里有问题
- ✅ **统一认知** - 团队讨论时，大家看着同一张图，理解一致
- ✅ **持续优化** - 对话式调整，想法越来越完善

---

## 🎬 应用场景

### 1. 产品经理：理清业务流程

**场景**：新需求来了，脑子里有个大概思路，但细节还没想清楚

**传统做法**：
- 打开 Axure/墨刀，纠结用什么形状
- 画了半天，发现流程不对，重新画
- 花 2 小时画图，核心业务逻辑还没想清楚

**用 ArchBoard**：

```
你: "设计一个电商秒杀流程，用户点击秒杀按钮..."

AI: [3秒生成基础流程]
    用户点击 → 检查库存 → 扣减库存 → 创建订单 → 跳转支付

你: "等等，库存扣减要加锁，防止超卖"

AI: [立即调整]
    检查库存 → Redis分布式锁 → 扣减库存 → 创建订单

你: "支付失败要恢复库存"

AI: [补充异常流程]
    支付失败 → 释放锁 → 恢复库存 → 返回失败
```

**结果**：10 分钟，流程图 + 边界情况都想清楚了。

---

### 2. 技术人员：设计技术方案

**场景**：要设计一个新系统，技术选型、架构设计还没定

**传统做法**：
- 写 Word 文档，用文字描述，干巴巴的
- 开评审会，大家各说各的，没有统一的视图
- 评审完了，还是不清楚怎么做

**用 ArchBoard**：

```
你: "设计一个短视频推荐系统，包含数据采集、特征提取、召回、排序"

AI: [生成初版架构]
    [数据采集] → [特征工程] → [召回服务] → [排序服务] → [用户端]

你: "召回服务拆成 3 个：热度召回、协同过滤、内容召回"

AI: [调整架构]
                    ┌─ 热度召回 ─┐
    特征工程 → ├─ 协同过滤 ─┤ → 排序融合 → 用户端
                    └─ 内容召回 ─┘

你: "加上实时数据流，用 Kafka + Flink"

AI: [补充实时链路]
    用户行为 → Kafka → Flink实时计算 → Redis → 召回服务
```

**结果**：方案清晰可见，评审时直接对着图讨论，效率提升 5 倍。

---

### 3. 创业者：梳理商业模式

**场景**：有个创业想法，但商业闭环还没想清楚

**传统做法**：
- 写 BP，文字描述，投资人看不懂
- 讲半天，别人还是理解不了
- 自己都说不清楚盈利模式

**用 ArchBoard**：

```
你: "做一个线上教育平台，老师入驻，学生付费学习"

AI: [生成基础流程]
    老师入驻 → 上传课程 → 学生购买 → 平台抽成

你: "老师怎么获得学生？要有推广机制"

AI: [补充推广流程]
    老师推广 → 学生注册（带推荐码）→ 购买课程 → 老师获得分成

你: "学生怎么知道课程质量好？要有评价和试听"

AI: [补充质量保证]
    课程详情 → 试听片段 → 学生评价 → 购买决策
```

**结果**：商业闭环清晰可见，哪里还有问题一目了然。

---

### 4. 运营人员：设计活动流程

**场景**：策划一个营销活动，流程步骤需要和技术、产品对齐

```
你: "双十一活动，用户领券、满减、凑单、支付"

AI: [生成活动流程]
    进入活动页 → 领取优惠券 → 添加商品 → 凑单满减 → 结算支付

你: "要考虑库存不足的情况"

AI: [补充异常]
    添加商品 → 检查库存 → 库存不足 → 推荐替代品

你: "支付失败后优惠券要退回"

AI: [完善退款逻辑]
    支付失败 → 退回优惠券 → 保留购物车 → 用户重试
```

**结果**：活动流程、异常处理、技术要求，都对齐了。

---

### 5. 学生/教师：理解算法逻辑

**场景**：学习复杂算法，代码看不懂，需要可视化理解

```
你: "快速排序算法的执行流程"

AI: [生成算法流程]
    选择基准值 → 分区（小于/大于）→ 递归左右子数组 → 合并

你: "详细展示分区的过程"

AI: [展开细节]
    遍历数组 → 比较元素 → 小于基准移左 → 大于基准移右 → 交换位置
```

**结果**：算法逻辑一目了然，不用死记硬背。

---

## ✨ 核心特性

### 1. 对话式生成 - 像聊天一样画图

不用学复杂的工具，**说出你的想法，AI 帮你画**。

```
你: "画一个用户注册流程"
AI: [生成基础版]

你: "加上手机验证码"
AI: [自动加上验证步骤]

你: "如果验证码输错 3 次，锁定账号 30 分钟"
AI: [补充异常处理]
```

**支持的 AI 模型：**
- Google Gemini（推荐，免费额度大）
- OpenAI GPT-4（理解最准确）
- Claude 3.5（逻辑最清晰）
- SiliconFlow（国内访问快）
- 自定义模型（接入你自己的）

### 2. 双画布系统 - 规范图 + 自由画

**Flow Canvas**：结构化流程图，适合正式场合
- 节点规范（API、Service、Database...）
- 连线清晰
- 自动布局
- 适合：技术方案、业务流程、系统设计

**Excalidraw**：手绘风白板，适合头脑风暴
- 自由涂鸦
- 手绘美学
- 无限画布
- 适合：初期构思、Workshop、快速草图

#### 为什么选择节点式画布？

与传统绘图工具不同，**ArchBoard 的 Flow Canvas 基于节点式架构（React Flow）**，带来革命性的交互体验：

**🔗 真正的节点互联**
- 传统工具：拖一个方框 + 拖一条线，它们只是"画"在一起，没有关联
- **ArchBoard**：拖拽节点时，连线自动跟随；删除节点时，相关连线自动清理
- **结果**：流程图始终保持一致性，不会出现"孤立的线"或"断开的连接"

**⚡ 实时响应式更新**
- 传统工具：修改节点位置后，需要手动调整每条线的起点和终点
- **ArchBoard**：基于 React 虚拟 DOM，节点移动时连线自动重绘，性能丝滑
- **结果**：随意调整布局，无需担心"图乱了"

**🎯 程序化控制能力**
- 传统工具：每个元素都是独立的"画出来的形状"
- **ArchBoard**：节点和连线是可编程的数据结构，支持批量操作、导出导入、版本控制
- **结果**：流程图可以像代码一样管理，支持 Git 版本控制、自动化生成

**🚀 性能优化**
- 传统工具：画布上元素多了就卡顿（全量渲染）
- **ArchBoard**：内置虚拟化技术，只渲染可视区域内的节点
- **结果**：即使 100+ 节点的复杂流程图，依然流畅交互

**简单来说**：
> 传统工具是"画图" → 你画什么就是什么
> **ArchBoard 是"建模"** → 节点和关系是活的，会自动维护一致性

这就是为什么 ArchBoard 更适合"思维整理"而不仅仅是"画图"。

### 3. 图片识别 - 白板照片变流程图

开完会，白板上画了一堆，拍照上传，AI 自动识别并生成可编辑的流程图。

再也不用担心白板擦掉后找不到了。

### 4. 多主题系统 - 适配各种场景

12+ 精心调教的配色方案：
- **汇报演示**：Geist、Default（专业简洁）
- **技术分享**：Dracula、Monokai（深色护眼）
- **长时间编辑**：Nord、Solarized（柔和配色）
- **文档截图**：GitHub、Material（高对比度）

---

## 🎬 功能演示

### AI 对话生成

![AI 生成演示](./docs/assets/demo-ai-generation.gif)

*描述想法 → AI 生成 → 持续优化*

### Flow Canvas 编辑

![Flow Canvas 演示](./docs/assets/demo-flow-canvas.gif)

*拖拽、连线、自动布局*

### Excalidraw 白板

![Excalidraw 演示](./docs/assets/demo-excalidraw.gif)

*手绘风格、自由创作*

<details>
<summary>📊 查看更多实际案例</summary>

<table>
<tr>
<td width="50%" align="center">
<img src="./docs/assets/example-1.png" width="100%">
<p><b>电商业务流程</b></p>
</td>
<td width="50%" align="center">
<img src="./docs/assets/example-2.png" width="100%">
<p><b>技术架构设计</b></p>
</td>
</tr>
<tr>
<td width="50%" align="center">
<img src="./docs/assets/example-3.png" width="100%">
<p><b>故障排查流程</b></p>
</td>
<td width="50%" align="center">
<img src="./docs/assets/example-4.png" width="100%">
<p><b>算法可视化</b></p>
</td>
</tr>
</table>

</details>

---

## 🚀 快速开始

### 5 分钟本地运行

```bash
# 1. 克隆项目
git clone https://github.com/luguochang/SmartArchitect.git
cd SmartArchitect

# 2. 启动（一键脚本）
# Windows:
start-dev.bat

# Linux/Mac:
./start-dev.sh

# 3. 访问
打开浏览器访问 http://localhost:3000
```

### 配置 AI（可选）

```bash
# backend 目录创建 .env 文件
cd backend
echo "GEMINI_API_KEY=你的Key" > .env
```

**不配置也能用**：可以在界面上动态输入 API Key。

---

## 💡 使用技巧

### 如何写好提示词？

**✅ 好的提示词**（描述清晰、分步骤）

```
设计一个外卖订单流程：

1. 用户端：
   - 浏览餐厅和菜品
   - 加入购物车
   - 提交订单（选择地址、备注）
   - 选择支付方式

2. 商家端：
   - 接收订单通知
   - 确认订单（可拒单）
   - 准备餐品
   - 通知配送

3. 骑手端：
   - 接单
   - 到店取餐
   - 配送中
   - 完成订单

4. 异常处理：
   - 商家拒单 → 退款
   - 骑手超时 → 自动改派
   - 用户取消 → 判断是否收取取消费
```

**❌ 不好的提示词**（模糊、没细节）

```
画个外卖流程
```

### 迭代优化策略

```
第 1 轮：快速生成基础版
"画一个用户登录流程"

第 2 轮：补充核心逻辑
"加上手机验证码登录"

第 3 轮：完善异常处理
"验证码输错 3 次锁定账号"

第 4 轮：优化体验细节
"添加自动登录（记住密码 7 天）"

第 5 轮：美化布局
"把节点对齐一下，布局更清晰"
```

**关键**：不要一次性想全，边生成边完善。

---

## 🛠️ 技术栈

**前端**
- Next.js 14 + TypeScript 5.7
- React Flow 11（Flow Canvas）
- Excalidraw 0.18（白板）
- Tailwind CSS 3.4（样式）

**后端**
- FastAPI 0.115 + Python 3.12
- 多 AI 模型接入（Gemini、GPT-4、Claude）
- RESTful API

---

## 🗺️ 开发路线图

### ✅ 已完成（v0.5）

- [x] Flow Canvas 拖拽编辑
- [x] Excalidraw 白板
- [x] AI 对话生成（多模型）
- [x] 图片智能识别
- [x] 12+ 主题系统
- [x] BPMN 节点支持

### 🚧 规划中（v0.6+）

**协作功能**
- [ ] 实时多人编辑（像 Figma 一样）
- [ ] 评论和批注
- [ ] 版本历史

**AI 能力增强**
- [ ] 流程优化建议（AI 指出流程中的问题）
- [ ] 自动补全缺失步骤
- [ ] 风险点提示

**知识库**
- [ ] 保存常用模板
- [ ] 团队模板库
- [ ] 智能推荐相似流程

**导出增强**
- [ ] 高清 PNG/SVG
- [ ] PDF 多页导出
- [ ] PowerPoint 演示文稿

---

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-idea`)
3. 提交代码 (`git commit -m 'feat: add amazing idea'`)
4. 推送分支 (`git push origin feature/amazing-idea`)
5. 提交 Pull Request

---

## ❓ 常见问题

<details>
<summary><b>1. 为什么我的想法 AI 生成得不准确？</b></summary>

**原因**：提示词太简单或太模糊。

**解决方案**：
- 分步骤描述（第一步、第二步...）
- 说明角色（用户、商家、系统）
- 说明判断条件（如果...则...）
- 补充技术细节（使用 Redis、MySQL）

查看 [使用技巧](#-使用技巧) 了解更多。
</details>

<details>
<summary><b>2. 能处理多复杂的流程？</b></summary>

- ✅ 简单流程（5-10 个节点）：秒生成
- ✅ 中等复杂（20-30 个节点）：效果很好
- ⚠️ 超复杂（50+ 个节点）：建议拆分成多个子流程

**技巧**：先画主流程，再逐步展开子流程。
</details>

<details>
<summary><b>3. 支持协作吗？</b></summary>

当前版本不支持实时协作，但可以：
- 导出图片发给团队
- 导出 JSON 文件分享
- 通过 Git 管理流程图版本

实时协作功能在 v0.6 规划中。
</details>

<details>
<summary><b>4. 和其他流程图工具的区别？</b></summary>

| 工具 | 定位 | 核心特点 |
|-----|------|---------|
| **ArchBoard** | 思维整理助手 | AI 对话生成，快速可视化想法 |
| ProcessOn | 在线绘图工具 | 手动拖拽，模板丰富 |
| Visio | 专业绘图软件 | 功能强大，学习成本高 |
| Mermaid | 代码转图表 | 程序员友好，语法门槛 |
| Excalidraw | 手绘白板 | 自由涂鸦，缺少 AI |

**ArchBoard 独特之处**：
- ✅ 降低门槛：说话就能画，不用学工具
- ✅ 快速迭代：对话式调整，想法越来越清晰
- ✅ 双引擎：规范图 + 自由画，灵活切换
</details>

---

## 📜 开源协议

MIT License - 自由使用、修改、商用

---

## 🙏 致谢

- [React Flow](https://reactflow.dev/) - 强大的节点画布
- [Excalidraw](https://excalidraw.com/) - 优雅的手绘白板
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python 框架
- [Next.js](https://nextjs.org/) - 优秀的 React 框架

感谢所有贡献者！

---

## 📬 联系我们

- **GitHub Issues**: [提问题 / 提建议](https://github.com/luguochang/SmartArchitect/issues)
- **GitHub Discussions**: [讨论区](https://github.com/luguochang/SmartArchitect/discussions)

---

## ⭐ 给个 Star 支持一下！

如果 ArchBoard 帮你理清了思路，请给个 Star 鼓励一下 🌟

[![Star History Chart](https://api.star-history.com/svg?repos=luguochang/SmartArchitect&type=Date)](https://star-history.com/#luguochang/SmartArchitect&Date)

---

<div align="center">

**让想法清晰，让沟通高效**

Made with ❤️ by [ArchBoard Team](https://github.com/luguochang/SmartArchitect/graphs/contributors)

[⬆️ 回到顶部](#archboard)

</div>
