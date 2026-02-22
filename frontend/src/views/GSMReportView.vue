<template>
  <div>
    <div class="page-header">
      <h2>Отчет по ГСМ</h2>
    </div>

    <!-- Filters -->
    <n-card size="small" style="margin-bottom: 16px">
      <n-space>
        <n-date-picker v-model:value="dateRange" type="daterange" clearable size="small" />
        <n-button size="small" @click="loadReport" type="primary" :loading="loading">Сформировать</n-button>
      </n-space>
    </n-card>

    <n-data-table :columns="columns" :data="data" :loading="loading" bordered :summary="summary" :row-props="rowProps" />

    <!-- Vehicle Fuel History Modal -->
    <n-modal v-model:show="showHistory" preset="dialog" :title="`Заправки — ${selectedVehicle?.vehicle_plate || ''}`" style="width: 700px">
      <n-data-table :columns="historyColumns" :data="history" :loading="loadingHistory" bordered size="small" :summary="historySummary" />
      <template #action>
        <n-button @click="showHistory = false">Закрыть</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NDataTable, NButton, NCard, NSpace, NDatePicker, NModal, useMessage } from 'naive-ui'
import api from '../api/client'

const msg = useMessage()
const data = ref<any[]>([])
const loading = ref(false)
const dateRange = ref<[number, number] | null>(null)
const fuelPrice = ref(0)

// History
const showHistory = ref(false)
const selectedVehicle = ref<any>(null)
const history = ref<any[]>([])
const loadingHistory = ref(false)

const columns = [
  { title: 'Машина', key: 'vehicle_plate' },
  { title: 'Литров', key: 'total_fuel', render: (r: any) => Number(r.total_fuel).toLocaleString() },
  { title: 'Стоимость (₸)', key: 'estimated_cost', render: (r: any) => `${(Number(r.total_fuel) * fuelPrice.value).toLocaleString()} ₸` },
]

const historyColumns = [
  { title: 'Дата', key: 'trip_date', width: 120 },
  { title: 'Литров', key: 'fuel_liters', width: 100, render: (r: any) => Number(r.fuel_liters).toLocaleString() },
  { title: 'Стоимость', key: 'cost', width: 120, render: (r: any) => `${(Number(r.fuel_liters) * fuelPrice.value).toLocaleString()} ₸` },
  { title: 'Водитель', key: 'driver_name' },
  { title: 'Объект', key: 'buyer_name' },
]

const summary = (pageData: any[]) => {
    const totalFuel = pageData.reduce((sum: number, r: any) => sum + Number(r.total_fuel), 0)
    const totalCost = totalFuel * fuelPrice.value
    return {
        vehicle_plate: { value: h('strong', 'Итого') },
        total_fuel: { value: h('strong', Number(totalFuel).toLocaleString()) },
        estimated_cost: { value: h('strong', `${totalCost.toLocaleString()} ₸`) },
    }
}

const historySummary = (pageData: any[]) => {
    const totalFuel = pageData.reduce((sum: number, r: any) => sum + Number(r.fuel_liters), 0)
    const totalCost = totalFuel * fuelPrice.value
    return {
        trip_date: { value: h('strong', 'Итого') },
        fuel_liters: { value: h('strong', Number(totalFuel).toLocaleString()) },
        cost: { value: h('strong', `${totalCost.toLocaleString()} ₸`) },
    }
}

const rowProps = (row: any) => ({
    style: 'cursor: pointer',
    onClick: () => openHistory(row),
})

async function loadFuelPrice() {
    try {
        const res = await api.get('/settings')
        const setting = res.data.find((s: any) => s.key === 'fuel_price_per_liter')
        fuelPrice.value = setting ? Number(setting.value) : 0
    } catch {}
}

async function loadReport() {
  loading.value = true
  try {
    const params: any = {}
    if (dateRange.value) {
      params.date_from = new Date(dateRange.value[0]).toISOString().split('T')[0]
      params.date_to = new Date(dateRange.value[1]).toISOString().split('T')[0]
    }
    const res = await api.get('/dashboard/gsm-report', { params })
    data.value = res.data
  } catch (e: any) {
    msg.error('Ошибка загрузки')
  }
  loading.value = false
}

async function openHistory(row: any) {
    selectedVehicle.value = row
    showHistory.value = true
    loadingHistory.value = true
    try {
        const params: any = { vehicle_id: row.vehicle_id }
        if (dateRange.value) {
            params.date_from = new Date(dateRange.value[0]).toISOString().split('T')[0]
            params.date_to = new Date(dateRange.value[1]).toISOString().split('T')[0]
        }
        const res = await api.get('/dashboard/gsm-vehicle-history', { params })
        history.value = res.data
    } catch { history.value = [] }
    loadingHistory.value = false
}

onMounted(async () => {
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), 1)
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    dateRange.value = [start.getTime(), end.getTime()]
    await loadFuelPrice()
    await loadReport()
})
</script>
