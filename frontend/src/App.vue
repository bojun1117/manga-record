<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// 補回 username(重新整理頁面後 token 還在但 username 只存在記憶體裡),順便驗證 token 是否還有效。
onMounted(() => {
  void auth.restoreSession()
})
</script>

<template>
  <RouterView />
</template>
