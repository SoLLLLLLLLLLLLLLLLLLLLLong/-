<template>
  <div class="history-item" :class="{ active }" @click="handleSelect">
    <div v-if="editing" class="history-item-editor" @click.stop>
      <input
        ref="editorRef"
        v-model.trim="draftTitle"
        class="history-item-input"
        maxlength="40"
        @keydown.enter.prevent="submitRename"
        @keydown.esc.prevent="cancelEdit"
      />
      <div class="history-item-actions">
        <button class="btn btn-primary" type="button" @click="submitRename">保存</button>
        <button class="btn btn-ghost" type="button" @click="cancelEdit">取消</button>
      </div>
    </div>

    <template v-else>
      <div class="history-item-title">{{ item.title || "未命名会话" }}</div>
      <div class="history-item-meta">{{ formatDate(item.updated_at || item.created_at) }}</div>
      <div class="history-item-actions">
        <button class="btn btn-ghost" type="button" @click.stop="startEdit">重命名</button>
        <button class="btn btn-danger" type="button" @click.stop="$emit('delete', item.id)">
          删除
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { nextTick, ref } from "vue";

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
  formatDate: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(["select", "rename", "delete"]);

const editing = ref(false);
const draftTitle = ref("");
const editorRef = ref(null);

function handleSelect() {
  if (!editing.value) {
    emit("select", props.item.id);
  }
}

async function startEdit() {
  editing.value = true;
  draftTitle.value = props.item.title || "";
  await nextTick();
  editorRef.value?.focus();
  editorRef.value?.select();
}

function cancelEdit() {
  editing.value = false;
  draftTitle.value = "";
}

function submitRename() {
  const nextName = draftTitle.value.trim();
  if (!nextName) {
    return;
  }
  emit("rename", { id: props.item.id, name: nextName });
  editing.value = false;
}
</script>
