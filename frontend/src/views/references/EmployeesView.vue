<template>
  <div>
    <div class="page-header">
      <h2>Сотрудники</h2>
      <n-button type="primary" @click="openCreate" v-if="auth.isAdmin">+ Добавить</n-button>
    </div>
    <n-data-table :columns="columns" :data="items" :loading="loading" bordered />
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Добавить'" positive-text="Сохранить" negative-text="Отмена" @positive-click="save" style="width: 450px">
      <n-form :model="form">
        <n-form-item label="ФИО"><n-input v-model:value="form.full_name" /></n-form-item>
        <n-form-item label="Тип">
          <n-select v-model:value="form.employee_type" :options="typeOptions" />
        </n-form-item>
        <n-form-item label="Активен"><n-switch v-model:value="form.is_active" /></n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSwitch, NTag, NSelect, useMessage } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const items = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ full_name: '', employee_type: 'driver', is_active: true })
const typeOptions = [
  { label: 'Водитель', value: 'driver' },
  { label: 'Оператор', value: 'operator' },
]

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: 'ФИО', key: 'full_name' },
  { title: 'Тип', key: 'employee_type', width: 120, render: (row: any) => h(NTag, { type: row.employee_type === 'driver' ? 'info' : 'warning', size: 'small' }, () => row.employee_type === 'driver' ? 'Водитель' : 'Оператор') },
  { title: 'Статус', key: 'is_active', width: 100, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, () => row.is_active ? 'Активен' : 'Неактивен') },
  { title: 'Действия', key: 'actions', width: 120, render: (row: any) => auth.isAdmin ? h(NButton, { size: 'small', onClick: () => startEdit(row) }, () => 'Ред.') : null },
]

function openCreate() { editItem.value = null; form.full_name = ''; form.employee_type = 'driver'; form.is_active = true; showModal.value = true }
function startEdit(row: any) { editItem.value = row; form.full_name = row.full_name; form.employee_type = row.employee_type; form.is_active = row.is_active; showModal.value = true }

async function load() { loading.value = true; try { items.value = (await api.get('/employees')).data } catch {} loading.value = false }
async function save() {
  try {
    if (editItem.value) { await api.put(`/employees/${editItem.value.id}`, form) } else { await api.post('/employees', form) }
    msg.success('Сохранено'); showModal.value = false; await load()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
  return false
}
onMounted(load)
</script>
