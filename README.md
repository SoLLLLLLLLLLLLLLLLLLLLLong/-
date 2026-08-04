# AI创作工坊

一个基于 `uni-app + Vue 3 + JavaScript` 的微信小程序 AI 创作平台，同时也是一个面向内容生产场景的轻量级 `AI Agent` 应用。当前聚焦于：

- AI 图片生成
- AI 文案生成
- AI 配音与音频预览
- 数字人口播创作
- 作品记录与任务状态追踪

项目采用 `monorepo` 结构，前端是微信小程序，后端已迁移为 `FastAPI`，并拆分出独立的数字人 `worker` 服务，方便后续接入真实推理链路。

从工程视角看，这个项目不仅仅是“调用几个 AI 接口”，而是具备了典型 Agent 应用的几个关键特征：

- 根据用户目标选择不同能力链路，例如图片生成、文案生成、数字人口播
- 将一次创作拆成多步骤任务，而不是单次同步请求
- 通过后端统一代理模型能力、任务状态和结果回收
- 通过 worker 解耦上层业务与底层推理实现
- 支持长任务轮询、失败重试、结果恢复与作品沉淀

## 1. 项目简介

### 1.1 产品定位

`AI创作工坊` 面向内容创作场景，提供从“首页进入功能”到“生成作品并回看结果”的完整链路。

如果从简历或项目包装角度描述，它也可以定义为：

`一个面向微信小程序场景的 AI 创作 Agent 平台`

这里的 `Agent` 不是指通用聊天机器人，而是指：

- 以用户创作目标为起点
- 自动选择对应的 AI 能力模块
- 编排多步生成流程
- 持续跟踪任务状态
- 最终返回可消费的作品结果

当前项目重点实现了以下主流程：

1. 用户进入首页工作台
2. 点击 `AI图片` 进入图片生成功能，输入提示词后创建任务并轮询结果
3. 点击 `数字人口播` 进入四步创作流程：
   - 文案脚本
   - 声音合成
   - 数字人视频
   - 包装导出
4. 任务完成后在作品页查看预览、状态和结果

### 1.2 当前架构

- 小程序前端：`uni-app + Vue 3 + JavaScript`
- 业务后端：`FastAPI`
- 数字人 worker：`FastAPI`
- 共享工程结构：`monorepo`

### 1.3 为什么它可以算 Agent 项目

严格来说，这个项目目前更接近 `workflow-style AI Agent application`，也就是“工作流型 Agent 应用”，而不是完全自治式的开放智能体。

原因是它已经具备以下 Agent 特征：

1. `目标驱动`
   - 用户不是单纯调用一个接口，而是带着“生成图片”“生成口播视频”“导出作品”这样的目标进入系统。
2. `能力编排`
   - 系统会把目标拆成多个环节，例如文案、配音、数字人、导出。
3. `任务状态管理`
   - 长任务不是同步完成，而是以任务创建、轮询、恢复、失败重试的方式推进。
4. `工具调用代理`
   - 前端不直接连接模型，而是由后端统一代理模型调用、worker 调度和结果整合。
5. `结果闭环`
   - 最终产出不是一段文本，而是图片、音频、视频或作品记录。

所以在 README、简历和项目介绍里，可以把它表述为：

- `AI 创作工作流平台`
- `面向内容生产的 AI Agent 小程序`
- `具备多阶段任务编排能力的 AI 应用`

其中第三种表述最稳妥，也最工程化。

## 2. 技术栈

### 2.1 前端

- `uni-app`
  - 用于开发微信小程序端页面与交互
- `Vue 3`
  - 采用 `script setup` 组织页面逻辑
- `JavaScript`
  - 当前前端全部采用 JS，不使用 TypeScript
- `Pinia`
  - 用于管理数字人口播创作状态、任务状态、预览结果
- `SCSS / CSS`
  - 用于页面卡片、布局、渐变与移动端适配

### 2.2 后端

- `FastAPI`
  - 提供业务 API
  - 提供数字人 worker API
- `uvicorn`
  - 用于运行 FastAPI 服务
- `httpx`
  - 用于服务间调用和上游模型调用
- `python-dotenv`
  - 用于加载环境变量

### 2.3 AI / 服务能力

- `DeepSeek / SiliconFlow`
  - 用于文案生成
  - 用于 Embedding 能力占位
- `Kwai-Kolors/Kolors`
  - 当前作为 AI 图片生成测试模型
- `MuseTalk / Wav2Lip / SadTalker`
  - 当前在架构上通过 `avatar-worker` 预留接入位
  - 默认先走统一 worker 抽象层，不直接绑定某一个推理仓库

## 3. 目录结构

```text
小程序/
├─ apps/
│  └─ miniprogram/              # uni-app 微信小程序前端
├─ services/
│  ├─ api/                      # FastAPI 业务后端
│  └─ avatar-worker/            # FastAPI 数字人 worker
├─ packages/
│  └─ shared/                   # 共享常量与任务状态定义
├─ .env
├─ .env.example
├─ package.json                 # npm workspace 根入口
└─ README.md
```

## 4. 运行方式总览

这个项目推荐采用下面的开发方式：

- 小程序前端在本地电脑运行
- API 后端可以在本地运行，也可以部署到服务器运行
- 数字人 worker 可以在本地运行，也可以部署到服务器运行
- 微信小程序页面预览必须通过本地 `微信开发者工具`

也就是说，最常见的开发模式是：

1. 本地 VS Code 写前端代码
2. 本地运行 `npm run dev:miniprogram`
3. 本地使用微信开发者工具导入小程序产物目录
4. 后端和 worker 运行在本地或服务器
5. 小程序通过 `API_BASE_URL` 请求远程或本地后端

## 5. 环境准备

### 5.1 必备软件

请先安装：

- `Node.js` 18+
- `npm` 9+
- `Python` 3.10+
- `微信开发者工具`

如果你用 `conda`，也可以先创建 Python 虚拟环境再装后端依赖。

### 5.2 推荐开发环境

- 编辑器：`VS Code`
- 小程序预览工具：`微信开发者工具`
- Python 环境：`conda` 或系统 Python

## 6. 环境变量配置

项目根目录有示例文件 [`.env.example`](D:\GZHU\CodexDocuments\小程序\.env.example)。

先复制一份：

```bash
cp .env.example .env
```

Windows PowerShell 也可以手动复制。

### 6.1 示例环境变量

```env
DEEPSEEK_API_KEY=replace-me
DEEPSEEK_BASE_URL=https://api.siliconflow.cn/v1
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-V4-Flash

EMBEDDING_API_KEY=replace-me
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B

WEATHER_API_KEY=replace-me

API_PORT=3000
API_BASE_URL=http://172.22.121.135:3000

AVATAR_WORKER_URL=http://127.0.0.1:4000
AVATAR_WORKER_PORT=4000
AVATAR_PROVIDER=musetalk

PUBLIC_FILE_BASE_URL=https://files.example.com

MUSE_TALK_ENDPOINT=
WAV2LIP_ENDPOINT=
SADTALKER_ENDPOINT=
```

### 6.2 说明

- `API_BASE_URL`
  - 给小程序前端使用
  - 如果你的后端跑在服务器上，这里填服务器地址，例如 `http://172.22.121.135:3000`
- `AVATAR_WORKER_URL`
  - 给 API 服务调用 worker 使用
- `DEEPSEEK_API_KEY`
  - 仅后端使用，不允许放在前端代码中

## 7. 安装依赖

### 7.1 安装前端 workspace 依赖

在项目根目录 [package.json](D:\GZHU\CodexDocuments\小程序\package.json) 下执行：

```bash
npm install
```

### 7.2 安装 Python 后端依赖

#### services/api

```bash
pip install -r services/api/requirements.txt
```

#### services/avatar-worker

```bash
pip install -r services/avatar-worker/requirements.txt
```

如果你使用 `conda`，建议先激活虚拟环境后再执行。

## 8. 启动流程

## 8.1 方式一：本地完整启动

适合本地联调。

### 第一步：启动数字人 worker

在项目根目录执行：

```bash
npm run dev:avatar-worker
```

默认监听：

```text
http://127.0.0.1:4000
```

### 第二步：启动 API 后端

另开一个终端，在项目根目录执行：

```bash
npm run dev:api
```

默认监听：

```text
http://127.0.0.1:3000
```

### 第三步：启动小程序前端编译

再开一个终端，在项目根目录执行：

```bash
npm run dev:miniprogram
```

成功后会生成微信小程序开发产物目录。

### 第四步：微信开发者工具导入

开发模式下导入：

```text
dist/dev/mp-weixin
```

生产构建模式导入：

```text
dist/build/mp-weixin
```

如果你执行的是：

```bash
npm run build:miniprogram
```

那么应该导入：

```text
dist/build/mp-weixin
```

## 8.2 方式二：后端放服务器，本地只跑小程序

这是更推荐的日常开发方式。

### 服务器上运行

在服务器项目目录执行：

```bash
npm run dev:avatar-worker
npm run dev:api
```

或者分别在两个终端执行。

### 本地运行

在本地项目目录执行：

```bash
npm install
npm run dev:miniprogram
```

然后本地微信开发者工具导入：

```text
dist/dev/mp-weixin
```

同时确保前端配置中的 `API_BASE_URL` 指向服务器，例如：

```js
export const API_BASE_URL = 'http://172.22.121.135:3000'
```

对应配置文件一般位于：

[apps/miniprogram/src/config/app.js](D:\GZHU\CodexDocuments\小程序\apps\miniprogram\src\config\app.js)

## 8.3 方式三：仅构建前端产物

如果你只想生成小程序包：

```bash
npm run build:miniprogram
```

导入目录：

```text
dist/build/mp-weixin
```

## 9. 常用命令

在项目根目录执行：

```bash
npm run dev:miniprogram
npm run build:miniprogram
npm run dev:api
npm run dev:avatar-worker
npm run check:api
npm run check:avatar-worker
```

## 10. 当前功能说明

### 10.1 首页

- 顶部品牌区
- AI 图片入口
- AI 音频入口
- AI 视频入口
- 核心功能宫格
- 数字人口播 Banner 主入口

### 10.2 AI 图片

- 输入提示词
- 创建图片生成任务
- 轮询任务状态
- 回显生成图片预览

### 10.3 数字人口播

四步流程：

1. 文案脚本
2. 声音合成
3. 数字人视频
4. 包装导出

支持能力包括：

- 模板文案生成
- 脚本改写与润色
- 音色选择
- 图片素材上传
- 素材质量校验
- 数字人任务创建
- 视频预览
- 导出结果查看

### 10.4 作品页

- 查看任务结果
- 查看作品状态
- 查看失败原因
- 查看预览地址与导出地址

## 11. 接口说明

当前主要 API：

- `GET /api/health`
- `GET /api/discovery`
- `GET /api/works`
- `GET /api/tasks/:taskId`
- `POST /api/script/generate`
- `POST /api/voice/tasks`
- `POST /api/image/tasks`
- `POST /api/avatar/tasks`
- `POST /api/export/tasks`
- `POST /api/uploads/sign`

worker 接口：

- `GET /worker/health`
- `POST /worker/avatar/assets`
- `POST /worker/avatar/jobs`
- `GET /worker/avatar/jobs/:jobId`

## 12. 校验与检查

后端静态检查：

```bash
npm run check:api
npm run check:avatar-worker
```

前端构建检查：

```bash
npm run build:miniprogram
```

## 13. 常见问题

### 13.1 为什么小程序不能完全在服务器运行

因为微信小程序最终仍然需要通过本地 `微信开发者工具` 进行预览、调试和上传。服务器可以负责：

- 跑 API
- 跑 worker
- 构建前端产物

但小程序页面本身仍需要在本地工具中打开。

### 13.2 微信开发者工具导入哪个目录

- 开发模式：`dist/dev/mp-weixin`
- 构建模式：`dist/build/mp-weixin`

### 13.3 如果后端在服务器上，本地怎么访问

把前端配置中的 `API_BASE_URL` 改为服务器地址，例如：

```js
export const API_BASE_URL = 'http://172.22.121.135:3000'
```

同时确保服务器安全组、防火墙和端口开放正确。

### 13.4 本地小程序请求服务器后端失败怎么办

如果本地微信开发者工具里看到类似：

```text
GET http://172.22.121.135:3000/api/discovery 502 Bad Gateway
```

优先按下面顺序排查。

第一步，确认服务器代码是不是最新版本：

```bash
cd /home/NBN/NBN/agent/小程序
cat services/api/package.json
cat services/avatar-worker/package.json
```

新版后端应该看到：

```json
"version": "0.2.0"
```

并且启动脚本应该是：

```json
"dev": "python -m src.main --reload"
```

如果终端里仍然显示：

```text
node --watch src/index.js
@ai-creator-workshop/api@0.1.0
```

说明服务器上运行的还是旧版 Node 后端，需要先把本地最新项目同步到服务器，或者确认自己进入的是正确目录。

第二步，安装 Python 后端依赖：

```bash
pip install -r services/api/requirements.txt
pip install -r services/avatar-worker/requirements.txt
```

第三步，启动 worker 和 API：

```bash
npm run dev:avatar-worker
npm run dev:api
```

新版 FastAPI 服务应由 `uvicorn` 启动，并监听：

```text
0.0.0.0:3000
0.0.0.0:4000
```

第四步，在服务器本机验证接口：

```bash
curl http://127.0.0.1:3000/api/health
curl http://127.0.0.1:4000/worker/health
```

第五步，在本地电脑验证服务器端口是否能访问：

```powershell
curl http://172.22.121.135:3000/api/health
```

如果服务器本机能访问，但本地电脑不能访问，通常是：

- 服务只监听了 `127.0.0.1`
- 服务器防火墙没有开放 `3000`
- 云服务器安全组没有开放 `3000`
- 中间有 Nginx/代理返回了 `502`
- 本地电脑和 `172.22.121.135` 不在同一个网络/VPN

第六步，微信开发者工具开发阶段需要打开：

```text
详情 -> 本地设置 -> 不校验合法域名、web-view、TLS 版本以及 HTTPS 证书
```

开发阶段可以用 `http://172.22.121.135:3000`。正式上线时必须配置微信小程序合法域名，并建议使用 `https`。

也可以直接在服务器项目根目录运行诊断脚本：

```bash
bash scripts/server-diagnose.sh
```

如果需要指定公网/局域网访问地址：

```bash
PUBLIC_API_URL=http://172.22.121.135:3000 bash scripts/server-diagnose.sh
```

诊断结果里重点看三处：

- `Package versions` 是否是 `0.2.0` 和 `python -m src.main --reload`
- `Listening ports` 中 `3000` 是否监听在 `0.0.0.0:3000`，而不是只有 `127.0.0.1:3000`
- `Local image task` 是否返回 `code: 0`

## 14. 后续规划

- 接入真实数字人推理链路
- 接入对象存储
- 接入数据库
- 接入队列系统
- 接入微信登录
- 完善作品中心与任务中心
- 接入更完整的 AI 图片、音频、视频能力

## 15. 备注

当前版本重点是：

- 小程序工作台体验
- FastAPI 后端架构
- AI 任务流
- 数字人口播流程化

其中数字人推理目前仍以统一 worker 抽象和模拟结果为主，后续可以在不改前端接口的情况下继续接入真实推理能力。
