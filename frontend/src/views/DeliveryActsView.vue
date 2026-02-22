<template>
  <div>
    <div class="page-header">
      <h2>Акты сверки (Закрытие объемов)</h2>
      <n-button type="primary" @click="openCreate">+ Сформировать акт</n-button>
    </div>

    <!-- Filters -->
    <n-card size="small" style="margin-bottom: 16px">
      <n-space>
        <n-date-picker v-model:value="filters.dateRange" type="daterange" clearable size="small" />
        <n-select v-model:value="filters.buyer_id" :options="buyerOptions" placeholder="Закупщик" clearable size="small" style="width: 200px" />
        <n-button size="small" @click="loadActs">Применить</n-button>
      </n-space>
    </n-card>

    <n-data-table :columns="columns" :data="acts" :loading="loading" bordered />

    <!-- Create Modal -->
    <n-modal v-model:show="showModal" preset="dialog" title="Сформировать акт" style="width: 500px">
      <n-form :model="form" label-placement="left" label-width="120">
        <n-form-item label="Закупщик">
          <n-select v-model:value="form.buyer_id" :options="buyerOptions" filterable />
        </n-form-item>
        <n-form-item label="Период">
          <n-date-picker v-model:value="form.dateRange" type="daterange" style="width: 100%" />
        </n-form-item>
        <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; font-size: 0.9rem">
            При формировании акта будут найдены все <b>подтверждённые</b> рейсы за этот период по выбранному закупщику, у которых ещё нет акта.
        </div>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">Отмена</n-button>
        <n-button type="primary" @click="createAct" :loading="saving">Сформировать</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NDataTable, NButton, NModal, NForm, NFormItem, NSelect, NDatePicker, NCard, NSpace, useMessage } from 'naive-ui'
import api from '../api/client'

const msg = useMessage()
const acts = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const buyerOptions = ref<any[]>([])

const filters = reactive({ dateRange: null as any, buyer_id: null as number | null })
const form = reactive({ buyer_id: null as number | null, dateRange: null as any })

const columns = [
  { title: 'ID', key: 'id', width: 50 },
  { title: 'Дата акта', key: 'act_date', width: 100 },
  { title: 'Закупщик', key: 'buyer_name' },
  { title: 'Период', key: 'period', render: (r: any) => `${r.date_from} — ${r.date_to}` },
  { title: 'Рейсов', key: 'total_trips', width: 80 },
  { title: 'Объем (м3)', key: 'total_volume', width: 100, render: (r: any) => r.total_volume ? Number(r.total_volume).toFixed(1) : '-' },
  { title: 'Сумма', key: 'total_amount', width: 120, render: (r: any) => `${Number(r.total_amount).toLocaleString()} ₸` },
  {
    title: 'Действия', key: 'actions', width: 100,
    render: (row: any) => h(NButton, { size: 'tiny', type: 'error', onClick: () => deleteAct(row.id) }, () => 'Удалить')
  },
]

async function loadRefs() {
  try {
    const res = await api.get('/buyers')
    buyerOptions.value = res.data.map((b: any) => ({ label: b.name, value: b.id }))
  } catch {}
}

async function loadActs() {
  loading.value = true
  try {
    const params: any = {}
    if (filters.buyer_id) params.buyer_id = filters.buyer_id
    // Add date filter to API if supported, currently just list
    const res = await api.get('/delivery-acts', { params })
    acts.value = res.data
  } catch {}
  loading.value = false
}

function openCreate() {
  form.buyer_id = null; form.dateRange = null
  showModal.value = true
}

async function createAct() {
    if (!form.buyer_id || !form.dateRange) return
    saving.value = true
    try {
        await api.post('/delivery-acts', {
            buyer_id: form.buyer_id,
            start_date: new Date(form.dateRange[0]).toISOString().split('T')[0],
            end_date: new Date(form.dateRange[1]).toISOString().split('T')[0]
        })
        msg.success('Акт сформирован')
        showModal.value = false
        await loadActs()
    } catch (e: any) {
        msg.error(e.response?.data?.detail || 'Ошибка')
    }
    saving.value = false
}

async function deleteAct(id: number) {
    if (!confirm('Удалить акт? Рейсы будут отвязаны.')) return
    try {
        await api.delete(`/delivery-acts/${id}`)
        msg.success('Удалено')
        await loadActs()
    } catch { msg.error('Ошибка') }
}

onMounted(async () => { await loadRefs(); await loadActs() })
</script>
