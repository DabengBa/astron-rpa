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
      storage.set('route_port', msg?.route_port)
      sessionStorage.setItem('launch', '1')
      location.replace(`/index.html`)
      break
    }
    default:
      break
  }
})

window.onload = () => {
  utilsManager.invoke('main_window_onload').catch(() => {})
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
