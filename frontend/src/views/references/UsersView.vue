<template>
  <div>
    <div class="page-header">
      <h2>Пользователи</h2>
      <n-button type="primary" @click="openCreate">+ Добавить</n-button>
    </div>
    <n-data-table :columns="columns" :data="items" :loading="loading" bordered />
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Создать'" positive-text="Сохранить" negative-text="Отмена" @positive-click="save" style="width: 450px">
      <n-form :model="form">
        <n-form-item label="Логин"><n-input v-model:value="form.username" :disabled="!!editItem" /></n-form-item>
        <n-form-item label="Пароль"><n-input v-model:value="form.password" type="password" :placeholder="editItem ? 'Оставить пустым' : 'Пароль'" /></n-form-item>
        <n-form-item label="Полное имя"><n-input v-model:value="form.full_name" /></n-form-item>
        <n-form-item label="Роль">
          <n-select v-model:value="form.role" :options="roleOptions" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSelect, NTag, useMessage } from 'naive-ui'
import api from '../../api/client'

const msg = useMessage()
const items = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ username: '', password: '', full_name: '', role: 'dispatcher' })
const roleOptions = [
  { label: 'Администратор', value: 'admin' },
  { label: 'Диспетчер', value: 'dispatcher' },
  { label: 'Бухгалтер', value: 'accountant' },
]

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: 'Логин', key: 'username' },
  { title: 'Имя', key: 'full_name' },
  { title: 'Роль', key: 'role', width: 130, render: (row: any) => h(NTag, { type: row.role === 'admin' ? 'error' : row.role === 'dispatcher' ? 'info' : 'success', size: 'small' }, () => row.role) },
  { title: 'Действия', key: 'actions', width: 120, render: (row: any) => h(NButton, { size: 'small', onClick: () => startEdit(row) }, () => 'Ред.') },
]

function openCreate() { editItem.value = null; form.username = ''; form.password = ''; form.full_name = ''; form.role = 'dispatcher'; showModal.value = true }
function startEdit(row: any) { editItem.value = row; form.username = row.username; form.password = ''; form.full_name = row.full_name; form.role = row.role; showModal.value = true }

async function load() { loading.value = true; try { items.value = (await api.get('/users')).data } catch {} loading.value = false }
async function save() {
  try {
    const payload: any = { full_name: form.full_name, role: form.role }
    if (form.password) payload.password = form.password
    if (editItem.value) { await api.put(`/users/${editItem.value.id}`, payload) } else { await api.post('/users', { ...form }) }
    msg.success('Сохранено'); showModal.value = false; await load()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
  return false
}
onMounted(load)
</script>
