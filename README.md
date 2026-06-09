# Personal Assistant Dialogue System

一个基于 `FastAPI + LLM API + RAG` 的个人智能助手对话系统，支持多轮对话、自动路由、联网搜索、文档问答、会话记忆和轻量部署。

这个项目更偏向一个适合学习和展示的 **LLM 应用 / 基础 Agent 实践项目**：它不是只做单轮聊天，而是把对话、搜索、文档检索和历史记忆串成了一条完整链路。
![Uploading image.png…]()

## 项目特点

- 自动路由问答：根据用户问题自动选择普通回答、联网搜索或文档检索
- 多轮对话能力：支持会话切换、历史消息持久化与流式回复
- 文档知识增强：支持上传 `PDF / DOCX / TXT / MD`，围绕文档进行问答
- 记忆压缩机制：保留最近消息，并对更早历史做 summary 压缩，减少 token 消耗
- 轻量部署：使用 `SQLite + FAISS`，不依赖 MySQL、Neo4j 等重型组件即可运行
- 前端可直接体验：登录后即可使用对话、搜索、文档问答、天气卡片等功能

## 当前实现功能

- 用户注册、登录与 JWT 鉴权
- 会话创建、重命名、删除
- 历史消息持久化
- 大模型流式回复
- 自动路由
  - 普通回答
  - 联网搜索
  - 文档检索
- 文档上传与解析
  - 支持 `PDF / DOCX / TXT / MD`
  - 文本切分、Embedding、FAISS 本地向量索引
- 会话记忆
  - 最近消息保留
  - 历史摘要压缩
- 思考过程展示
  - 路由判断
  - 搜索 / 检索中间过程
- 首页天气卡片

## 技术栈

- 后端：`Python`、`FastAPI`、`SQLAlchemy`
- 数据库：`SQLite`
- 大模型接口：`SiliconFlow / OpenAI-compatible API`
- Embedding：`SiliconFlow Embedding API`
- 检索增强：`FAISS`
- 文档解析：`PyPDF2`、`python-docx`
- 前端：`HTML`、`CSS`、`JavaScript`
- 部署环境：`Linux / Windows`

## 系统流程

1. 用户登录后进入对话页面，创建或切换会话。
2. 用户发送问题后，后端先读取当前会话历史与摘要，补全上下文。
3. 路由模块判断当前问题更适合：
   - 普通回答
   - 联网搜索
   - 文档检索
4. 如果当前会话已关联文档，系统会先在向量索引中检索相关片段，再交给模型生成答案。
5. 回答完成后，用户消息和助手回复会保存到数据库；当会话较长时，会触发 summary 压缩。

## 目录结构

```text
deepseek_agent/
├─ llm_backend/
│  ├─ app/
│  │  ├─ api/              # 登录鉴权接口
│  │  ├─ core/             # 配置、数据库、日志、中间件、安全
│  │  ├─ models/           # 用户、会话、消息数据模型
│  │  ├─ schemas/          # Pydantic 请求/响应结构
│  │  ├─ services/         # 聊天、自动路由、检索、会话、搜索等服务
│  │  └─ tools/            # 搜索工具定义
│  ├─ static/dist/         # 前端页面与静态资源
│  ├─ scripts/init_db.py   # 数据库初始化脚本
│  ├─ main.py              # FastAPI 应用入口
│  └─ run.py               # 启动脚本
├─ requirements.txt
└─ README.md
```

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

参考根目录 `.env.example`，在 `llm_backend/.env` 中至少配置：

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

- `TAVILY_API_KEY` 用于联网搜索
- `EMBEDDING_PROVIDER=siliconflow` 表示文档向量化走 SiliconFlow 的 embedding 接口
- `WEATHERAPI_KEY` 用于首页天气展示，不配置也不影响核心聊天功能
- 如果不配置搜索 key，普通对话和文档问答仍可使用

### 3. 初始化数据库

```bash
cd llm_backend
python scripts/init_db.py
```

### 4. 启动服务

```bash
python run.py
```

默认访问地址：

- 前端页面：[http://localhost:8000](http://localhost:8000)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

## 适合展示的项目点

如果你把它作为简历或实习项目展示，比较适合突出这些点：

- 基于 `FastAPI + LLM API` 搭建完整对话系统
- 实现自动路由的基础 Agent 闭环
- 实现文档上传、Embedding、向量检索与问答
- 实现多轮会话记忆与 summary 压缩
- 实际完成 Linux 服务器部署、依赖调试与工程问题排查

## 当前版本说明

本项目当前保留的是轻量可部署版本，聚焦：

- 多轮对话
- 自动路由
- 联网搜索
- 文档问答
- 会话记忆
- 轻量前端交互

当前主链路 **不包含** 图谱问答、GraphRAG 和 Neo4j 功能。

## 适用场景

- 个人智能助手
- 基础知识增强对话系统
- LLM 应用 / Agent 实习项目展示
- 多轮对话与 RAG 的教学或练习项目
