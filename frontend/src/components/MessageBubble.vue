<template>
  <div class="message-row" :class="messageRole">
    <div
      class="message"
      :class="[(message.sender || message.role || 'assistant'), { pending: message.pending }]"
    >
      <div class="message-actions" v-if="!message.pending">
        <button type="button" @click="$emit('copy', message)">复制</button>
        <button
          v-if="messageRole === 'assistant'"
          type="button"
          @click="$emit('regenerate', index)"
        >
          重新生成
        </button>
        <button
          v-if="messageRole === 'user'"
          type="button"
          @click="startEdit"
        >
          编辑重发
        </button>
      </div>

      <div v-if="editing" class="message-edit">
        <textarea v-model="draftContent" rows="4"></textarea>
        <div class="message-edit-actions">
          <button class="btn btn-primary" type="button" @click="submitEdit">重新发送</button>
          <button class="btn btn-ghost" type="button" @click="cancelEdit">取消</button>
        </div>
      </div>

      <div
        v-else-if="isRichText"
        class="message-markdown"
        v-html="renderedContent"
        @click="handleMarkdownClick"
      ></div>

      <template v-else-if="!editing">
        {{ message.content }}
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { renderMarkdown } from "../utils/markdown.js";

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(["copy", "regenerate", "edit-resend"]);

const editing = ref(false);
const draftContent = ref("");

const messageRole = computed(() => props.message.sender || props.message.role || "assistant");
const isRichText = computed(
  () => messageRole.value === "assistant" && !props.message.pending
);
const renderedContent = computed(() => renderMarkdown(props.message.content || ""));

function startEdit() {
  draftContent.value = props.message.content || "";
  editing.value = true;
}

function cancelEdit() {
  editing.value = false;
  draftContent.value = "";
}

function submitEdit() {
  const content = draftContent.value.trim();
  if (!content) {
    return;
  }
  emit("edit-resend", { index: props.index, content });
  editing.value = false;
}

async function handleMarkdownClick(event) {
  const button = event.target.closest?.("[data-copy-code]");
  if (!button) {
    return;
  }
  const code = button.getAttribute("data-code") || "";
  if (code) {
    await navigator.clipboard.writeText(code);
    button.textContent = "已复制";
    window.setTimeout(() => {
      button.textContent = "复制代码";
    }, 1200);
  }
}
</script>
