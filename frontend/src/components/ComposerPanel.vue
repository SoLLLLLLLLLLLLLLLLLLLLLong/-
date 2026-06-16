<template>
  <div class="composer-wrap">
    <div class="status-strip">
      <span class="status-pill">记忆：最近消息 + summary 长期记忆</span>
      <span class="status-pill">上传 PDF / DOCX / TXT 后可直接围绕文档提问</span>
    </div>

    <div v-if="currentAttachment" class="attachment-banner">
      <span class="attachment-banner-label">当前已关联文档</span>
      <span class="attachment-banner-name" :title="currentAttachment.filename">
        {{ currentAttachment.filename }}
      </span>
      <button
        class="attachment-banner-remove"
        type="button"
        aria-label="移除当前文档"
        @click="$emit('remove-attachment')"
      >
        ×
      </button>
    </div>

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
const props = defineProps({
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
  event.target.value = "";
}
</script>
