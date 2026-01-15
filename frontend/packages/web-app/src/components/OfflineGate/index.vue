<script setup lang="ts">
import { Tooltip } from 'ant-design-vue'

defineProps<{ disabled: boolean, reason: string }>()
</script>

<template>
  <Tooltip :title="disabled ? reason : ''">
    <span class="inline-flex" :style="{ cursor: disabled ? 'not-allowed' : 'pointer' }">
      <span :style="{ opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? 'none' : 'auto' }">
        <slot />
      </span>
    </span>
  </Tooltip>
</template>
