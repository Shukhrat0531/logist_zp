<template>
  <div>
    <div class="page-header">
      <h2>Смены спецтехники</h2>
      <n-button type="primary" @click="openCreate">+ Открыть смену</n-button>
    </div>

    <!-- Open sessions highlight -->
    <n-card v-if="openSessions.length > 0" size="small" style="margin-bottom: 16px; border-left: 4px solid #f2994a">
      <n-space vertical>
        <strong style="color: #f2994a">Открытые смены ({{ openSessions.length }})</strong>
        <div v-for="s in openSessions" :key="s.id" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0">
          <span>{{ s.operator_name }} — {{ s.machinery_name }} ({{ s.start_at?.slice(0,16) }}) [Тариф: {{ s.hourly_rate }}]</span>
          <n-button size="small" type="warning" @click="openClose(s)">Закрыть смену</n-button>
        </div>
      </n-space>
    </n-card>

    <!-- Filters -->
    <n-card size="small" style="margin-bottom: 16px">
      <n-space>
        <n-date-picker v-model:value="filters.dateRange" type="daterange" clearable size="small" />
        <n-select v-model:value="filters.operator_id" :options="operatorOptions" placeholder="Оператор" clearable size="small" style="width: 180px" />
        <n-select v-model:value="filters.status" :options="statusOptions" placeholder="Статус" clearable size="small" style="width: 140px" />
        <n-button size="small" @click="loadSessions">Применить</n-button>
      </n-space>
    </n-card>

    <n-data-table :columns="columns" :data="sessions" :loading="loading" bordered />

    <!-- Create modal -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="Открыть смену" style="width: 500px">
      <n-form :model="createForm" label-placement="left" label-width="120">
        <n-form-item label="Оператор">
          <n-select v-model:value="createForm.operator_id" :options="operatorOptions" filterable />
        </n-form-item>
        <n-form-item label="Спецтехника">
          <n-select v-model:value="createForm.machinery_id" :options="machineryOptions" filterable />
        </n-form-item>
        <n-form-item label="Объект">
          <n-select v-model:value="createForm.buyer_id" :options="buyerOptions" clearable filterable />
        </n-form-item>
        
        <!-- Tariff Select -->
        <n-form-item label="Тариф" v-if="tariffOptions.length > 0">
            <n-select v-model:value="createForm.tariff_id" :options="tariffOptions" placeholder="Выберите тариф" clearable />
        </n-form-item>

        <!-- Hourly Rate Input -->
        <n-form-item label="Тариф (час)">
            <n-input-number v-model:value="createForm.hourly_rate" :step="100" style="width: 100%" placeholder="По умолчанию из настроек" />
        </n-form-item>

        <n-form-item label="Начало">
          <n-date-picker v-model:value="createForm.start_at" type="datetime" style="width: 100%" />
        </n-form-item>
        <n-form-item label="Примечание">
          <n-input v-model:value="createForm.notes" type="textarea" :rows="2" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">Отмена</n-button>
        <n-button type="primary" @click="createSession" :loading="saving">Открыть</n-button>
      </template>
    </n-modal>

    <!-- Close modal -->
    <n-modal v-model:show="showCloseModal" preset="dialog" title="Закрыть смену" style="width: 400px">
      <n-form label-placement="left" label-width="120">
        <n-form-item label="Конец">
          <n-date-picker v-model:value="closeEndAt" type="datetime" style="width: 100%" />
        </n-form-item>
        <n-form-item label="Солярка (л)">
          <n-input-number v-model:value="closeFuelLiters" :min="0" :precision="1" placeholder="Необязательно" style="width: 100%" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCloseModal = false">Отмена</n-button>
        <n-button type="warning" @click="closeSession" :loading="saving">Закрыть смену</n-button>
      </template>
    </n-modal>

    <!-- Edit modal -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="Редактировать смену" style="width: 500px">
      <n-form :model="editForm" label-placement="left" label-width="120">
        <n-form-item label="Оператор">
          <n-select v-model:value="editForm.operator_id" :options="operatorOptions" filterable />
        </n-form-item>
        <n-form-item label="Спецтехника">
          <n-select v-model:value="editForm.machinery_id" :options="machineryOptions" filterable />
        </n-form-item>
        <n-form-item label="Объект">
          <n-select v-model:value="editForm.buyer_id" :options="buyerOptions" clearable filterable />
        </n-form-item>
        <n-form-item label="Тариф (час)">
          <n-input-number v-model:value="editForm.hourly_rate" :min="0" style="width: 100%" />
        </n-form-item>
        <n-form-item label="Примечание">
          <n-input v-model:value="editForm.notes" type="textarea" :rows="2" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showEditModal = false">Отмена</n-button>
        <n-button type="primary" @click="saveEditSession" :loading="saving">Сохранить</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive, watch } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSelect, NDatePicker, NCard, NSpace, NTag, useMessage, useDialog, NInputNumber } from 'naive-ui'
import api from '../api/client'

const msg = useMessage()
const dialog = useDialog()
const sessions = ref<any[]>([])
const openSessions = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showCreateModal = ref(false)
const showCloseModal = ref(false)
const closingSession = ref<any>(null)
const closeEndAt = ref(Date.now())
const closeFuelLiters = ref<number | null>(null)
const showEditModal = ref(false)
const editingSession = ref<any>(null)
const editForm = reactive({
  operator_id: null as number | null,
  machinery_id: null as number | null,
  buyer_id: null as number | null,
  notes: '',
  hourly_rate: 0,
})

const operatorOptions = ref<any[]>([])
const machineryOptions = ref<any[]>([])
const buyerOptions = ref<any[]>([])
const tariffOptions = ref<any[]>([]) // dynamic depending on machine

const filters = reactive({ dateRange: null as any, operator_id: null as number | null, status: null as string | null })
const statusOptions = [
  { label: 'Открыта', value: 'open' },
  { label: 'Закрыта', value: 'closed' },
  { label: 'Заблокирована', value: 'locked' },
]

const createForm = reactive({
  operator_id: null as number | null,
  machinery_id: null as number | null,
  buyer_id: null as number | null,
  tariff_id: null as number | null,
  hourly_rate: 0,
  start_at: Date.now(),
  notes: '',
})

function statusTag(status: string) {
  const map: Record<string, 'warning' | 'success' | 'error' | 'default'> = { open: 'warning', closed: 'success', locked: 'error' }
  const labels: Record<string, string> = { open: 'Открыта', closed: 'Закрыта', locked: 'Заблокирована' }
  return h(NTag, { type: map[status] || 'default', size: 'small' }, () => labels[status] || status)
}

const columns = [
  { title: '№', key: 'index', width: 50, render: (_: any, index: number) => index + 1 },
  { title: 'Дата', key: 'work_date', width: 100 },
  { title: 'Оператор', key: 'operator_name' },
  { title: 'Спецтехника', key: 'machinery_name' },
  { title: 'Объект', key: 'buyer_name' },
  { title: 'Тариф', key: 'hourly_rate', width: 80 },
  { title: 'Начало', key: 'start_at', width: 140, render: (r: any) => r.start_at?.slice(0, 16) },
  { title: 'Конец', key: 'end_at', width: 140, render: (r: any) => r.end_at?.slice(0, 16) || '—' },
  { title: 'Часы', key: 'pay_hours', width: 80, render: (r: any) => r.pay_hours ? r.pay_hours.toFixed(1) : '—' },
  { title: 'Статус', key: 'status', width: 120, render: (r: any) => statusTag(r.status) },
  {
    title: 'Действия', key: 'actions', width: 180,
    render: (row: any) => {
      const btns: any[] = []
      if (row.status === 'open') {
        btns.push(h(NButton, { size: 'tiny', type: 'warning', onClick: () => openClose(row) }, () => 'Закрыть'))
      }
      if (row.status !== 'locked') {
        btns.push(h(NButton, { size: 'tiny', onClick: () => startEditSession(row) }, () => '✎'))
        btns.push(h(NButton, { size: 'tiny', type: 'error', onClick: () => deleteSession(row.id) }, () => '🗑'))
      }
      return h(NSpace, { size: 4 }, () => btns)
    },
  },
]

function openCreate() {
  createForm.operator_id = null; createForm.machinery_id = null
  createForm.buyer_id = null; createForm.start_at = Date.now(); createForm.notes = ''
  createForm.hourly_rate = 0; createForm.tariff_id = null
  tariffOptions.value = []
  showCreateModal.value = true
}

function openClose(session: any) {
  closingSession.value = session
  closeEndAt.value = Date.now()
  closeFuelLiters.value = null
  showCloseModal.value = true
}

async function loadRefs() {
  const [ops, macs, buys] = await Promise.all([
    api.get('/employees?employee_type=operator'),
    api.get('/machinery'),
    api.get('/buyers'),
  ])
  operatorOptions.value = ops.data.map((o: any) => ({ label: o.full_name, value: o.id }))
  machineryOptions.value = macs.data.map((e: any) => ({ label: e.name, value: e.id }))
  buyerOptions.value = buys.data.map((b: any) => ({ label: b.name, value: b.id }))
}

async function loadSessions() {
  loading.value = true
  try {
    const params: any = { page: 1, size: 200 }
    if (filters.dateRange) {
      params.date_from = new Date(filters.dateRange[0]).toISOString().split('T')[0]
      params.date_to = new Date(filters.dateRange[1]).toISOString().split('T')[0]
    }
    if (filters.operator_id) params.operator_id = filters.operator_id
    if (filters.status) params.status = filters.status
    const res = await api.get('/machinery-sessions', { params })
    sessions.value = res.data.items
  } catch {}
  loading.value = false
}

async function loadOpen() {
  try {
    const res = await api.get('/machinery-sessions/open')
    openSessions.value = res.data.items
  } catch {}
}

async function createSession() {
  saving.value = true
  try {
    await api.post('/machinery-sessions', {
      operator_id: createForm.operator_id,
      machinery_id: createForm.machinery_id,
      buyer_id: createForm.buyer_id,
      hourly_rate: createForm.hourly_rate || null, 
      start_at: new Date(createForm.start_at).toISOString(),
      notes: createForm.notes || null,
    })
    msg.success('Смена открыта')
    showCreateModal.value = false
    await loadSessions()
    await loadOpen()
  } catch (e: any) {
    msg.error(e.response?.data?.detail || 'Ошибка')
  }
  saving.value = false
}

async function closeSession() {
  saving.value = true
  try {
    await api.post(`/machinery-sessions/${closingSession.value.id}/close`, {
      end_at: new Date(closeEndAt.value).toISOString(),
      fuel_liters: closeFuelLiters.value || null,
    })
    msg.success('Смена закрыта')
    showCloseModal.value = false
    await loadSessions()
    await loadOpen()
  } catch (e: any) {
    msg.error(e.response?.data?.detail || 'Ошибка')
  }
  saving.value = false
}

async function startEditSession(row: any) {
  editingSession.value = row
  editForm.operator_id = row.operator_id
  editForm.machinery_id = row.machinery_id
  editForm.buyer_id = row.buyer_id
  editForm.notes = row.notes || ''
  editForm.hourly_rate = row.hourly_rate || 0
  showEditModal.value = true
}

async function saveEditSession() {
  saving.value = true
  try {
    await api.put(`/machinery-sessions/${editingSession.value.id}`, {
      operator_id: editForm.operator_id,
      machinery_id: editForm.machinery_id,
      buyer_id: editForm.buyer_id,
      notes: editForm.notes || null,
      hourly_rate: editForm.hourly_rate,
    })
    msg.success('Сохранено')
    showEditModal.value = false
    await loadSessions()
    await loadOpen()
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
  saving.value = false
}

async function deleteSession(id: number) {
  dialog.error({
    title: 'Удалить смену?',
    content: 'Смена будет полностью удалена. Это действие нельзя отменить.',
    positiveText: 'Удалить',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try { await api.delete(`/machinery-sessions/${id}`); msg.success('Удалено'); await loadSessions(); await loadOpen() }
      catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
    },
  })
}

// Watchers
watch(() => createForm.machinery_id, async (newVal) => {
    tariffOptions.value = []
    createForm.tariff_id = null
    createForm.hourly_rate = 0 
    
    if (newVal) {
        try {
            const res = await api.get(`/machinery/${newVal}/tariffs`)
            tariffOptions.value = res.data.map((t: any) => ({ label: `${t.name} (${t.rate})`, value: t.id, rate: t.rate }))
        } catch {}
    }
})

watch(() => createForm.tariff_id, (newVal) => {
    if (newVal) {
        const t: any = tariffOptions.value.find((opt: any) => opt.value === newVal)
        if (t) {
            createForm.hourly_rate = t.rate
        }
    }
})

onMounted(async () => { await loadRefs(); await loadSessions(); await loadOpen() })
</script>
