<template>
  <div>
    <div class="page-header">
      <h2>Закупщики / Объекты</h2>
      <n-button type="primary" @click="openCreate" v-if="auth.isAdmin">+ Добавить</n-button>
    </div>
    <n-data-table :columns="columns" :data="items" :loading="loading" bordered />

    <!-- Create/Edit Buyer Modal -->
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Добавить'" style="width: 550px">
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="Название"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="Активен"><n-switch v-model:value="form.is_active" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">Отмена</n-button>
        <n-button type="primary" @click="save">Сохранить</n-button>
      </template>
    </n-modal>

    <!-- Places Modal -->
    <n-modal v-model:show="showPlacesModal" preset="dialog" :title="`Места — ${currentBuyer?.name || ''}`" style="width: 600px">
      <n-data-table :columns="placeColumns" :data="places" bordered size="small" style="margin-bottom: 16px" />
      <n-space>
        <n-input v-model:value="newPlaceName" placeholder="Название места" style="width: 300px" />
        <n-button type="primary" @click="addPlace" :disabled="!newPlaceName">+ Добавить место</n-button>
      </n-space>
      <template #action>
        <n-button @click="showPlacesModal = false">Закрыть</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSwitch, NTag, NSpace, useMessage } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const items = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ name: '', is_active: true })

// Places
const showPlacesModal = ref(false)
const currentBuyer = ref<any>(null)
const places = ref<any[]>([])
const newPlaceName = ref('')

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: 'Название', key: 'name' },
  { title: 'Статус', key: 'is_active', width: 100, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, () => row.is_active ? 'Активен' : 'Неактивен') },
  { title: 'Действия', key: 'actions', width: 200, render: (row: any) => {
      if (!auth.isAdmin) return null
      return h(NSpace, { size: 4 }, () => [
        h(NButton, { size: 'small', onClick: () => { editItem.value = row; form.name = row.name; form.is_active = row.is_active; showModal.value = true } }, () => 'Ред.'),
        h(NButton, { size: 'small', type: 'info', onClick: () => openPlaces(row) }, () => 'Места'),
      ])
    }
  },
]

const placeColumns = [
  { title: 'ID', key: 'id', width: 50 },
  { title: 'Название', key: 'name' },
  { title: '', key: 'actions', width: 60, render: (row: any) => h(NButton, { size: 'tiny', type: 'error', onClick: () => deletePlace(row.id) }, () => '✗') },
]

function openCreate() {
  editItem.value = null
  form.name = ''
  form.is_active = true
  showModal.value = true
}

async function load() { loading.value = true; try { items.value = (await api.get('/buyers')).data } catch {} loading.value = false }

async function save() {
  try {
    if (editItem.value) { await api.put(`/buyers/${editItem.value.id}`, form) } else { await api.post('/buyers', form) }
    msg.success('Сохранено'); showModal.value = false; editItem.value = null; form.name = ''; form.is_active = true; await load()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
}

async function openPlaces(buyer: any) {
  currentBuyer.value = buyer
  showPlacesModal.value = true
  newPlaceName.value = ''
  await loadPlaces()
}

async function loadPlaces() {
  try {
    places.value = (await api.get('/object-places', { params: { buyer_id: currentBuyer.value.id } })).data
  } catch {}
}

async function addPlace() {
  if (!newPlaceName.value || !currentBuyer.value) return
  try {
    await api.post('/object-places', { buyer_id: currentBuyer.value.id, name: newPlaceName.value, is_active: true })
    msg.success('Место добавлено')
    newPlaceName.value = ''
    await loadPlaces()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
}

async function deletePlace(id: number) {
  try {
    await api.delete(`/object-places/${id}`)
    msg.success('Удалено')
    await loadPlaces()
  } catch { msg.error('Ошибка') }
}

onMounted(load)
</script>
