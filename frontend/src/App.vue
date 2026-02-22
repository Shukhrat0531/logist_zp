<template>
  <n-config-provider :locale="ruRU" :date-locale="dateRuRU">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NDialogProvider, ruRU, dateRuRU } from 'naive-ui'
</script>
