<template>
  <div>
    <div class="page-header">
      <h2>Спецтехника (Machinery)</h2>
      <n-button type="primary" @click="openCreate" v-if="auth.isAdmin">+ Добавить</n-button>
    </div>
    <n-data-table :columns="columns" :data="items" :loading="loading" bordered />

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Добавить'" style="width: 450px">
      <n-form :model="form" label-placement="left" label-width="120">
        <n-form-item label="Название"><n-input v-model:value="form.name" placeholder="Например, JCB 3CX" /></n-form-item>
        <n-form-item label="Активен"><n-switch v-model:value="form.is_active" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">Отмена</n-button>
        <n-button type="primary" @click="save" :loading="saving">Сохранить</n-button>
      </template>
    </n-modal>

    <!-- Tariffs Modal -->
    <n-modal v-model:show="showTariffModal" preset="card" title="Тарифы" style="width: 600px">
        <div style="margin-bottom: 16px; font-weight: bold;">
            Техника: {{ currentMachine?.name }}
        </div>
        
        <n-space vertical>
            <n-input-group>
                <n-input v-model:value="newTariff.name" placeholder="Название тарифа (напр. Стандарт)" />
                <n-input-number v-model:value="newTariff.rate" placeholder="Ставка" :show-button="false" />
                <n-button type="primary" @click="addTariff" :disabled="!newTariff.name || !newTariff.rate">Добавить</n-button>
            </n-input-group>

            <n-data-table :columns="tariffColumns" :data="tariffList" :loading="loadingTariffs" size="small" />
        </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSwitch, NTag, useMessage, NSpace, NInputGroup, NInputNumber } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const items = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)

// Main Machinery CRUD
const showModal = ref(false)
const editItem = ref<any>(null)
const form = reactive({ name: '', is_active: true })

// Tariffs
const showTariffModal = ref(false)
const currentMachine = ref<any>(null)
const tariffList = ref<any[]>([])
const loadingTariffs = ref(false)
const newTariff = reactive({ name: '', rate: 0 })

const columns = [
  { title: '№', key: 'index', width: 60, render: (_: any, index: number) => index + 1 },
  { title: 'Название', key: 'name' },
  { title: 'Статус', key: 'is_active', width: 100, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, () => row.is_active ? 'Активен' : 'Неактивен') },
  { 
    title: 'Действия', key: 'actions', width: 200, 
    render: (row: any) => {
        const buttons = []
        if (auth.isAdmin) {
             buttons.push(h(NButton, { size: 'tiny', type: 'info', style: 'margin-right: 6px', onClick: () => openTariffs(row) }, () => 'Тарифы'))
             buttons.push(h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, () => 'Ред.'))
        }
        return buttons
    } 
  },
]

const tariffColumns = [
    { title: 'Название', key: 'name' },
    { title: 'Ставка', key: 'rate' },
    { 
        title: '', key: 'actions', width: 60,
        render: (row: any) => h(NButton, { size: 'tiny', type: 'error', onClick: () => deleteTariff(row.id) }, () => 'X')
    }
]

async function load() { 
    loading.value = true; 
    try { 
        // Use new endpoint
        items.value = (await api.get('/machinery')).data 
    } catch {} 
    loading.value = false 
}

function openCreate() {
    editItem.value = null
    form.name = ''; form.is_active = true
    showModal.value = true
}

function openEdit(row: any) {
    editItem.value = row
    form.name = row.name; form.is_active = row.is_active
    showModal.value = true
}

async function save() {
  saving.value = true
  try {
    if (editItem.value) { 
        await api.put(`/machinery/${editItem.value.id}`, form) 
    } else { 
        await api.post('/machinery', form) 
    }
    msg.success('Сохранено')
    showModal.value = false
    await load()
  } catch (e: any) { 
      msg.error(e.response?.data?.detail || 'Ошибка') 
  }
  saving.value = false
}

// Tariff Logic
async function openTariffs(row: any) {
    currentMachine.value = row
    showTariffModal.value = true
    await loadTariffs()
}

async function loadTariffs() {
    if (!currentMachine.value) return
    loadingTariffs.value = true
    try {
        const res = await api.get(`/machinery/${currentMachine.value.id}/tariffs`)
        tariffList.value = res.data
    } catch {}
    loadingTariffs.value = false
}

async function addTariff() {
    if (!currentMachine.value) return
    try {
        await api.post('/machinery-tariffs', {
            machinery_id: currentMachine.value.id,
            name: newTariff.name,
            rate: newTariff.rate,
            is_active: true
        })
        msg.success('Тариф добавлен')
        newTariff.name = ''; newTariff.rate = 0
        await loadTariffs()
    } catch (e: any) {
        msg.error(e.response?.data?.detail || 'Ошибка')
    }
}

async function deleteTariff(id: number) {
    try {
        await api.delete(`/machinery-tariffs/${id}`)
        msg.success('Тариф удален')
        await loadTariffs()
    } catch (e: any) {
        msg.error(e.response?.data?.detail || 'Ошибка')
    }
}

onMounted(load)
</script>
