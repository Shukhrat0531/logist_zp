<template>
  <div>
    <div class="page-header">
      <h2>Настройки системы</h2>
      <n-button type="primary" @click="openAdd">+ Добавить параметр</n-button>
    </div>
    <n-card size="small">
      <n-data-table :columns="columns" :data="settings" bordered />
    </n-card>

    <!-- Edit Modal -->
    <n-modal v-model:show="showModal" preset="dialog" title="Редактировать" style="width: 400px">
      <n-form :model="form">
        <n-form-item :label="keyLabels[editItem?.key] || editItem?.key || 'Значение'">
          <n-input v-model:value="form.value" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">Отмена</n-button>
        <n-button type="primary" @click="save">Сохранить</n-button>
      </template>
    </n-modal>

    <!-- Add Modal -->
    <n-modal v-model:show="showAddModal" preset="dialog" title="Добавить параметр" style="width: 450px">
      <n-form :model="addForm" label-placement="left" label-width="100">
        <n-form-item label="Параметр">
          <n-select v-model:value="addForm.key" :options="availableKeys" placeholder="Выберите" />
        </n-form-item>
        <n-form-item label="Значение">
          <n-input v-model:value="addForm.value" placeholder="Значение" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showAddModal = false">Отмена</n-button>
        <n-button type="primary" @click="addSetting" :disabled="!addForm.key || !addForm.value">Добавить</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive, computed } from 'vue'
import { NDataTable, NButton, NCard, NModal, NForm, NFormItem, NInput, NSelect, useMessage } from 'naive-ui'
import api from '../api/client'

const msg = useMessage()
const settings = ref<any[]>([])
const showModal = ref(false)
const showAddModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ value: '' })
const addForm = reactive({ key: '', value: '' })

const keyLabels: Record<string, string> = {
  fuel_price_per_liter: 'Цена за литр солярки (₸)',
}

const allKeys = [
  { label: 'Цена за литр солярки (₸)', value: 'fuel_price_per_liter' },
]

const availableKeys = computed(() => {
  const existingKeys = settings.value.map(s => s.key)
  return allKeys.filter(k => !existingKeys.includes(k.value))
})

const columns = [
  { title: 'Параметр', key: 'key', render: (r: any) => keyLabels[r.key] || r.key },
  { title: 'Значение', key: 'value' },
  {
    title: 'Действия', key: 'actions', width: 120,
    render: (row: any) => h(NButton, { size: 'small', onClick: () => { editItem.value = row; form.value = row.value; showModal.value = true } }, () => 'Ред.'),
  },
]

async function load() { try { settings.value = (await api.get('/settings')).data } catch {} }

async function save() {
  try {
    await api.put(`/settings/${editItem.value.id}`, { value: form.value })
    msg.success('Сохранено'); showModal.value = false; await load()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
}

function openAdd() {
  addForm.key = ''
  addForm.value = ''
  showAddModal.value = true
}

async function addSetting() {
  try {
    await api.post('/settings', { key: addForm.key, value: addForm.value })
    msg.success('Параметр добавлен'); showAddModal.value = false; await load()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
}

onMounted(load)
</script>
