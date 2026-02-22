<template>
  <div>
    <div class="page-header">
      <h2>Накладные (рейсы)</h2>
      <n-button type="primary" @click="openCreate">+ Создать накладную</n-button>
    </div>

    <!-- Filters -->
    <n-card size="small" style="margin-bottom: 16px">
      <n-space>
        <n-date-picker v-model:value="filters.dateRange" type="daterange" clearable size="small" />
        <n-select v-model:value="filters.driver_id" :options="driverOptions" placeholder="Водитель" clearable size="small" style="width: 180px" />
        <n-select v-model:value="filters.carrier_id" :options="carrierOptions" placeholder="Карьер" clearable size="small" style="width: 180px" />
        <n-select v-model:value="filters.status" :options="statusOptions" placeholder="Статус" clearable size="small" style="width: 140px" />
        <n-button size="small" @click="loadInvoices">Применить</n-button>
      </n-space>
    </n-card>

    <n-data-table :columns="columns" :data="invoices" :loading="loading" bordered :pagination="pagination" />

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="dialog" :title="editItem ? 'Редактировать' : 'Новая накладная'" style="width: 700px">
      <n-form :model="form" label-placement="left" label-width="140">
        <n-form-item label="Дата рейса">
          <n-date-picker v-model:value="form.trip_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="Водитель">
          <n-select v-model:value="form.driver_id" :options="driverOptions" filterable placeholder="Выберите водителя" />
        </n-form-item>
        <n-form-item label="Машина">
          <n-select v-model:value="form.vehicle_id" :options="vehicleOptions" filterable placeholder="Выберите машину" />
        </n-form-item>
        <n-form-item label="Карьер">
          <n-select v-model:value="form.carrier_id" :options="carrierOptions" filterable placeholder="Выберите карьер" @update:value="onCarrierChange" />
        </n-form-item>
        <n-form-item label="Цена рейса">
          <n-tag type="success" size="large">{{ selectedPrice.toLocaleString() }} ₸</n-tag>
        </n-form-item>
        <n-form-item label="Закупщик">
          <n-select v-model:value="form.buyer_id" :options="buyerOptions" filterable placeholder="Выберите закупщика" @update:value="onBuyerChange" />
        </n-form-item>
        <n-form-item label="Место выгрузки">
          <n-select v-model:value="form.place_id" :options="placeOptions" filterable placeholder="Выберите место (опционально)" :disabled="!form.buyer_id" />
        </n-form-item>
        <n-form-item label="Материал">
          <n-select v-model:value="form.material_id" :options="materialOptions" filterable placeholder="Выберите материал" />
        </n-form-item>
        
        <n-space>
            <n-form-item label="Объем (м3)" style="width: 250px">
                <n-input-number v-model:value="form.volume_m3" placeholder="м3" :step="0.1" />
            </n-form-item>
            <n-form-item label="Топливо (л)" style="width: 250px">
                <n-input-number v-model:value="form.fuel_liters" placeholder="Литры" :step="1" />
            </n-form-item>
        </n-space>

        <n-form-item label="Номер накл.">
          <n-input v-model:value="form.invoice_number" placeholder="Опционально" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">Отмена</n-button>
        <n-button type="primary" @click="save" :loading="saving">Сохранить</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive, computed } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSelect, NDatePicker, NCard, NSpace, NTag, useMessage, useDialog, NInputNumber } from 'naive-ui'
import api from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const dialog = useDialog()
const invoices = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const editItem = ref<any>(null)

// Reference data
const carriers = ref<any[]>([])
const driverOptions = ref<any[]>([])
const vehicleOptions = ref<any[]>([])
const carrierOptions = ref<any[]>([])
const buyerOptions = ref<any[]>([])
const materialOptions = ref<any[]>([])
const placeOptions = ref<any[]>([])
const selectedPrice = ref(0)

const filters = reactive({ dateRange: null as any, driver_id: null as number | null, carrier_id: null as number | null, status: null as string | null })
const statusOptions = [
  { label: 'Черновик', value: 'draft' },
  { label: 'Подтверждён', value: 'confirmed' },
  { label: 'Аннулирован', value: 'void' },
  { label: 'Заблокирован', value: 'locked' },
]

const pagination = reactive({ page: 1, pageSize: 50, showSizePicker: true, pageSizes: [20, 50, 100] })

const form = reactive({
  trip_date: Date.now(),
  driver_id: null as number | null,
  vehicle_id: null as number | null,
  carrier_id: null as number | null,
  buyer_id: null as number | null,
  material_id: null as number | null,
  place_id: null as number | null,
  fuel_liters: null as number | null,
  volume_m3: null as number | null,
  invoice_number: '',
})

function statusTag(status: string) {
  const map: Record<string, 'default' | 'success' | 'error' | 'warning' | 'info'> = { draft: 'default', confirmed: 'success', void: 'error', locked: 'warning' }
  const labels: Record<string, string> = { draft: 'Черновик', confirmed: 'Подтверждён', void: 'Аннулирован', locked: 'Заблокирован' }
  return h(NTag, { type: map[status] || 'default', size: 'small' }, () => labels[status] || status)
}

const columns = [
  { title: 'ID', key: 'id', width: 50 },
  { title: 'Дата', key: 'trip_date', width: 100 },
  { title: 'Водитель', key: 'driver_name' },
  { title: 'Машина', key: 'vehicle_plate', width: 110 },
  { title: 'Карьер', key: 'carrier_name' },
  { title: 'Закупщик', key: 'buyer_name' },
  { title: 'Место', key: 'place_name' },
  { title: 'Объем', key: 'volume_m3', width: 80, render: (r: any) => r.volume_m3 ? r.volume_m3 : '—' },
  { title: 'Цена', key: 'trip_price_fixed', width: 100, render: (r: any) => h('span', `${Number(r.trip_price_fixed).toLocaleString()}`) },
  { title: 'Статус', key: 'status', width: 120, render: (r: any) => statusTag(r.status) },
  {
    title: 'Действия', key: 'actions', width: 180,
    render: (row: any) => {
      const btns: any[] = []
      if (row.status === 'draft') {
        btns.push(h(NButton, { size: 'tiny', type: 'success', style: 'margin-right:4px', onClick: () => confirmInvoice(row.id) }, () => '✓'))
        btns.push(h(NButton, { size: 'tiny', onClick: () => startEdit(row) }, () => '✎'))
      }
      if (row.status !== 'void' && row.status !== 'locked') {
        btns.push(h(NButton, { size: 'tiny', type: 'error', style: 'margin-left:4px', onClick: () => voidInvoice(row.id) }, () => '✗'))
      }
      return h(NSpace, { size: 4 }, () => btns)
    },
  },
]

function onCarrierChange(val: number) {
  const c = carriers.value.find((x: any) => x.id === val)
  selectedPrice.value = c ? Number(c.price_per_trip) : 0
}

async function onBuyerChange(val: number | null) {
    if (!val) {
        placeOptions.value = []
        form.place_id = null
        return
    }
    // Load places for this buyer
    try {
        const res = await api.get('/object-places', { params: { buyer_id: val } })
        placeOptions.value = res.data.map((p: any) => ({ label: p.name, value: p.id }))
    } catch {
        placeOptions.value = []
    }
    form.place_id = null
}

function openCreate() {
  editItem.value = null
  form.trip_date = Date.now()
  form.driver_id = null; form.vehicle_id = null; form.carrier_id = null
  form.buyer_id = null; form.material_id = null; form.invoice_number = ''
  form.place_id = null; form.fuel_liters = null; form.volume_m3 = 20
  selectedPrice.value = 0
  placeOptions.value = []
  showModal.value = true
}

async function startEdit(row: any) {
  editItem.value = row
  form.trip_date = new Date(row.trip_date).getTime()
  form.driver_id = row.driver_id; form.vehicle_id = row.vehicle_id; form.carrier_id = row.carrier_id
  form.buyer_id = row.buyer_id; form.material_id = row.material_id; form.invoice_number = row.invoice_number || ''
  form.fuel_liters = row.fuel_liters; form.volume_m3 = row.volume_m3
  onCarrierChange(row.carrier_id)
  
  // Load places and set place_id
  await onBuyerChange(row.buyer_id)
  form.place_id = row.place_id
  
  showModal.value = true
}

async function loadRefs() {
  const [drv, veh, car, buy, mat] = await Promise.all([
    api.get('/employees?employee_type=driver'),
    api.get('/vehicles'),
    api.get('/carriers'),
    api.get('/buyers'),
    api.get('/materials'),
  ])
  driverOptions.value = drv.data.map((d: any) => ({ label: d.full_name, value: d.id }))
  vehicleOptions.value = veh.data.map((v: any) => ({ label: v.plate_number, value: v.id }))
  carriers.value = car.data
  carrierOptions.value = car.data.map((c: any) => ({ label: `${c.name} (${Number(c.price_per_trip).toLocaleString()} ₸)`, value: c.id }))
  buyerOptions.value = buy.data.map((b: any) => ({ label: b.name, value: b.id }))
  materialOptions.value = mat.data.map((m: any) => ({ label: m.name, value: m.id }))
}

async function loadInvoices() {
  loading.value = true
  try {
    const params: any = { page: 1, size: 200 }
    if (filters.dateRange) {
      params.trip_date_from = new Date(filters.dateRange[0]).toISOString().split('T')[0]
      params.trip_date_to = new Date(filters.dateRange[1]).toISOString().split('T')[0]
    }
    if (filters.driver_id) params.driver_id = filters.driver_id
    if (filters.carrier_id) params.carrier_id = filters.carrier_id
    if (filters.status) params.status = filters.status
    const res = await api.get('/trip-invoices', { params })
    invoices.value = res.data.items
  } catch {}
  loading.value = false
}

async function save() {
  saving.value = true
  try {
    const payload = {
      trip_date: new Date(form.trip_date).toISOString().split('T')[0],
      driver_id: form.driver_id,
      vehicle_id: form.vehicle_id,
      carrier_id: form.carrier_id,
      buyer_id: form.buyer_id,
      material_id: form.material_id,
      place_id: form.place_id,
      fuel_liters: form.fuel_liters,
      volume_m3: form.volume_m3,
      invoice_number: form.invoice_number || null,
    }
    if (editItem.value) {
      await api.put(`/trip-invoices/${editItem.value.id}`, payload)
    } else {
      await api.post('/trip-invoices', payload)
    }
    msg.success('Сохранено')
    showModal.value = false
    await loadInvoices()
  } catch (e: any) {
    msg.error(e.response?.data?.detail || 'Ошибка')
  }
  saving.value = false
}

async function confirmInvoice(id: number) {
  try { await api.post(`/trip-invoices/${id}/confirm`); msg.success('Подтверждено'); await loadInvoices() }
  catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
}

async function voidInvoice(id: number) {
  dialog.warning({
    title: 'Аннулировать?',
    content: 'Накладная будет аннулирована',
    positiveText: 'Да',
    negativeText: 'Нет',
    onPositiveClick: async () => {
      try { await api.post(`/trip-invoices/${id}/void`); msg.success('Аннулировано'); await loadInvoices() }
      catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
    },
  })
}

onMounted(async () => { await loadRefs(); await loadInvoices() })
</script>
