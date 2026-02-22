<template>
  <div>
    <div class="page-header">
      <h2>Панель управления</h2>
    </div>
    <n-grid :cols="4" :x-gap="16" :y-gap="16">
      <n-gi>
        <div class="stat-card">
          <h3>Рейсы сегодня</h3>
          <div class="value">{{ stats.today_trips }}</div>
          <div class="sub">{{ formatMoney(stats.today_trips_amount) }} ₸</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="stat-card green">
          <h3>Рейсы за месяц</h3>
          <div class="value">{{ stats.month_trips }}</div>
          <div class="sub">{{ formatMoney(stats.month_trips_amount) }} ₸</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="stat-card orange">
          <h3>Открытые смены</h3>
          <div class="value">{{ stats.open_sessions }}</div>
          <div class="sub">спецтехника</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="stat-card blue">
          <h3>Смены за месяц</h3>
          <div class="value">{{ stats.month_sessions }}</div>
          <div class="sub">спецтехника</div>
        </div>
      </n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16" style="margin-top: 24px">
      <n-gi>
        <n-card title="Накладные" size="small">
          <template #header-extra>
            <n-button size="small" type="primary" @click="$router.push('/trip-invoices')">Открыть →</n-button>
          </template>
          <p style="color: #888">Управление рейсами самосвалов. Создание, подтверждение и просмотр накладных.</p>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="Спецтехника" size="small">
          <template #header-extra>
            <n-button size="small" type="primary" @click="$router.push('/machinery-sessions')">Открыть →</n-button>
          </template>
          <p style="color: #888">Учёт рабочих смен спецтехники. Открытие и закрытие смен.</p>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card title="Активные объекты (этот месяц)" size="small" style="margin-top: 24px">
        <n-grid :cols="4" :x-gap="12" :y-gap="12">
            <n-gi v-for="obj in objectStats" :key="obj.buyer_id">
                <n-card hoverable @click="$router.push(`/objects/${obj.buyer_id}`)" style="cursor: pointer; border-left: 3px solid #2080f0">
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px">{{ obj.buyer_name }}</div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666">
                        <span>Рейсов: {{ obj.trips_count }}</span>
                        <span>Объем: {{ obj.total_volume }} м³</span>
                    </div>
                </n-card>
            </n-gi>
        </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NGrid, NGi, NCard, NButton } from 'naive-ui'
import api from '../api/client'

const stats = ref({
  today_trips: 0, month_trips: 0, open_sessions: 0, month_sessions: 0,
  today_trips_amount: 0, month_trips_amount: 0,
})

function formatMoney(v: number) {
  return new Intl.NumberFormat('ru-RU').format(v)
}

const objectStats = ref<any[]>([])

onMounted(async () => {
  try {
    const [statsRes, objRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/objects-stats')
    ])
    stats.value = statsRes.data
    objectStats.value = objRes.data
  } catch {}
})
</script>
