<template>
  <div id="app">
    <AppShell v-if="$route.meta.requiresAuth" />
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import AppShell from './layouts/AppShell.vue'
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
