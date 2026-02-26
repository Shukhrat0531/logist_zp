<template>
  <div>
    <div class="page-header">
      <h2>Карьеры</h2>
      <n-button type="primary" @click="showModal = true" v-if="auth.isAdmin">+ Добавить</n-button>
    </div>
    <n-data-table :columns="columns" :data="items" :loading="loading" bordered />
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Добавить карьер'" positive-text="Сохранить" negative-text="Отмена" @positive-click="save" @negative-click="showModal = false" style="width: 450px">
      <n-form :model="form">
        <n-form-item label="Название">
          <n-input v-model:value="form.name" placeholder="Название карьера" />
        </n-form-item>
        <n-form-item label="Цена за рейс">
          <n-input-number v-model:value="form.price_per_trip" :min="0" style="width: 100%" />
        </n-form-item>
        <n-form-item label="Активен">
          <n-switch v-model:value="form.is_active" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NInputNumber, NSwitch, NSpace, NTag, useMessage } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const items = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ name: '', price_per_trip: 0, is_active: true })

const columns = [
  { title: '№', key: 'index', width: 60, render: (_: any, index: number) => index + 1 },
  { title: 'Название', key: 'name' },
  { title: 'Цена за рейс', key: 'price_per_trip', render: (row: any) => h('span', `${Number(row.price_per_trip).toLocaleString()} ₸`) },
  { title: 'Статус', key: 'is_active', width: 100, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, () => row.is_active ? 'Активен' : 'Неактивен') },
  {
    title: 'Действия', key: 'actions', width: 120,
    render: (row: any) => auth.isAdmin ? h(NButton, { size: 'small', onClick: () => startEdit(row) }, () => 'Ред.') : null,
  },
]

async function load() {
  loading.value = true
  try { items.value = (await api.get('/carriers')).data } catch {}
  loading.value = false
}

function startEdit(row: any) {
  editItem.value = row
  form.name = row.name
  form.price_per_trip = Number(row.price_per_trip)
  form.is_active = row.is_active
  showModal.value = true
}

async function save() {
  try {
    if (editItem.value) {
      await api.put(`/carriers/${editItem.value.id}`, form)
    } else {
      await api.post('/carriers', form)
    }
    msg.success('Сохранено')
    showModal.value = false
    editItem.value = null
    form.name = ''; form.price_per_trip = 0; form.is_active = true
    await load()
  } catch (e: any) {
    msg.error(e.response?.data?.detail || 'Ошибка')
  }
  return false
}

onMounted(load)
</script>
