<template>
  <div class="modal-overlay" :class="{ visible: show }" @click.self="close">
    <div class="modal">
      <div class="modal-header">
        <div class="modal-title">{{ groupName }}</div>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <div v-if="groupAssets.length === 0" class="modal-empty">
          该分组暂无资产
        </div>
        
        <div 
          v-for="asset in groupAssets" 
          :key="asset.id" 
          class="modal-asset"
        >
          <div class="modal-asset-row">
            <div class="modal-asset-info">
              <div class="modal-asset-name">{{ asset.name }}</div>
              <div class="modal-asset-meta">
                <span class="modal-asset-code">{{ asset.code || '--' }}</span>
                <span class="modal-asset-amount">{{ formatAmount(asset.amount) }}</span>
              </div>
              <div class="modal-asset-tags">
                <span class="modal-tag">{{ asset.type }}</span>
                <span class="modal-tag">{{ asset.region }}</span>
                <span class="modal-tag">{{ asset.style }}</span>
              </div>
            </div>
            <div class="modal-asset-actions">
              <button class="btn-edit" @click="startEdit(asset)">编辑</button>
              <button 
                class="btn-delete" 
                :class="{ confirming: deletingId === asset.id }"
                @click="handleDelete(asset.id)"
              >{{ deletingId === asset.id ? '确认?' : '删除' }}</button>
            </div>
          </div>
          
          <!-- Inline Edit Form -->
          <div v-if="editingId === asset.id" class="modal-edit-form">
            <div class="edit-grid">
              <div class="form-group">
                <label>资产名</label>
                <input type="text" v-model="editForm.name">
              </div>
              <div class="form-group">
                <label>金额</label>
                <input type="number" v-model.number="editForm.amount">
              </div>
              <div class="form-group">
                <label>代码</label>
                <input type="text" v-model="editForm.code">
              </div>
              <div class="form-group">
                <label>类型</label>
                <select v-model="editForm.type">
                  <option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>区域</label>
                <select v-model="editForm.region">
                  <option v-for="r in regionOptions" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>风格</label>
                <select v-model="editForm.style">
                  <option v-for="s in styleOptions" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>
            <div style="margin-top: 8px; display: flex; gap: 8px; justify-content: flex-end;">
              <button class="btn btn-secondary btn-sm" @click="cancelEdit">取消</button>
              <button class="btn btn-primary btn-sm" @click="saveEdit(asset.id)">保存</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useConfigStore } from '@/store/configStore';
import { formatAmount } from '@/utils';
import type { Asset } from '@/types';

const props = defineProps<{
  show: boolean,
  groupName: string,
  dimensionKey: 'type' | 'region' | 'style'
}>();

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>();

const store = useConfigStore();

const groupAssets = computed(() => {
  if (!props.groupName) return [];
  // Ensure we check with a fallback to '其他' mapping logic
  return store.assets.filter(a => {
    const key = a[props.dimensionKey] || '其他';
    return key === props.groupName;
  });
});

const close = () => {
  emit('update:show', false);
  cancelEdit();
  resetDeleteState();
};

// --- Two-step delete confirmation ---
const deletingId = ref<string | null>(null);
let deletingTimer: ReturnType<typeof setTimeout> | null = null;

const resetDeleteState = () => {
  deletingId.value = null;
  if (deletingTimer !== null) {
    clearTimeout(deletingTimer);
    deletingTimer = null;
  }
};

const handleDelete = (id: string | undefined) => {
  if (!id) return;

  if (deletingId.value === id) {
    // Second click: execute delete
    resetDeleteState();
    store.removeAsset(id);
    if (groupAssets.value.length === 0) {
      close();
    }
  } else {
    // First click: enter confirming state, auto-cancel after 3s
    resetDeleteState();
    deletingId.value = id;
    deletingTimer = setTimeout(() => {
      deletingId.value = null;
      deletingTimer = null;
    }, 3000);
  }
};

// Editing State
const editingId = ref<string | null>(null);
const editForm = ref<Partial<Asset>>({});

const typeOptions = ['股票', '大宗商品', '债券', '货币基金', '现金', '其他'];
const regionOptions = ['中国大陆', '中国香港', '美国', '欧洲', '印度', '全球', '无'];
const styleOptions = ['大盘价值', '大盘成长', '中小盘', '商品对冲', '防御型', '新兴市场', '无'];

const startEdit = (asset: Asset) => {
  editingId.value = asset.id!;
  editForm.value = { ...asset };
};

const cancelEdit = () => {
  editingId.value = null;
  editForm.value = {};
};

const saveEdit = (id: string | undefined) => {
  if (!id) return;
  store.updateAsset(id, { ...editForm.value } as Asset);
  
  // If we changed the dimension we're currently grouped by, this asset might disappear from the modal
  const newDimValue = (editForm.value as any)[props.dimensionKey] || '其他';
  if (newDimValue !== props.groupName) {
     if (groupAssets.value.length === 1) { // It was the last one
       close();
     }
  }
  
  cancelEdit();
};

// Reset edit and delete state when modal closes
watch(() => props.show, (newVal) => {
  if (!newVal) {
    cancelEdit();
    resetDeleteState();
  }
});
</script>

<style scoped>
/* Inherits modal styles from global style.css */
.btn-sm {
  padding: 4px 10px;
  font-size: 11px;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary:hover {
  border-color: var(--border-glow);
}
</style>
