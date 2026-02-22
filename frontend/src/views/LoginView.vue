<template>
  <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
    <n-card style="width: 400px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3)">
      <div style="text-align: center; margin-bottom: 24px">
        <h1 style="font-size: 1.8rem; font-weight: 700; color: #667eea; margin-bottom: 4px">Logist ZP</h1>
        <p style="color: #888; font-size: 0.9rem">Управление перевозками и зарплатой</p>
      </div>
      <n-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <n-form-item label="Логин" path="username">
          <n-input v-model:value="form.username" placeholder="Введите логин" size="large" />
        </n-form-item>
        <n-form-item label="Пароль" path="password">
          <n-input v-model:value="form.password" type="password" placeholder="Введите пароль" size="large" show-password-on="click" />
        </n-form-item>
        <n-button type="primary" block size="large" :loading="loading" @click="handleLogin" style="margin-top: 8px; background: linear-gradient(135deg, #667eea, #764ba2); border: none">
          Войти
        </n-button>
      </n-form>
      <n-alert v-if="error" type="error" style="margin-top: 16px">{{ error }}</n-alert>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { NCard, NForm, NFormItem, NInput, NButton, NAlert } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', password: '' })
const rules = {
  username: { required: true, message: 'Введите логин', trigger: 'blur' },
  password: { required: true, message: 'Введите пароль', trigger: 'blur' },
}

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.username, form.password)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>
