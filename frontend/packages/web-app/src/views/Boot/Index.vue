<script setup lang="ts">
import { theme } from 'ant-design-vue'
import { ref } from 'vue'

import { base64ToString } from '@/utils/common'
import { storage } from '@/utils/storage'

import LaunchCarousel from '@/components/Boot/LaunchCarousel.vue'
import ConfigProvider from '@/components/ConfigProvider/index.vue'
import Loading from '@/components/Loading.vue'
import { utilsManager } from '@/platform'

const { token } = theme.useToken()
const progress = ref(0)

async function waitForSchedulerReady() {
  const start = Date.now()
  const timeoutMs = 60_000
  const intervalMs = 500

  while (Date.now() - start < timeoutMs) {
    try {
      const resp = await fetch('http://127.0.0.1:13159/health', { cache: 'no-store' })
      if (resp.ok) {
        const data = await resp.json()
        if (data?.route_port) {
          storage.set('route_port', data.route_port)
          sessionStorage.setItem('launch', '1')
          location.replace(`/index.html`)
          return
        }
      }
    } catch {
      // ignore until timeout
    }
    await new Promise(resolve => setTimeout(resolve, intervalMs))
  }
}

utilsManager.listenEvent('scheduler-event', (eventMsg) => {
  const msgString = base64ToString(eventMsg)
  const msgObject = JSON.parse(msgString)
  const { type, msg } = msgObject

  switch (type) {
    case 'sync': {
      progress.value = msg.step
      break
    }
    case 'sync_cancel': {
      // 兼容旧链路：仍接收事件，但由 /health 探活确认 ready
      waitForSchedulerReady()
      break
    }
    default:
      break
  }
})

window.onload = () => {
  utilsManager.invoke('main_window_onload').catch(() => {})
  waitForSchedulerReady()
}
</script>

<template>
  <ConfigProvider>
    <div class="flex h-full w-full items-center justify-center">
      <LaunchCarousel>
        <template #footer>
          <div class="mt-6 w-[280px]">
            <a-progress
              :percent="progress"
              :show-info="false"
              :stroke-color="token.colorPrimary"
              trail-color="rgba(255, 255, 255, 0.12)"
            />
          </div>
        </template>
      </LaunchCarousel>
    </div>
    <Loading />
  </ConfigProvider>
</template>
