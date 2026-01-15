<script setup lang="ts">
import { RouterView } from 'vue-router'

import BackendReaction from '@/components/BackendReaction/Index.vue'
import ConfigProvider from '@/components/ConfigProvider/index.vue'
import GlobalRegister from '@/components/GlobalRegister/Index.vue'
import Loading from '@/components/Loading.vue'
import { useAppConfigStore } from '@/stores/useAppConfig'

const appStore = useAppConfigStore()

</script>

<template>
  <ConfigProvider>
    <BackendReaction />
    <RouterView />
    <Loading />
    <GlobalRegister />
  </ConfigProvider>
</template>


