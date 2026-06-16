# 基于大模型的个人智能助手 Web 问答系统

一个基于 `Vue 3 + Vite + FastAPI + SQLite + FAISS` 的个人智能助手 Web 问答系统，支持多轮对话、会话管理、文件上传、联网搜索、文档检索、流式回复与会话记忆。

这个项目当前更适合用于：

- 前端 / 全栈开发实习项目展示
- 大模型 Web 应用开发练习
- RAG 与多轮对话系统的基础工程实践

## 项目概览

系统分为两部分：

- 前端：基于 `Vue 3 + Vite + Vue Router + JavaScript` 实现页面、交互与前后端联调
- 后端：基于 `FastAPI + SQLite` 提供用户、会话、消息、文件上传、天气、流式问答等接口能力

在业务能力上，系统支持：

- 用户登录与注册
- 多会话管理
- 历史消息持久化
- 文件上传与知识库问答
- 普通问答、联网搜索、文档检索三类问答场景
- 流式回复与生成中断
- 多轮对话记忆与历史摘要压缩

---

## 前端实现

前端工程位于 `frontend/` 目录，采用标准的 `Vue 3 + Vite` 工程结构，已经拆分为页面、组件、路由与组合式逻辑。

### 前端技术栈

- `Vue 3`
- `Vite`
- `Vue Router`
- `JavaScript`
- `CSS`

### 前端主要功能

- 登录页与聊天页分离
- 基于路由实现页面跳转
- 会话列表展示、切换、重命名、删除
- 消息列表展示与自动滚动
- 支持回车发送消息
- 文件上传与文档绑定提示
- 模型思考过程展示
- 流式输出渲染
- 停止生成
- 天气卡片展示

### 前端工程结构

```text
frontend/
├─ src/
│  ├─ api/
│  │  └─ client.js
│  ├─ components/
│  │  ├─ ChatHeader.vue
│  │  ├─ ComposerPanel.vue
│  │  ├─ ConversationList.vue
│  │  ├─ ConversationListItem.vue
│  │  ├─ EmptyState.vue
│  │  ├─ MessageList.vue
│  │  ├─ SidebarPanel.vue
│  │  ├─ SourcesPanel.vue
│  │  ├─ ThinkingPanel.vue
│  │  └─ WeatherCard.vue
│  ├─ composables/
│  │  └─ useAssistantApp.js
│  ├─ pages/
│  │  ├─ AuthPage.vue
│  │  └─ ChatPage.vue
│  ├─ router/
│  │  └─ index.js
│  ├─ App.vue
│  ├─ main.js
│  └─ styles.css
├─ index.html
├─ package.json
└─ vite.config.js
```

### 前端设计思路

- 使用 `Vue Router` 将登录页和聊天页拆开，避免所有内容堆在同一个组件里
- 使用组件化方式拆分会话列表、天气卡片、消息区、思考面板、输入区等模块
- 使用 `useAssistantApp.js` 统一管理前端核心状态与交互逻辑
- 使用 `api/client.js` 统一封装接口请求，降低页面与后端的耦合
- 使用 `AbortController` 实现生成中断
- 使用流式响应读取实现消息逐段输出

### 前端开发说明

#### 本地开发

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

#### 前端代理说明

开发环境下，`Vite` 已配置 `/api` 代理：

- 前端地址：`5173`
- 后端地址：`8000`

因此在 `5173` 页面下调用 `/api/...` 时，请求会自动转发到 `FastAPI` 后端。

#### 构建说明

```bash
npm run build
```

执行后会将前端源码打包为浏览器可直接运行的静态文件，并输出到：

- `llm_backend/static/dist`

这样后端启动后，访问 `8000` 就能加载最新的前端页面。

### 前端补充文档

如果想进一步了解前端实现思路，可查看：

- [frontend.md](/D:/GZHU/智能客服Agent/customer%20service/deepseek_agent/frontend.md)

---

## 后端实现

后端工程位于 `llm_backend/` 目录，使用 `FastAPI` 提供接口能力，并通过 `SQLite` 实现轻量持久化。

### 后端技术栈

- `Python`
- `FastAPI`
- `SQLAlchemy`
- `Pydantic`
- `SQLite`
- `FAISS`

### 后端主要能力

- 用户注册、登录与 JWT 鉴权
- 会话创建、查询、重命名、删除
- 历史消息持久化
- 文件上传与文档解析
- 向量索引构建与检索
- 流式问答接口
- 天气接口封装
- 自动路由问答
- 会话记忆与历史摘要压缩

### 后端目录结构

```text
llm_backend/
├─ app/
│  ├─ api/          # 接口路由
│  ├─ core/         # 配置、数据库、安全等
│  ├─ models/       # 数据模型
│  ├─ schemas/      # 请求与响应结构
│  ├─ services/     # 聊天、搜索、检索、记忆等核心服务
│  └─ tools/        # 工具能力封装
├─ logs/
├─ scripts/
│  └─ init_db.py
├─ static/
│  └─ dist/         # 前端打包产物
├─ uploads/
├─ .env
├─ main.py
└─ run.py
```

### 后端问答链路

用户发送问题后，后端大致会经历以下流程：

1. 读取当前会话历史与摘要记忆
2. 判断当前问题更适合普通问答、联网搜索还是文档检索
3. 如当前会话绑定了文档，则优先走文档检索链路
4. 将上下文、检索结果或搜索结果交给大模型生成最终回复
5. 通过流式接口将回复逐段返回给前端
6. 回答结束后保存消息并按需更新摘要记忆

---

## 当前实现功能

### 1. 用户与会话

- 用户注册、登录、鉴权
- 多会话创建与管理
- 会话重命名与删除
- 历史消息持久化

### 2. 问答能力

- 普通问答
- 联网搜索问答
- 文档检索问答
- 自动路由切换

### 3. 文档与知识库

- 支持上传 `PDF / DOCX / TXT / MD`
- 文本解析与切分
- Embedding 生成
- 本地 `FAISS` 向量索引
- 文档检索增强生成

### 4. 多轮记忆

- 保留最近消息作为短期上下文
- 使用历史摘要压缩早期对话
- 新会话对应独立的记忆上下文

### 5. 交互体验

- 思考过程展示
- 流式回复
- 停止生成
- 文件绑定提示
- 天气信息展示

---

## 快速开始

## 1. 后端环境准备

推荐 Python 版本：

- `Python 3.10`
- `Python 3.11`

创建虚拟环境并安装依赖：

```bash
python -m venv .cs_venv
```

Windows：

```powershell
.cs_venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS：

```bash
source .cs_venv/bin/activate
pip install -r requirements.txt
```

## 2. 配置环境变量

在 `llm_backend/.env` 中至少配置：

```env
CHAT_SERVICE=siliconflow
REASON_SERVICE=siliconflow
AGENT_SERVICE=siliconflow

SILICONFLOW_API_KEY=your_api_key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

DB_TYPE=sqlite

TAVILY_API_KEY=your_tavily_api_key

EMBEDDING_PROVIDER=siliconflow
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B

WEATHERAPI_KEY=your_weatherapi_key
WEATHER_DEFAULT_CITY=Beijing
```

说明：

- `SILICONFLOW_API_KEY` 用于大模型与 Embedding 调用
- `TAVILY_API_KEY` 用于联网搜索
- `WEATHERAPI_KEY` 用于天气展示
- 当前项目使用 `SQLite`，不再依赖 MySQL
- 当前主链路不依赖 Neo4j 和 GraphRAG

## 3. 初始化数据库

```bash
cd llm_backend
python scripts/init_db.py
```

## 4. 启动后端

```bash
python run.py
```

默认地址：

- 前端页面：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- 接口文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 5. 前端开发

```bash
cd frontend
npm install
npm run dev
```

开发地址：

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## 6. 构建前端到后端静态目录

```bash
cd frontend
npm run build
```

构建完成后，最新前端会被输出到：

- `llm_backend/static/dist`

---

## 项目定位

这个项目属于一个偏前端 / 全栈导向的大模型 Web 应用实践项目，重点体现：

- 前端组件化开发与页面路由管理
- 前后端接口联调能力
- 用户系统、会话系统与文件上传等完整业务闭环
- 流式响应、多轮对话与记忆压缩等交互实现
- 文档检索增强问答的基础工程落地
- Linux / Windows 环境下的部署、调试与问题排查

---

## 当前简化说明

当前保留的核心模块：

- Vue 前端页面与交互
- FastAPI 后端接口
- 普通问答
- 联网搜索
- 文档检索问答
- 会话记忆
- 文件上传与知识库

## 后续可扩展方向

- 将前端状态进一步拆分为更细粒度的 composable
- 增加文档管理页与知识库管理页
- 增加会话搜索、置顶、归档等功能
- 增加更完整的多 Agent / Workflow 模块
- 增加单元测试、接口测试与前端构建校验
