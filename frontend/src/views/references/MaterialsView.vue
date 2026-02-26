<template>
  <div>
    <div class="page-header">
      <h2>Материалы</h2>
      <n-button type="primary" @click="showModal = true" v-if="auth.isAdmin">+ Добавить</n-button>
    </div>
    <n-data-table :columns="columns" :data="items" :loading="loading" bordered />
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Добавить'" positive-text="Сохранить" negative-text="Отмена" @positive-click="save" style="width: 450px">
      <n-form :model="form">
        <n-form-item label="Название"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="Активен"><n-switch v-model:value="form.is_active" /></n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSwitch, NTag, useMessage } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const items = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ name: '', is_active: true })

const columns = [
  { title: '№', key: 'index', width: 60, render: (_: any, index: number) => index + 1 },
  { title: 'Название', key: 'name' },
  { title: 'Статус', key: 'is_active', width: 100, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, () => row.is_active ? 'Активен' : 'Неактивен') },
  { title: 'Действия', key: 'actions', width: 120, render: (row: any) => auth.isAdmin ? h(NButton, { size: 'small', onClick: () => { editItem.value = row; form.name = row.name; form.is_active = row.is_active; showModal.value = true } }, () => 'Ред.') : null },
]

async function load() { loading.value = true; try { items.value = (await api.get('/materials')).data } catch {} loading.value = false }
async function save() {
  try {
    if (editItem.value) { await api.put(`/materials/${editItem.value.id}`, form) } else { await api.post('/materials', form) }
    msg.success('Сохранено'); showModal.value = false; editItem.value = null; form.name = ''; form.is_active = true; await load()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
  return false
}
onMounted(load)
</script>
