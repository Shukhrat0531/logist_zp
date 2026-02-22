<template>
  <div>
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: 12px">
        <n-button @click="$router.push('/')">← Назад</n-button>
        <h2>{{ objectName }}</h2>
      </div>
      <n-space>
        <n-button type="primary" color="#f0a020" @click="openCloseVolume" v-if="pendingStats.trips_count > 0">
            Закрыть объем ({{ pendingStats.trips_count }})
        </n-button>
        <n-date-picker v-model:value="dateRange" type="daterange" clearable size="small" @update:value="loadData" />
      </n-space>
    </div>

    <n-tabs type="line" animated>
      <n-tab-pane name="overview" tab="Обзор">
        <!-- Stats Cards -->
        <n-grid :cols="3" :x-gap="12" style="margin-bottom: 24px">
            <n-gi>
                <n-card size="small">
                    <div style="color: #888; font-size: 12px">Всего рейсов</div>
                    <div style="font-size: 24px; font-weight: bold">{{ trips.length }}</div>
                </n-card>
            </n-gi>
            <n-gi>
                <n-card size="small">
                    <div style="color: #888; font-size: 12px">Доставлено объема</div>
                    <div style="font-size: 24px; font-weight: bold">{{ totalVolume.toFixed(2) }} м³</div>
                </n-card>
            </n-gi>
            <n-gi>
                <n-card size="small" style="border-left: 3px solid #f0a020">
                    <div style="color: #666; font-size: 12px">Не закрыто</div>
                    <div style="font-size: 18px; font-weight: bold">{{ pendingStats.trips_count }} рейсов</div>
                    <div style="font-size: 14px">{{ pendingStats.total_volume.toFixed(2) }} м³</div>
                </n-card>
            </n-gi>
        </n-grid>

        <!-- Trips Table -->
        <h3>Рейсы на объект</h3>
        <n-data-table :columns="tripColumns" :data="trips" :loading="loading" size="small" bordered />
      </n-tab-pane>

      <n-tab-pane name="acts" tab="Акты сверки">
          <n-data-table :columns="actColumns" :data="acts" :loading="loadingActs" bordered />
      </n-tab-pane>
    </n-tabs>

    <!-- Close Volume Modal -->
    <n-modal v-model:show="showCloseModal" preset="dialog" title="Закрытие объема (Создание акта)" style="width: 500px">
        <n-form label-placement="left" label-width="120">
            <n-form-item label="Период">
                <n-date-picker v-model:value="closeDateRange" type="daterange" style="width: 100%" />
            </n-form-item>
            <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; font-size: 0.9rem">
                Будет сформирован акт для <b>{{ objectName }}</b> за выбранный период.
                В акт войдут все подтвержденные рейсы, которые еще не закрыты.
            </div>
        </n-form>
        <template #action>
            <n-button @click="showCloseModal = false">Отмена</n-button>
            <n-button type="primary" @click="createAct" :loading="saving">Сформировать</n-button>
        </template>
    </n-modal>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NDatePicker, NGrid, NGi, NCard, NDataTable, NSpace, NTabs, NTabPane, NModal, NForm, NFormItem, useMessage } from 'naive-ui'
import api from '../api/client'

const route = useRoute()
const msg = useMessage()
const objectName = ref('Объект')
const dateRange = ref<[number, number] | null>(null)
const loading = ref(false)
const loadingActs = ref(false)
const saving = ref(false)

const trips = ref<any[]>([])
const acts = ref<any[]>([])
const pendingStats = ref({ trips_count: 0, total_volume: 0, total_amount: 0 })

const showCloseModal = ref(false)
const closeDateRange = ref<[number, number] | null>(null)

const totalVolume = computed(() => trips.value.reduce((s, t) => s + (t.volume_m3 || 0), 0))

const tripColumns = [
    { title: 'Дата', key: 'trip_date', width: 100 },
    { title: 'Машина', key: 'vehicle_plate', width: 120 },
    { title: 'Водитель', key: 'driver_name' },
    { title: 'Материал', key: 'material_name' },
    { title: 'Место', key: 'place_name' },
    { title: 'Объем (м³)', key: 'volume_m3', width: 100, render: (r: any) => r.volume_m3 ? Number(r.volume_m3).toFixed(2) : '—' },
]

const actColumns = [
  { title: 'ID', key: 'id', width: 50 },
  { title: 'Дата', key: 'created_at', width: 150, render: (r: any) => new Date(r.created_at).toLocaleString() },
  { title: 'Период', key: 'period', render: (r: any) => `${r.start_date} — ${r.end_date}` },
  { title: 'Рейсов', key: 'total_trips', width: 80 },
  { title: 'Объем', key: 'total_volume', width: 100, render: (r: any) => Number(r.total_volume).toFixed(1) },
  { title: 'Действия', key: 'actions', width: 100, render: (row: any) => h(NButton, { size: 'tiny', type: 'error', onClick: () => deleteAct(row.id) }, () => 'Удалить') },
]

async function loadData() {
    loading.value = true
    const params: any = {}
    if (dateRange.value) {
        params.date_from = new Date(dateRange.value[0]).toISOString().split('T')[0]
        params.date_to = new Date(dateRange.value[1]).toISOString().split('T')[0]
    }

    try {
        const id = route.params.id

        // Pending stats
        const pRes = await api.get(`/dashboard/objects/${id}/pending-stats`)
        pendingStats.value = pRes.data

        // Trips for this buyer
        const tParams: any = { buyer_id: id, page: 1, size: 200 }
        if (dateRange.value) {
            tParams.trip_date_from = new Date(dateRange.value[0]).toISOString().split('T')[0]
            tParams.trip_date_to = new Date(dateRange.value[1]).toISOString().split('T')[0]
        }
        const tRes = await api.get('/trip-invoices', { params: tParams })
        trips.value = tRes.data.items

        // Name
        if (trips.value.length > 0) objectName.value = trips.value[0].buyer_name
        else {
             const bRes = await api.get('/buyers')
             const found = bRes.data.find((b: any) => b.id == id)
             if (found) objectName.value = found.name
        }

        // Acts
        loadActs()

    } catch {}
    loading.value = false
}

async function loadActs() {
    loadingActs.value = true
    try {
        const res = await api.get('/delivery-acts', { params: { buyer_id: route.params.id } })
        acts.value = res.data.items
    } catch {}
    loadingActs.value = false
}

function openCloseVolume() {
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), 1)
    closeDateRange.value = [start.getTime(), now.getTime()]
    showCloseModal.value = true
}

async function createAct() {
    if (!closeDateRange.value) return
    saving.value = true
    try {
        await api.post('/delivery-acts', {
            buyer_id: Number(route.params.id),
            start_date: new Date(closeDateRange.value[0]).toISOString().split('T')[0],
            end_date: new Date(closeDateRange.value[1]).toISOString().split('T')[0]
        })
        msg.success('Объем закрыт (Акт создан)')
        showCloseModal.value = false
        await loadData()
    } catch (e: any) {
        msg.error(e.response?.data?.detail || 'Ошибка создания акта')
    }
    saving.value = false
}

async function deleteAct(id: number) {
    if (!confirm('Удалить акт? Рейсы снова станут незакрытыми.')) return
    try {
        await api.delete(`/delivery-acts/${id}`)
        msg.success('Акт удален')
        await loadData()
    } catch { msg.error('Ошибка') }
}

onMounted(() => {
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
    dateRange.value = [firstDay.getTime(), now.getTime()]
    loadData()
})
</script>
