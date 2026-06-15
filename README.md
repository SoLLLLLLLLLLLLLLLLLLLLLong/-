# 个人智能助手问答系统

一个基于 `FastAPI + Vue 3 + Vite + SQLite + FAISS` 的个人智能助手问答系统，支持多轮对话、自动路由、联网搜索、文档上传解析、知识库检索、会话记忆与流式回复。


## 项目特点

- 支持用户注册、登录与基于 JWT 的鉴权
- 支持多会话管理、历史消息持久化与会话切换
- 支持自动路由问答，可在普通回答、联网搜索、文档检索之间自动选择
- 支持上传 `PDF / DOCX / TXT / MD` 文档并建立本地知识库索引
- 支持基于 `FAISS` 的向量检索增强生成
- 支持短期上下文 + 历史摘要压缩的会话记忆机制
- 支持流式输出、思考中提示、手动停止生成
- 支持天气信息展示与基础前端交互

## 当前实现功能

### 1. 对话与会话

- 创建新会话
- 会话重命名
- 删除会话
- 同一会话内历史消息持久化
- 多轮对话连续上下文

### 2. 自动路由问答

系统会根据用户问题自动判断走哪条链路：

- 普通问答
- 联网搜索
- 文档检索问答

### 3. 文档检索与知识库

- 上传文档到当前会话
- 解析文档文本内容
- 文本切分
- 调用 Embedding 模型生成向量
- 使用 `FAISS` 建立本地索引
- 检索相关片段后再交给大模型生成答案

### 4. 记忆机制

- 保留当前会话最近消息作为短期记忆
- 将较早历史压缩为 summary，减少上下文 token 消耗
- 新建会话对应新的独立记忆
- 删除会话时同步删除对应历史数据

### 5. 前端交互

- 登录页与聊天页分离
- 支持回车发送消息
- 无会话时首次发送自动创建新会话
- 支持上传文档后在输入区附近显示文件名
- 支持移除已上传文档
- 支持消息区独立滚动
- 支持模型生成中显示“正在思考中”
- 支持中断生成

## 技术栈

### 后端

- `Python`
- `FastAPI`
- `SQLAlchemy`
- `Pydantic`
- `Uvicorn`

### 数据与存储

- `SQLite`
- `FAISS`

### 大模型与外部能力

- `SiliconFlow API`
- `Tavily Search API`
- `WeatherAPI`

### 前端

- `Vue 3`
- `Vite`
- `JavaScript`
- `CSS`

## 项目结构

```text
deepseek_agent/
├─ frontend/                    # Vue + Vite 前端工程源码
│  ├─ src/
│  │  ├─ api/
│  │  │  └─ client.js
│  │  ├─ App.vue
│  │  ├─ app-options.js
│  │  ├─ main.js
│  │  └─ styles.css
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ llm_backend/
│  ├─ app/
│  │  ├─ api/                  # 接口路由
│  │  ├─ core/                 # 配置、数据库、安全等
│  │  ├─ models/               # 数据模型
│  │  ├─ schemas/              # 请求与响应结构
│  │  ├─ services/             # 聊天、检索、记忆、搜索等核心服务
│  │  └─ tools/                # 工具能力封装
│  ├─ static/dist/             # 前端打包产物，由 Vite 输出到这里
│  ├─ scripts/init_db.py       # 初始化数据库
│  ├─ main.py                  # FastAPI 应用入口
│  └─ run.py                   # 本地启动脚本
├─ uploads/                    # 上传文档及索引相关数据
├─ requirements.txt
└─ README.md
```

## 系统主链路

1. 用户登录后进入聊天界面。
2. 用户发送问题，系统读取当前会话历史与摘要记忆。
3. 路由模块判断当前问题更适合：
   - 普通回答
   - 联网搜索
   - 文档检索
4. 如果当前会话关联了文档，则优先进行知识库检索。
5. 将检索结果、搜索结果和历史上下文交给大模型生成最终答案。
6. 回复结束后保存消息，并按需更新摘要记忆。

## 快速开始

### 1. 后端环境准备

推荐 Python 版本：

- `Python 3.10` 或 `Python 3.11`

创建虚拟环境：

激活虚拟环境
source .cs_venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

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

- `SILICONFLOW_API_KEY` 用于大模型和 Embedding 调用
- `TAVILY_API_KEY` 用于联网搜索
- `WEATHERAPI_KEY` 用于天气信息展示
- 当前项目使用 `SQLite`，不再依赖 MySQL
- 当前主链路不依赖 Neo4j 和 GraphRAG

### 3. 初始化数据库

```bash
cd llm_backend
python scripts/init_db.py
```

### 4. 启动后端

```bash
python run.py
```

默认访问地址：

- 前端页面：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- 接口文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 5. 前端开发

```bash
cd frontend
npm install
npm run dev
```

默认前端开发地址通常为：

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

构建前端到后端静态目录：

```bash
npm run build
```

打包后产物会输出到：

- `llm_backend/static/dist`

## 项目定位

这个项目属于一个轻量级、可运行、可展示的 LLM 应用实践项目，重点体现：

- 从前后端到部署的完整闭环
- 自动路由问答的基础 Agent 思路
- 文档检索增强生成的基础实现
- 多轮会话与记忆管理
- 在真实开发中处理依赖、部署、超时、中断与交互细节的能力

## 当前简化说明

为保证项目可部署、可演示、便于实习展示，当前保留的是轻量版本主链路，已经移除或暂时关闭：

- GraphRAG 深度索引链路
- Neo4j 图谱问答链路
- MySQL 依赖

当前版本主要保留：

- 普通问答
- 联网搜索
- 文档检索问答
- 会话记忆
- 文档上传与知识库
- Vue 前端交互

## 适合简历展示的点

- 基于 `FastAPI + Vue + SQLite + FAISS` 搭建完整的个人智能助手问答系统
- 实现自动路由问答，支持普通回答、联网搜索与文档检索
- 搭建基础 RAG 链路，支持文档解析、向量索引与知识库问答
- 实现多轮会话记忆与摘要压缩，优化上下文利用
- 完成 Linux / Windows 环境下的调试、部署与问题排查

## 后续可扩展方向

- 将前端进一步拆分为多个 Vue 组件
- 补充更完整的多 Agent workflow
- 增加工具调用可观测性与日志追踪
- 增加回答失败后的重试与恢复机制
- 增加文档管理页与知识库管理页
- 补充单元测试与接口测试
