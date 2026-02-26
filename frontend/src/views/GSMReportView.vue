<template>
  <div>
    <div class="page-header">
      <h2>Отчет по ГСМ</h2>
    </div>

    <!-- Filters -->
    <n-card size="small" style="margin-bottom: 16px">
      <n-space>
        <n-date-picker v-model:value="dateRange" type="daterange" clearable size="small" />
        <n-button size="small" @click="loadAll" type="primary" :loading="loading">Сформировать</n-button>
      </n-space>
    </n-card>

    <!-- Vehicles -->
    <h3 style="margin-bottom: 8px">🚛 Транспорт</h3>
    <n-data-table :columns="vehicleColumns" :data="vehicleData" :loading="loading" bordered :summary="vehicleSummary" :row-props="vehicleRowProps" style="margin-bottom: 24px" />

    <!-- Machinery -->
    <h3 style="margin-bottom: 8px">🏗️ Спецтехника</h3>
    <n-data-table :columns="machineryColumns" :data="machineryData" :loading="loading" bordered :summary="machinerySummary" :row-props="machineryRowProps" />

    <!-- Total -->
    <n-card size="small" style="margin-top: 16px">
      <n-space justify="end">
        <strong>Общий расход: {{ totalAllFuel.toLocaleString() }} л — {{ (totalAllFuel * fuelPrice).toLocaleString() }} ₸</strong>
      </n-space>
    </n-card>

    <!-- History Modal -->
    <n-modal v-model:show="showHistory" preset="dialog" :title="`Заправки — ${historyTitle}`" style="width: 700px">
      <n-data-table :columns="historyColumns" :data="history" :loading="loadingHistory" bordered size="small" :summary="historySummary" />
      <template #action>
        <n-button @click="showHistory = false">Закрыть</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NDataTable, NButton, NCard, NSpace, NDatePicker, NModal, useMessage } from 'naive-ui'
import api from '../api/client'

const msg = useMessage()
const loading = ref(false)
const fuelPrice = ref(0)

// Data
const vehicleData = ref<any[]>([])
const machineryData = ref<any[]>([])
const dateRange = ref<[number, number] | null>(null)

// History
const showHistory = ref(false)
const historyTitle = ref('')
const history = ref<any[]>([])
const loadingHistory = ref(false)

const totalAllFuel = computed(() => {
    const vFuel = vehicleData.value.reduce((s, r) => s + Number(r.total_fuel), 0)
    const mFuel = machineryData.value.reduce((s, r) => s + Number(r.total_fuel), 0)
    return vFuel + mFuel
})

// Vehicle columns
const vehicleColumns = [
  { title: 'Машина', key: 'vehicle_plate' },
  { title: 'Литров', key: 'total_fuel', render: (r: any) => Number(r.total_fuel).toLocaleString() },
  { title: 'Стоимость (₸)', key: 'cost', render: (r: any) => `${(Number(r.total_fuel) * fuelPrice.value).toLocaleString()} ₸` },
]

const machineryColumns = [
  { title: 'Спецтехника', key: 'machinery_name' },
  { title: 'Оператор', key: 'operator_name' },
  { title: 'Литров', key: 'total_fuel', render: (r: any) => Number(r.total_fuel).toLocaleString() },
  { title: 'Стоимость (₸)', key: 'cost', render: (r: any) => `${(Number(r.total_fuel) * fuelPrice.value).toLocaleString()} ₸` },
]

const historyColumns = [
  { title: 'Дата', key: 'trip_date', width: 120 },
  { title: 'Литров', key: 'fuel_liters', width: 100, render: (r: any) => Number(r.fuel_liters).toLocaleString() },
  { title: 'Стоимость', key: 'cost', width: 120, render: (r: any) => `${(Number(r.fuel_liters) * fuelPrice.value).toLocaleString()} ₸` },
  { title: 'Сотрудник', key: 'driver_name' },
  { title: 'Объект', key: 'buyer_name' },
]

function makeSummary(data: any[]) {
    const totalFuel = data.reduce((s: number, r: any) => s + Number(r.total_fuel), 0)
    return {
        vehicle_plate: { value: h('strong', 'Итого') },
        machinery_name: { value: h('strong', 'Итого') },
        total_fuel: { value: h('strong', Number(totalFuel).toLocaleString()) },
        cost: { value: h('strong', `${(totalFuel * fuelPrice.value).toLocaleString()} ₸`) },
    }
}

const vehicleSummary = (d: any[]) => makeSummary(d)
const machinerySummary = (d: any[]) => makeSummary(d)

const historySummary = (pageData: any[]) => {
    const totalFuel = pageData.reduce((s: number, r: any) => s + Number(r.fuel_liters), 0)
    return {
        trip_date: { value: h('strong', 'Итого') },
        fuel_liters: { value: h('strong', Number(totalFuel).toLocaleString()) },
        cost: { value: h('strong', `${(totalFuel * fuelPrice.value).toLocaleString()} ₸`) },
    }
}

const vehicleRowProps = (row: any) => ({ style: 'cursor: pointer', onClick: () => openVehicleHistory(row) })
const machineryRowProps = (row: any) => ({ style: 'cursor: pointer', onClick: () => openMachineryHistory(row) })

function getDateParams() {
    const params: any = {}
    if (dateRange.value) {
        params.date_from = new Date(dateRange.value[0]).toISOString().split('T')[0]
        params.date_to = new Date(dateRange.value[1]).toISOString().split('T')[0]
    }
    return params
}

async function loadFuelPrice() {
    try {
        const res = await api.get('/settings')
        const s = res.data.find((s: any) => s.key === 'fuel_price_per_liter')
        fuelPrice.value = s ? Number(s.value) : 0
    } catch {}
}

async function loadAll() {
    loading.value = true
    try {
        const params = getDateParams()
        const [vRes, mRes] = await Promise.all([
            api.get('/dashboard/gsm-report', { params }),
            api.get('/dashboard/gsm-machinery-report', { params }),
        ])
        vehicleData.value = vRes.data
        machineryData.value = mRes.data
    } catch { msg.error('Ошибка загрузки') }
    loading.value = false
}

async function openVehicleHistory(row: any) {
    historyTitle.value = row.vehicle_plate
    showHistory.value = true
    loadingHistory.value = true
    try {
        const params = { vehicle_id: row.vehicle_id, ...getDateParams() }
        history.value = (await api.get('/dashboard/gsm-vehicle-history', { params })).data
    } catch { history.value = [] }
    loadingHistory.value = false
}

async function openMachineryHistory(row: any) {
    historyTitle.value = row.machinery_name
    showHistory.value = true
    loadingHistory.value = true
    try {
        const params = { machinery_id: row.machinery_id, ...getDateParams() }
        history.value = (await api.get('/dashboard/gsm-machinery-history', { params })).data
    } catch { history.value = [] }
    loadingHistory.value = false
}

onMounted(async () => {
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), 1)
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    dateRange.value = [start.getTime(), end.getTime()]
    await loadFuelPrice()
    await loadAll()
})
</script>
