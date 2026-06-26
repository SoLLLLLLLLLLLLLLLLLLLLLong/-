<template>
  <div class="composer-wrap">
    <!-- 这两条状态说明只是给用户看的提示，不参与真实业务逻辑。 -->
    <!-- <div class="status-strip">
      <span class="status-pill">记忆：最近消息 + 长期偏好记忆</span>
      <span class="status-pill">上传 PDF / DOCX / TXT 后可直接围绕文档提问</span>
    </div> -->

    <!-- 当前会话如果已经绑定附件，就在输入区上方显示。 -->
    <div v-if="currentAttachment" class="attachment-banner">
      <span class="attachment-banner-label">当前已关联附件</span>
      <span class="attachment-banner-name" :title="currentAttachment.filename">
        {{ currentAttachment.filename }}
      </span>
      <button
        class="attachment-banner-remove"
        type="button"
        aria-label="移除当前附件"
        @click="$emit('remove-attachment')"
      >
        ×
      </button>
    </div>

    <!-- 表单提交不会刷新页面，而是交给上层触发发送逻辑。 -->
    <form class="composer" @submit.prevent="$emit('send')">
      <textarea
        id="composer-input"
        :value="composerInput"
        placeholder="直接提问即可，例如：帮我总结这份 PDF 的重点，或者帮我查询今天的 AI 新闻。"
        required
        @input="$emit('update:composerInput', $event.target.value)"
        @keydown="$emit('keydown', $event)"
      ></textarea>

      <div class="composer-actions">
        <div class="composer-left">
          <!-- 原生 file input 负责真正选择文件，label 只是更好看的触发按钮。 -->
          <label class="btn btn-ghost" for="upload-input">上传文档</label>
          <input
            id="upload-input"
            type="file"
            accept=".pdf,.docx,.txt,.md"
            class="hidden"
            @change="handleFileChange"
          />
        </div>

        <div class="composer-right">
          <!-- 正在生成时，发送按钮会切换成“停止生成”。 -->
          <button
            v-if="isLoading"
            class="btn btn-danger"
            type="button"
            @click="$emit('stop')"
          >
            停止生成
          </button>
          <button v-else class="btn btn-primary" type="submit">发送</button>
        </div>
      </div>

      <p v-if="composerError" class="error-text">{{ composerError }}</p>
    </form>
  </div>
</template>

<script setup>
// 这个组件是“输入区组件”，只负责输入和局部交互。
// 真正的消息发送、文件上传、停止生成逻辑都在上层 store 里。
defineProps({
  composerInput: {
    type: String,
    default: "",
  },
  currentAttachment: {
    type: Object,
    default: null,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  composerError: {
    type: String,
    default: "",
  },
});

// update:composerInput：把输入框内容回传给父层
// remove-attachment：移除当前会话绑定附件
// send：发送消息
// keydown：处理回车发送
// upload：上传文件
// stop：停止当前流式生成
const emit = defineEmits([
  "update:composerInput",
  "remove-attachment",
  "send",
  "keydown",
  "upload",
  "stop",
]);

function handleFileChange(event) {
  const file = event.target.files?.[0] || null;
  emit("upload", file);

  // 清空 input，后续才能重复选择同名文件。
  event.target.value = "";
}
</script>
