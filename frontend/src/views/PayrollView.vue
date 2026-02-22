<template>
  <div>
    <div class="page-header">
      <h2>Зарплата и Авансы</h2>
    </div>

    <n-tabs type="line" animated>
      <n-tab-pane name="payroll" tab="Ведомости">
        <!-- Generate -->
        <n-card size="small" style="margin-bottom: 16px">
          <n-space align="center">
            <span style="font-weight: 500">Период:</span>
            <n-input v-model:value="selectedMonth" placeholder="YYYY-MM" style="width: 140px" size="small" />
            <n-button type="primary" size="small" @click="generate" :loading="generating">Сформировать</n-button>
          </n-space>
        </n-card>

        <!-- Periods list -->
        <n-data-table :columns="periodColumns" :data="periods" bordered style="margin-bottom: 24px" />

        <!-- Lines for selected period -->
        <n-card v-if="selectedPeriod" :title="`Ведомость за ${selectedPeriod.month}`" size="small">
          <template #header-extra>
            <n-space>
              <n-button size="small" @click="exportExcel" type="info">📥 Скачать Excel</n-button>
              <n-button v-if="selectedPeriod.status === 'open'" size="small" type="warning" @click="closePeriod">Закрыть месяц</n-button>
              <n-button v-if="selectedPeriod.status === 'closed'" size="small" type="success" @click="markPaid">Отметить всё выплачено</n-button>
              <n-button size="small" type="error" @click="resetPeriod">🔄 Отменить и пересчитать</n-button>
            </n-space>
          </template>
          
          <n-data-table :columns="lineColumns" :data="lines" bordered size="small" />
          
          <div style="margin-top: 12px; text-align: right; font-weight: 600; font-size: 1.1rem">
            Итого к выплате: {{ totalPayable.toLocaleString() }} ₸
          </div>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="advances" tab="Авансы">
        <n-card size="small" title="Выдать аванс" style="margin-bottom: 16px">
          <n-form inline :model="advanceForm" label-placement="left">
            <n-form-item label="Сотрудник" style="width: 250px">
              <n-select v-model:value="advanceForm.employee_id" :options="employeeOptions" filterable placeholder="Выберите" />
            </n-form-item>
            <n-form-item label="Сумма" style="width: 150px">
              <n-input-number v-model:value="advanceForm.amount" :step="1000" placeholder="Сумма" />
            </n-form-item>
            <n-form-item label="Дата">
               <n-date-picker v-model:value="advanceForm.date" type="date" style="width: 140px" />
            </n-form-item>
            <n-form-item label="Комментарий">
              <n-input v-model:value="advanceForm.comment" placeholder="Опционально" />
            </n-form-item>
            <n-form-item>
              <n-button type="primary" @click="createAdvance" :loading="savingAdvance">Выдать</n-button>
            </n-form-item>
          </n-form>
        </n-card>

        <n-data-table :columns="advanceColumns" :data="advances" bordered :loading="loadingAdvances" />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed, reactive } from 'vue'
import { NDataTable, NButton, NCard, NSpace, NInput, NTag, useMessage, useDialog, NTabs, NTabPane, NForm, NFormItem, NSelect, NInputNumber, NDatePicker, NSwitch } from 'naive-ui'
import api from '../api/client'

const msg = useMessage()
const dialog = useDialog()
const periods = ref<any[]>([])
const lines = ref<any[]>([])
const selectedPeriod = ref<any>(null)
const selectedMonth = ref('')
const generating = ref(false)

// Advances
const advances = ref<any[]>([])
const loadingAdvances = ref(false)
const savingAdvance = ref(false)
const employeeOptions = ref<any[]>([])
const advanceForm = reactive({
  employee_id: null as number | null,
  amount: 0,
  date: Date.now(),
  comment: '',
})

const totalPayable = computed(() => lines.value.reduce((sum: number, l: any) => sum + (l.total_amount + l.manual_correction - l.advances_amount), 0))

function statusTag(status: string) {
  const map: Record<string, 'warning' | 'info' | 'success' | 'default'> = { open: 'warning', closed: 'info', paid: 'success' }
  const labels: Record<string, string> = { open: 'Открыт', closed: 'Закрыт', paid: 'Выплачено' }
  return h(NTag, { type: map[status] || 'default', size: 'small' }, () => labels[status] || status)
}

const periodColumns = [
  { title: 'Месяц', key: 'month', width: 100 },
  { title: 'Статус', key: 'status', width: 120, render: (r: any) => statusTag(r.status) },
  { title: 'Закрыт', key: 'closed_at', render: (r: any) => r.closed_at?.slice(0, 16) || '—' },
  {
    title: 'Действия', key: 'actions', width: 160,
    render: (row: any) => h(NButton, { size: 'small', type: 'primary', onClick: () => selectPeriod(row) }, () => 'Ведомость'),
  },
]

const lineColumns = [
  { title: 'Сотрудник', key: 'employee_name' },
  { title: 'Рейсов', key: 'trips_count', width: 80, render: (r: any) => r.trips_count || 0 },
  { title: 'Часов', key: 'hours_total', width: 80, render: (r: any) => Number(r.hours_total || 0).toFixed(1) },
  { title: 'Итого', key: 'total_amount', width: 130, render: (r: any) => h('strong', `${Number(r.total_amount).toLocaleString()} ₸`) },
  { title: 'Авансы', key: 'advances_amount', width: 100, render: (r: any) => h('span', { style: 'color: red' }, `-${Number(r.advances_amount).toLocaleString()}`) },
  { 
    title: 'К выплате', key: 'payable', width: 160, 
    render: (row: any) => {
        const payable = row.total_amount + row.manual_correction - row.advances_amount
        return h(NInputNumber, {
            value: payable,
            showButton: false,
            size: 'small',
            style: 'font-weight: bold; color: green',
            onUpdateValue: (v: number | null) => {
                const newPayable = v || 0
                row.manual_correction = newPayable - row.total_amount + row.advances_amount
            },
            onBlur: () => updateLine(row)
        })
    }
  },
  {
    title: 'Выплачено', key: 'is_paid', width: 100, align: 'center' as const,
    render: (row: any) => {
        return h(NSwitch, {
            value: row.is_paid,
            onUpdateValue: (v: boolean) => { row.is_paid = v; updateLine(row) }
        })
    }
  }
]

const advanceColumns = [
    { title: 'Дата', key: 'date', width: 120 },
    { title: 'Сотрудник', key: 'employee_name' },
    { title: 'Сумма', key: 'amount', render: (r: any) => `${r.amount.toLocaleString()} ₸` },
    { title: 'Комментарий', key: 'comment' },
    { 
        title: '', key: 'actions', width: 60,
        render: (row: any) => h(NButton, { type: 'error', size: 'tiny', onClick: () => deleteAdvance(row.id) }, () => '✗')
    }
]

async function loadPeriods() {
  try { periods.value = (await api.get('/payroll/periods')).data } catch {}
}

async function loadAdvances() {
    loadingAdvances.value = true
    try { advances.value = (await api.get('/salary-advances')).data } catch {}
    loadingAdvances.value = false
}

async function loadEmployees() {
    try { 
        const res = await api.get('/employees')
        employeeOptions.value = res.data.map((e: any) => ({ label: e.full_name, value: e.id }))
    } catch {}
}

async function selectPeriod(period: any) {
  selectedPeriod.value = period
  try { lines.value = (await api.get(`/payroll/periods/${period.id}/lines`)).data } catch {}
}

async function generate() {
  if (!selectedMonth.value) return msg.warning('Укажите месяц (YYYY-MM)')
  generating.value = true
  try {
    const res = await api.post(`/payroll/periods/generate?month=${selectedMonth.value}`)
    msg.success('Ведомость сформирована')
    await loadPeriods()
    await selectPeriod(res.data)
  } catch (e: any) {
    msg.error(e.response?.data?.detail || 'Ошибка')
  }
  generating.value = false
}

async function updateLine(row: any) {
    try {
        await api.put(`/payroll/lines/${row.id}`, {
            manual_correction: row.manual_correction,
            is_paid: row.is_paid
        })
        msg.success('Сохранено')
    } catch {
        msg.error('Ошибка сохранения')
    }
}

async function createAdvance() {
    if (!advanceForm.employee_id || !advanceForm.amount) return
    savingAdvance.value = true
    try {
        await api.post('/salary-advances', {
            employee_id: advanceForm.employee_id,
            amount: advanceForm.amount,
            date: new Date(advanceForm.date).toISOString().split('T')[0],
            comment: advanceForm.comment
        })
        msg.success('Аванс выдан')
        advanceForm.amount = 0; advanceForm.comment = ''
        await loadAdvances()
    } catch (e: any) { msg.error('Ошибка') }
    savingAdvance.value = false
}

async function deleteAdvance(id: number) {
    try { await api.delete(`/salary-advances/${id}`); await loadAdvances() } catch { msg.error('Ошибка') }
}

async function closePeriod() {
  dialog.warning({
    title: 'Закрыть месяц?',
    content: 'Все документы за период будут заблокированы. Это действие нельзя отменить.',
    positiveText: 'Закрыть',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try {
        await api.post(`/payroll/periods/${selectedPeriod.value.id}/close`)
        msg.success('Месяц закрыт')
        await loadPeriods()
        await selectPeriod({ ...selectedPeriod.value, status: 'closed' })
      } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
    },
  })
}

async function markPaid() {
  try {
    await api.post(`/payroll/periods/${selectedPeriod.value.id}/mark-paid`)
    msg.success('Отмечено как выплачено')
    await loadPeriods()
    selectedPeriod.value.status = 'paid'
    // Reload lines to update switches
    await selectPeriod(selectedPeriod.value)
  } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
}

async function resetPeriod() {
  if (!selectedPeriod.value) return
  const monthStr = selectedPeriod.value.month
  const periodId = selectedPeriod.value.id
  dialog.warning({
    title: 'Отменить и пересчитать?',
    content: `Ведомость за ${monthStr} будет удалена и пересформирована заново. Все ручные изменения будут потеряны. Точно хотите продолжить?`,
    positiveText: 'Да, пересчитать',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try {
        await api.delete(`/payroll/periods/${periodId}`)
        msg.success('Ведомость удалена')
        // Regenerate with saved month
        const res = await api.post(`/payroll/periods/generate?month=${monthStr}`)
        msg.success('Ведомость пересформирована')
        await loadPeriods()
        await selectPeriod(res.data)
      } catch (e: any) { msg.error(e.response?.data?.detail || 'Ошибка') }
    },
  })
}

async function exportExcel() {
  try {
    const res = await api.get(`/payroll/periods/${selectedPeriod.value.id}/export-excel`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `payroll_${selectedPeriod.value.month}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e: any) { msg.error('Ошибка экспорта') }
}

// Set default month to current
const now = new Date()
selectedMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

onMounted(async () => { await loadPeriods(); await loadAdvances(); await loadEmployees() })
</script>
