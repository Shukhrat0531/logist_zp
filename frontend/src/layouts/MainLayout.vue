<template>
  <n-layout has-sider style="height: 100vh">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      :native-scrollbar="false"
      style="background: #fff"
    >
      <div style="padding: 16px; text-align: center; font-weight: 700; font-size: 1.1rem; color: #667eea; border-bottom: 1px solid #eee">
        {{ collapsed ? 'LZ' : 'Logist ZP' }}
      </div>
      <n-menu :collapsed="collapsed" :options="menuOptions" :value="currentKey" @update:value="handleNav" />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered style="height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; background: #fff">
        <span style="font-weight: 600; font-size: 1rem">{{ auth.user?.full_name || auth.user?.username }}</span>
        <n-space>
          <n-tag :type="roleColor" size="small">{{ auth.user?.role }}</n-tag>
          <n-button size="small" @click="handleLogout">Выйти</n-button>
        </n-space>
      </n-layout-header>
      <n-layout-content style="padding: 24px; background: #f5f7fa; min-height: calc(100vh - 56px)">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NButton, NSpace, NTag, NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  HomeOutline, CarOutline, ConstructOutline, PeopleOutline,
  DocumentTextOutline, TimerOutline, WalletOutline, SettingsOutline,
  BusinessOutline, CubeOutline, MapOutline, PersonOutline
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const collapsed = ref(false)

const currentKey = computed(() => route.name as string)
const roleColor = computed(() => {
  if (auth.user?.role === 'admin') return 'error'
  if (auth.user?.role === 'dispatcher') return 'info'
  return 'success'
})

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = computed<MenuOption[]>(() => {
  const items: MenuOption[] = [
    { label: 'Панель', key: 'Dashboard', icon: renderIcon(HomeOutline) },
    { label: 'ГСМ', key: 'GSMReport', icon: renderIcon(CarOutline) },
    { type: 'divider', key: 'd1' },
    { label: 'Накладные', key: 'TripInvoices', icon: renderIcon(DocumentTextOutline) },
    { label: 'Спецтехника', key: 'MachinerySessions', icon: renderIcon(TimerOutline) },
    { label: 'Зарплата', key: 'Payroll', icon: renderIcon(WalletOutline) },
    { type: 'divider', key: 'd2' },
    { label: 'Карьеры', key: 'Carriers', icon: renderIcon(MapOutline) },
    { label: 'Закупщики', key: 'Buyers', icon: renderIcon(BusinessOutline) },
    { label: 'Материалы', key: 'Materials', icon: renderIcon(CubeOutline) },
    { label: 'Машины', key: 'Vehicles', icon: renderIcon(CarOutline) },
    { label: 'Спецтехника (Спр)', key: 'Machinery', icon: renderIcon(ConstructOutline) },
    { label: 'Сотрудники', key: 'Employees', icon: renderIcon(PeopleOutline) },
  ]
  if (auth.isAdmin) {
    items.push(
      { type: 'divider', key: 'd3' },
      { label: 'Пользователи', key: 'Users', icon: renderIcon(PersonOutline) },
      { label: 'Настройки', key: 'Settings', icon: renderIcon(SettingsOutline) },
    )
  }
  return items
})

function handleNav(key: string) {
  router.push({ name: key })
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
