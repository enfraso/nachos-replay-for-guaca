<template>
    <div class="blank-layout">
        <slot></slot>
    </div>
</template>

<script setup>
</script>

<style scoped>
.blank-layout {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--color-primary-600) 0%, var(--color-primary-800) 100%);
}
</style>
