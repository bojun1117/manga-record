<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isServerResting } from '@/constants/serverSchedule'
import ServerRestingNotice from '@/components/ServerRestingNotice.vue'

const auth = useAuthStore()

// 伺服器排程關機時直接顯示提示，不呼叫 API（否則要等 CloudFront 逾時約 30 秒才會失敗）
const resting = ref(isServerResting())
let timer: number | null = null

watch(
  resting,
  (isResting) => {
    if (!isResting) void auth.restoreSession()
  },
  { immediate: true },
)

onMounted(() => {
  timer = window.setInterval(() => {
    resting.value = isServerResting()
  }, 60_000)
})

onUnmounted(() => {
  if (timer !== null) window.clearInterval(timer)
})
</script>

<template>
  <ServerRestingNotice v-if="resting" />
  <RouterView v-else />
</template>
