把“前端怎么获取后端数据”分成 4 层来讲，这样最清楚：
页面层：用户触发操作  
业务层：组织请求参数、管理状态  
请求层：真正发送 HTTP 请求  
展示层：拿到结果后更新页面

我把接口请求统一封装在 client.js 里，里面负责 3 件事：一是发 HTTP 请求，二是自动带上 token，三是统一处理错误。这样页面和业务逻辑层就不用重复写这些底层细节。

## 登录流程：
页面上用户点登录
页面调用 handleLogin()
handleLogin() 再调用 login()
login() 在 client.js 里发请求到 /api/token
后端返回 access_token
handleLogin() 把 token 存进 localStorage
再调用 bootstrapUser()
bootstrapUser() 调用 getCurrentUser() 和 refreshConversations()
最后把用户信息、会话列表写进 state


## 普通接口的数据是怎么传送的
比如获取会话列表。
链路是这样的：
前端调用 getConversations(userId)
这个函数在 client.js 里执行 fetch('/api/conversations/user/${userId}')
后端返回 JSON 数据
前端 response.json() 解析成 JavaScript 对象
useAssistantApp.js 里的 refreshConversations() 把结果赋值给 state.conversations
左侧会话列表组件收到新的 conversations，自动重新渲染

## “获取历史消息”再理解一次：
switchConversation(conversationId) 被触发
如果本地还没有这个会话的消息
就调用 getConversationMessages(conversationId, userId)
后端返回这个会话的消息数组
前端把结果写到 state.messagesByConversation[conversationId]
currentMessages 是一个 computed
MessageList 用到 currentMessages
所以消息区自动更新


## 前端怎么拿到流式数据（这个回答还太泛了，缺乏细节）
后端每推来一段数据，reader.read() 就能读到一段，前端解析完以后立刻更新状态。

## 前端怎么知道当前收到的是哪种状态
因为后端返回的数据里带了 type 字段。
比如后端会发这种数据：
type: "thinking"
type: "route"
type: "sources"
type: "content"
前端在 handleStreamEvent(payload) 里专门判断：
如果是 route，更新路由信息
如果是 thinking，更新思考面板
如果是 sources，更新来源列表
如果是 content，就把正文追加到 AI 的最后一条消息里
所以你可以这样说：
“前后端之间约定了一套事件格式，前端不是随便收到一段文本就乱显示，而是先看它的 type，再决定更新哪个区域。

## 后端是怎么把这些数据一段段发给前端的
接口：/api/agent/chat，不会一次性返回完整结果，而是保持连接，边生成边发，所以后端“通知前端状态变化”的方式，不是额外发通知接口，而是直接在同一个流连接里发送不同阶段的事件。

我这个项目里前端和后端的数据交互做了分层。最底层是 client.js，负责统一封装接口请求，包括 fetch、token 注入和错误处理；中间层是 useAssistantApp.js，负责调用这些接口，并把返回结果写入 Vue 的响应式状态，比如用户信息、会话列表、消息列表、来源信息、生成状态等；页面层像 ChatPage.vue 和消息组件，只负责把这些状态展示出来并绑定用户交互。普通接口比如登录、获取会话列表、获取历史消息，都是请求一次、返回一次 JSON，然后写入状态。流式聊天接口则不同，它请求的是后端的 text/event-stream，前端通过 ReadableStream 持续读取后端一段一段返回的数据，并按事件 type 分发处理。比如 thinking 用来更新思考面板，sources 用来更新检索来源，content 用来实时追加 AI 正文，所以最终用户看到的是无刷新、流式、实时更新的聊天效果

## 结束后还要刷新会话列表和历史消息，这个是怎么实现实时更新的
前端先本地实时渲染，流结束后再主动拉一次后端最新数据

这个项目里聊天生成过程中，前端会先把用户消息和 assistant 占位消息直接写进本地状态，然后一边接收后端流式返回，一边把内容追加到当前消息里，所以用户看到的是实时生成。等流式响应结束后，前端会再主动调用一次获取历史消息和会话列表的接口，把后端已经持久化的正式数据重新同步回来，保证页面展示和数据库状态一致。

## 结束后还要刷新会话列表和历史消息，这个是怎么实现实时更新的
我这个项目里前端已经做了中断控制，用户点击停止后页面会立即停止接收和渲染；前端中断不等于后端任务一定停止，完整的中断机制应该是前端停止接收、后端停止流式生成、模型调用停止推理、数据库按中断状态落库，这样才是比较完整的工程实现。

如果用户点击中断，后端大模型的输出没有中断，这个怎么样
前端点击中断后，会通过 AbortController 把浏览器这边的请求断掉
这样前端页面不会再继续接收内容，也不会再往消息区追加
但如果后端没有继续把这个“取消信号”传给模型调用层，那后端那次大模型生成任务可能还会在服务器里继续跑完

前端中断请求只能保证浏览器不再接收响应，但不一定能保证后端模型立即停止。要真正实现完整中断，后端也要感知客户端断开，或者维护任务取消标记，并把取消信号继续传递给模型流式生成那一层。否则就会出现前端停了，但服务端还在继续生成的情况。”
如果面试官继续追问“那应该怎么做”，你可以答这几种常见方案：
在后端流式接口里检测客户端是否断开
例如在流式生成循环里判断连接是否还存在，断开后立即停止后续生成。

给每次生成分配 task_id
前端点击停止时，再额外发一个“取消任务”接口，后端根据 task_id 把这次生成标记为取消。

模型调用层支持取消时，继续向下传递取消信号
如果底层 SDK 或异步任务支持取消，就在后端收到中断后真正 cancel 掉生成协程。

写库时做状态控制
如果任务已中断，就不要把完整回答继续落库，或者把这条记录标记成 interrupted、partial。

## 从前端登录到后端的完整链路怎么讲
这个项目整体是前后端分离的单页应用。前端基于 Vue 3，后端基于 FastAPI。用户先在登录页输入邮箱和密码，前端会调用封装好的登录接口，把账号信息通过 POST /api/token 发给后端。后端校验用户信息和密码后，返回 access_token。前端拿到 token 后存到 localStorage，然后再请求当前用户信息和会话列表，最后跳转到聊天页。聊天页加载后，会根据当前用户去拉取会话列表、当前会话历史消息、天气信息等数据，再渲染到页面上。

把登录链路记成 6 步：
用户在前端输入账号密码  
前端调用 login()  
client.js 用 fetch 请求 /api/token  
后端验证用户，返回 access_token  
前端把 token 存进 localStorage  
前端再请求当前用户、会话列表，跳转到 /chat

## 流式响应实时前端更新，是怎么实现的
前端实时更新的核心不在于定时刷新，而在于持续读取后端流。后端每推一段，前端就解析一段，然后立刻更新响应式状态，所以消息区会看起来像是一边生成一边展示。

我这里不是固定多久轮询一次，而是后端只要生成出新的 chunk，就立刻通过 text/event-stream 往前端推一段，前端收到一段就更新一次页面，所以更新频率取决于后端返回 chunk 的节奏，不是前端定时器轮询。不是每秒固定更新，也不是前端 setInterval 去轮询，而是后端每生成一小段内容就立即往流里写一次，前端通过 ReadableStream 持续读取，所以基本是后端出一段、前端就更新一段。  

前端流式链路你可以这样讲：
“发送消息时，前端先把用户消息和一条 assistant 占位消息写进本地状态，然后调用 streamAgentChat() 请求后端的 /api/agent/chat 接口。这个接口返回的是 text/event-stream。前端拿到 response 后，不是直接 response.json()，而是通过 response.body.getReader() 持续读取字节流，再用 TextDecoder 解码。每解析出一个完整的 data: 事件，就交给 handleStreamEvent() 处理。不同类型的事件会更新不同状态，比如 thinking 更新思考面板，route 更新路由结果，sources 更新来源信息，content 追加到 assistant 回答里。”


## 后端流式响应是怎么实现的，后端怎么通知前端数据状态变化
后端不是一次性返回大 JSON，而是一个异步生成器不断 yield 数据；“前后端约定了一套简单的事件协议，不同事件有不同 type，比如 thinking、route、sources、content。前端收到以后按类型更新不同区域，所以页面能同步展示思考过程、检索结果和最终回答。”

把后端流式过程记成：
先收到前端消息  
构造上下文消息  
调用 generate_stream()  
先 yield 一些中间状态事件
例如 thinking、route、sources
再调用模型流式生成 _stream_answer()  
每拿到一个 delta.content，就包装成
{"type": "content", "content": delta}
然后继续 yield
全部结束后，再调用 on_complete 去保存消息

后端在 /api/agent/chat 这个接口里没有等模型全部生成完再一次性返回，而是把 generate_stream() 这个异步生成器交给 StreamingResponse。generate_stream() 会在不同阶段不断 yield 一段符合 SSE 格式的数据，也就是 data: ...\n\n。前端只要保持连接不断开，就能持续收到这些事件。


## 把这条聊天链路整体讲一下”，你可以直接说：
“用户在聊天页输入问题后，前端先把用户消息和 AI 占位消息写入本地状态，然后调用封装好的 streamAgentChat() 请求后端 /api/agent/chat 接口。后端接口会先构造上下文消息，再进入 generate_stream() 这条异步生成链路。这个过程中，后端会先返回路由决策、思考状态、检索来源等中间事件，再把模型生成的正文内容按 chunk 持续返回。前端通过 ReadableStream 持续读取这些流事件，按事件类型更新 thinking 面板、来源区域和最终回答内容。等整条流结束后，前端再主动刷新当前会话消息和会话列表，保证页面状态和后端持久化数据一致。


## 前端怎么知道后端状态变了”，你直接说：
“前端不是猜状态，也不是定时轮询，而是后端在流里主动发带 type 的事件。前端收到 thinking 就更新思考面板，收到 sources 就更新来源区，收到 content 就追加正文，所以状态变化是由流事件直接驱动的。”

## “请求回来后怎么更新页面状态”    

“怎么请求后端”