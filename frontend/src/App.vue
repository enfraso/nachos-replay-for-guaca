<template>
    <component :is="layout">
        <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
                <component :is="Component" />
            </transition>
        </router-view>
    </component>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DefaultLayout from '@/components/layouts/DefaultLayout.vue'
import BlankLayout from '@/components/layouts/BlankLayout.vue'

const route = useRoute()
const authStore = useAuthStore()

const layout = computed(() => {
    const layoutName = route.meta.layout || 'default'
    return layoutName === 'blank' ? BlankLayout : DefaultLayout
})

onMounted(async () => {
    await authStore.init()
})
</script>

<style>
#app {
    min-height: 100vh;
}
</style>
