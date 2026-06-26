# 基于大模型的个人智能助手 Web 问答系统

这是一个前后端分离的多轮对话系统，定位是“个人智能助手 / 问答系统”，不是纯聊天 Demo。  
系统支持用户注册登录、会话管理、历史消息持久化、文件上传、文档检索、联网搜索、天气查询、工作区检索，以及基于大模型的自动路由问答。

<img width="2229" height="1215" alt="image" src="https://github.com/user-attachments/assets/2f4f0be4-875b-45f5-8d54-0534be5537f8" />
<img width="2229" height="1215" alt="aca6db2f-cd95-45fd-af28-24e5e29816bc" src="https://github.com/user-attachments/assets/21140b0f-11bb-4156-9499-48e567f0781d" />

当前项目已经从单一自动路由升级为轻量多 Agent 工作流：

- `Router Agent`：先判断本轮问题应该走普通回答、联网搜索、文档检索、工作区检索还是混合检索
- `Research Agent`：根据路由结果执行工具，拿外部证据并整理结果
- `Code Agent`：当问题偏代码场景时，额外检查代码回答是否合理，并尝试用 `black / prettier` 自动格式化代码块
- `Response Agent`：统一整合计划、证据、代码检查结果和上下文，生成最终回答
- `Memory Agent`：从用户对话里抽取偏好，写入长期记忆

## 核心功能

- 用户注册、登录、鉴权
- 会话创建、切换、重命名、删除
- 历史消息持久化
- 流式问答与中断控制
- 自动路由问答
- 联网搜索
- 基础 RAG 文档问答
- 工作区文件检索
- 天气信息查询
- 执行轨迹 trace 面板
- 用户画像 / 偏好记忆
- 代码问答增强与代码块格式化输出

## 技术栈

### 前端

- Vue 3
- Vite
- Vue Router
- Pinia
- JavaScript
- Fetch API
- Markdown 渲染

### 后端

- FastAPI
- Python
- SQLite
- SQLAlchemy
- FAISS
- 大模型 API
- WeatherAPI

## 项目结构

```text
deepseek_agent/
├─ frontend/                # Vue 3 前端
│  ├─ src/api/              # 接口封装
│  ├─ src/components/       # 页面组件
│  ├─ src/pages/            # 页面级组件
│  ├─ src/stores/           # Pinia 状态管理
│  └─ src/router/           # 路由配置
├─ llm_backend/             # FastAPI 后端
│  ├─ app/api/              # 认证等接口
│  ├─ app/core/             # 配置、数据库、鉴权、中间件
│  ├─ app/models/           # 数据模型
│  ├─ app/services/         # 业务服务层
│  └─ app/tools/            # 工具定义
└─ README.md
```

## 快速开始

### 1. 安装后端依赖

```bash
python -m venv .cs_venv
source .cs_venv/bin/activate
pip install -r requirements.txt
pip install aiosqlite
```

### 2. 配置环境变量

在 `llm_backend/.env` 中至少配置：

```env
CHAT_API_KEY=your_key
CHAT_BASE_URL=https://api.siliconflow.cn/v1
CHAT_MODEL_NAME=your_model

AGENT_API_KEY=your_key
AGENT_BASE_URL=https://api.siliconflow.cn/v1
AGENT_MODEL_NAME=your_model

WEATHERAPI_KEY=your_weather_api_key
TAVILY_API_KEY=your_tavily_key
```

### 3. 启动后端

进入后端目录，安装依赖并启动：

```bash
cd llm_backend
pip install -r requirements.txt
python run.py
```

默认会启动 FastAPI 服务，前端构建产物也可以由后端静态托管。

### 2. 启动前端开发环境

```bash
cd frontend
npm install
npm run dev
```

### 3. 构建前端

```bash
cd frontend
npm run build
```


如果是开发模式，前端通常运行在 `5173`，通过代理转发到后端接口。  
如果是构建后交给后端托管，则访问后端地址即可。
